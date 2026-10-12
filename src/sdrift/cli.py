"""Command line entry point.

    python -m sdrift.cli prepare            # raw txt -> hourly parquet
    python -m sdrift.cli run [--clients N] [--seeds K] [--out results]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from .data import prepare_hourly
from .evaluate import Config, run_experiment, summarize
from .generator import Change, inject, make_control
from .plots import plot_delay, plot_detectability, plot_example, plot_far


def cmd_prepare(args):
    h = prepare_hourly()
    print(f"hourly: {h.shape[0]} rows x {h.shape[1]} clients, {h.index[0]} .. {h.index[-1]}")


def write_summary_md(cfg: Config, summ: dict, models, calib: pd.DataFrame, out: Path):
    far, det = summ["far"], summ["detect"]
    lines = ["# MVP results", ""]
    lines.append(f"Clients: {len(models)} ({', '.join(m.client for m in models)}). Seeds per client: {len(cfg.seeds)}.")
    lines.append(f"Series length {cfg.n_points} h, warm-up {cfg.warmup} h, change at point {cfg.t0}, detection window {cfg.detect_window} h.")
    lines.append(f"Settings: `default` = textbook thresholds (KS p < 0.05, PSI > 0.1, River defaults); `calibrated` = thresholds chosen on separate control series so that every detector gives about {cfg.target_far:g} false alarms per 1000 points.")
    lines.append("")
    lines += ["## Calibrated parameters", "", calib.drop(columns=[c for c in ("far_grid",) if c in calib]).to_markdown(index=False, floatfmt=".4g"), ""]
    for setting in ("default", "calibrated"):
        lines += [f"# Setting: {setting}", ""]
        for kind, title in (("none", "False alarms on control series without changes (alarms per 1000 points, mean over series)"), ("real", "Alarms on the real source series, autumn 2013, unlabelled (alarms per 1000 points)")):
            t = far[(far.kind == kind) & (far.setting == setting)].pivot(index="detector", columns="variant", values="far_mean").round(2)
            if t.empty:
                continue
            lines += [f"## {title}", "", t.to_markdown(), ""]
        for kind in sorted(det.kind.unique()):
            d = det[(det.kind == kind) & (det.setting == setting)]
            rate = d.pivot_table(index="detector", columns=["variant", "magnitude"], values="detect_rate").round(2)
            delay = d.pivot_table(index="detector", columns=["variant", "magnitude"], values="delay_median").round(0)
            lines += [f"## Change type: {kind}", "", "Share of series where the change was detected within one week (columns: variant, magnitude in sigma):", "", rate.to_markdown(), "", "Median delay in hours among detected series:", "", delay.to_markdown(), ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def make_report(cfg: Config, runs: pd.DataFrame, models, calib: pd.DataFrame, out: Path):
    summ = summarize(runs)
    summ["far"].to_csv(out / "far_summary.csv", index=False)
    summ["detect"].to_csv(out / "detect_summary.csv", index=False)
    write_summary_md(cfg, summ, models, calib, out / "summary.md")
    for setting in ("default", "calibrated"):
        plot_far(summ["far"], "none", out / f"far_control_{setting}.png", f"False alarms on series without changes ({setting} thresholds)", setting)
        if "real" in set(summ["far"].kind):
            plot_far(summ["far"], "real", out / f"far_real_{setting}.png", f"Alarms on real series, autumn 2013, unlabelled ({setting} thresholds)", setting)
        for kind in cfg.kinds:
            plot_detectability(summ["detect"], kind, out / f"detectability_{kind}_{setting}.png", setting)
            plot_delay(summ["detect"], kind, out / f"delay_{kind}_{setting}.png", setting)
    # example: the client with the largest seasonal amplitude
    m = max(models, key=lambda m: m.amplitude)
    control = make_control(m, cfg.n_points, cfg.seeds[0])
    shifted = inject(control, m, Change("level_shift", 1.0, cfg.t0))
    plot_example(control, shifted, cfg.t0, cfg.warmup, m.client, 1.0, out / "example_series.png")


def cmd_run(args):
    t = time.time()
    cfg = Config(n_clients=args.clients, seeds=tuple(range(args.seeds)), processes=args.processes, target_far=args.target_far)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs, models, calib = run_experiment(cfg)
    runs.to_csv(out / "runs.csv", index=False)
    calib.to_csv(out / "calibration.csv", index=False)
    make_report(cfg, runs, models, calib, out)
    print(f"done in {time.time() - t:.0f} s: {len(runs)} rows -> {out}")
    print((out / "summary.md").read_text(encoding="utf-8"))


def cmd_report(args):
    """Rebuild tables and figures from a finished run without recomputing it."""
    from .evaluate import fit_models

    cfg = Config(n_clients=args.clients, seeds=tuple(range(args.seeds)), target_far=args.target_far)
    out = Path(args.out)
    runs = pd.read_csv(out / "runs.csv")
    calib = pd.read_csv(out / "calibration.csv")
    make_report(cfg, runs, fit_models(cfg), calib, out)
    print(f"report rebuilt in {out}")


def main():
    p = argparse.ArgumentParser(prog="sdrift")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare").set_defaults(func=cmd_prepare)
    r = sub.add_parser("run")
    r.add_argument("--clients", type=int, default=20)
    r.add_argument("--seeds", type=int, default=3)
    r.add_argument("--processes", type=int, default=None)
    r.add_argument("--target-far", type=float, default=2.0, help="false alarms per 1000 points that calibration aims at")
    r.add_argument("--out", default="results")
    r.set_defaults(func=cmd_run)
    rp = sub.add_parser("report")
    for a in r._actions:
        if a.dest in ("clients", "seeds", "target_far", "out"):
            rp.add_argument(*a.option_strings, type=a.type, default=a.default)
    rp.set_defaults(func=cmd_report)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
