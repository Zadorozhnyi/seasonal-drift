"""Experiment driver: control series, injected changes, all detectors in the
default and the calibrated setting, metrics (false alarms per 1000 points,
detection rate, delay)."""
from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .data import load_hourly, select_clients, source_series
from .detectors import BATCH, STREAM, VARIANTS, batch_default_threshold, run_batch, run_stream, transform
from .generator import WEEK, Change, SeasonalModel, fit_seasonal_model, inject, make_control


@dataclass
class Config:
    n_clients: int = 20
    seeds: tuple[int, ...] = (0, 1, 2)
    calib_seeds: tuple[int, ...] = (100, 101, 102)  # control series used only for calibration
    warmup: int = 4 * WEEK  # reference window for KS/PSI and for the seasonal profile
    n_points: int = 12 * WEEK  # total length of every synthetic series
    t0: int = 8 * WEEK  # first changed point
    detect_window: int = WEEK  # alarm inside [t0, t0 + window) counts as a detection
    magnitudes: tuple[float, ...] = (0.5, 1.0, 2.0, 3.0)
    kinds: tuple[str, ...] = ("level_shift", "trend_ramp")
    target_far: float = 2.0  # alarms per 1000 points that calibration aims at
    include_real: bool = True
    processes: int | None = None


# ------------------------------------------------------------------ series
def fit_models(cfg: Config) -> list[SeasonalModel]:
    hourly = load_hourly()
    clients = select_clients(hourly, cfg.n_clients)
    return [fit_seasonal_model(source_series(hourly, c), client=c) for c in clients]


def control_tasks(models, seeds, cfg) -> list[dict]:
    return [dict(client=m.client, seed=s, kind="none", magnitude=0.0, x=make_control(m, cfg.n_points, s)) for m in models for s in seeds]


def build_tasks(models: list[SeasonalModel], cfg: Config) -> list[dict]:
    tasks = []
    for m in models:
        for seed in cfg.seeds:
            control = make_control(m, cfg.n_points, seed)
            tasks.append(dict(client=m.client, seed=seed, kind="none", magnitude=0.0, x=control))
            for kind in cfg.kinds:
                for mag in cfg.magnitudes:
                    y = inject(control, m, Change(kind, mag, cfg.t0), seed=seed)
                    tasks.append(dict(client=m.client, seed=seed, kind=kind, magnitude=mag, x=y))
    if cfg.include_real:
        hourly = load_hourly()
        for m in models:
            x = source_series(hourly, m.client).to_numpy(dtype=float)
            tasks.append(dict(client=m.client, seed=-1, kind="real", magnitude=0.0, x=x))
    return tasks


# ------------------------------------------------------------- calibration
def _batch_stats_job(args):
    task, cfg = args
    out = {}
    for variant in VARIANTS:
        z = transform(variant, task["x"], cfg.warmup)
        for name in BATCH:
            out[(name, variant)] = run_batch(name, z, cfg.warmup)[1]
    return out


def _stream_far_job(args):
    task, cfg = args
    out = {}
    n_eval = len(task["x"]) - cfg.warmup
    for variant in VARIANTS:
        z = transform(variant, task["x"], cfg.warmup)
        for name, spec in STREAM.items():
            for p in spec["grid"]:
                out[(name, variant, p)] = 1000.0 * len(run_stream(name, z, cfg.warmup, p)) / n_eval
    return out


def calibrate(models: list[SeasonalModel], cfg: Config, pool: Pool) -> tuple[dict, pd.DataFrame]:
    """Thresholds/parameters giving `cfg.target_far` alarms per 1000 points on
    control series generated with `cfg.calib_seeds`."""
    tasks = control_tasks(models, cfg.calib_seeds, cfg)
    from .detectors import STRIDE

    share = cfg.target_far * STRIDE / 1000.0  # share of daily batch tests allowed to alarm
    settings, rows = {}, []
    stats = pool.map(_batch_stats_job, [(t, cfg) for t in tasks], chunksize=4)
    for name in BATCH:
        for variant in VARIANTS:
            allv = np.concatenate([s[(name, variant)] for s in stats])
            thr = float(np.quantile(allv, 1.0 - share))
            settings[(name, variant)] = thr
            rows.append(dict(detector=name, variant=variant, parameter="threshold", default=batch_default_threshold(name, cfg.warmup), calibrated=thr))
    fars = pool.map(_stream_far_job, [(t, cfg) for t in tasks], chunksize=4)
    for name, spec in STREAM.items():
        for variant in VARIANTS:
            mean_far = {p: float(np.mean([f[(name, variant, p)] for f in fars])) for p in spec["grid"]}
            best = min(spec["grid"], key=lambda p: (abs(mean_far[p] - cfg.target_far), -mean_far[p]))
            settings[(name, variant)] = best
            rows.append(dict(detector=name, variant=variant, parameter=spec["param"], default=spec["default"], calibrated=best, far_grid=str({p: round(v, 2) for p, v in mean_far.items()})))
    return settings, pd.DataFrame(rows)


# -------------------------------------------------------------- evaluation
def _metrics(alarms: list[int], task: dict, cfg: Config) -> dict:
    x = task["x"]
    if task["kind"] in ("none", "real"):
        n_eval = len(x) - cfg.warmup
        return dict(n_alarms=len(alarms), far=1000.0 * len(alarms) / n_eval, detected=np.nan, delay=np.nan)
    pre = [a for a in alarms if a < cfg.t0]
    post = [a for a in alarms if cfg.t0 <= a < cfg.t0 + cfg.detect_window]
    return dict(n_alarms=len(alarms), far=1000.0 * len(pre) / (cfg.t0 - cfg.warmup), detected=float(bool(post)), delay=float(post[0] - cfg.t0) if post else np.nan)


def evaluate_task(args) -> list[dict]:
    task, cfg, settings = args
    base = dict(client=task["client"], seed=task["seed"], kind=task["kind"], magnitude=task["magnitude"])
    rows = []
    for variant in VARIANTS:
        z = transform(variant, task["x"], cfg.warmup)
        for name in BATCH:
            idx, vals = run_batch(name, z, cfg.warmup)
            for setting, thr in (("default", batch_default_threshold(name, cfg.warmup)), ("calibrated", settings[(name, variant)])):
                alarms = [int(i) for i, v in zip(idx, vals) if v > thr]
                rows.append(dict(base, detector=name, variant=variant, setting=setting, **_metrics(alarms, task, cfg)))
        for name, spec in STREAM.items():
            for setting, p in (("default", spec["default"]), ("calibrated", settings[(name, variant)])):
                alarms = run_stream(name, z, cfg.warmup, p)
                rows.append(dict(base, detector=name, variant=variant, setting=setting, **_metrics(alarms, task, cfg)))
    return rows


def run_experiment(cfg: Config):
    models = fit_models(cfg)
    with Pool(cfg.processes) as pool:
        settings, calib = calibrate(models, cfg, pool)
        tasks = build_tasks(models, cfg)
        results = pool.map(evaluate_task, [(t, cfg, settings) for t in tasks], chunksize=2)
    runs = pd.DataFrame([r for rows in results for r in rows])
    return runs, models, calib


def summarize(runs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    far = (
        runs[runs.kind.isin(["none", "real"])]
        .groupby(["setting", "kind", "detector", "variant"])
        .agg(far_mean=("far", "mean"), far_median=("far", "median"), series=("far", "size"))
        .reset_index()
    )
    det = (
        runs[~runs.kind.isin(["none", "real"])]
        .groupby(["setting", "kind", "magnitude", "detector", "variant"])
        .agg(detect_rate=("detected", "mean"), delay_median=("delay", "median"), delay_mean=("delay", "mean"), far_pre=("far", "mean"), series=("detected", "size"))
        .reset_index()
    )
    return {"far": far, "detect": det}
