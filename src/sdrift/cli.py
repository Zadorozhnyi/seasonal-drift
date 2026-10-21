"""Command line entry point.

    python -m sdrift.cli prepare            # raw txt -> hourly parquet
    python -m sdrift.cli run [--clients N] [--seeds K] [--out results]
"""
from __future__ import annotations

import argparse
import sys
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


ENTSOE_FILE = Path("data/raw/opsd/time_series_60min_singleindex.csv")
TUNE_CONFIGS = {
    "A: 200 rounds, lr 0.05, 31 leaves": {},
    "B: 400 rounds, lr 0.05, 63 leaves": dict(rounds=400, num_leaves=63),
    "C: 300 rounds, lr 0.03, 15 leaves": dict(rounds=300, learning_rate=0.03, num_leaves=15),
    "D: 200 rounds, lr 0.10, 31 leaves": dict(learning_rate=0.10),
}


def cmd_adapt(args):
    """Stream B (RQ3): base model validation, reference strategies and the oracle."""
    from .adapt import SYN_DEPLOY_WEEK, entsoe_series, run_adapt, synthetic_series, tune_base_model
    from .evaluate import fit_models
    from .forecast import LGBM_PARAMS, WEEK

    t = time.time()
    out = Path(args.out) / "adapt"
    out.mkdir(parents=True, exist_ok=True)
    cache = {}

    def models():
        if "m" not in cache:
            cache["m"] = fit_models(Config(n_clients=args.clients))
        return cache["m"]

    real = ENTSOE_FILE.exists() and not args.no_real
    if args.tune:
        # validation only: other control seeds, and 2019 for ENTSO-E (the test period is 2020)
        tune = synthetic_series(models(), [900, 901], scenarios=(("none", 0.0),))
        for s in tune:
            s["t_stop"] = (SYN_DEPLOY_WEEK + 6) * WEEK
        if real:
            tune += entsoe_series(str(ENTSOE_FILE), start="2017-01-02", deploy="2019-09-02", end="2019-12-01 23:00")
        configs = {k: dict(LGBM_PARAMS, **v) for k, v in TUNE_CONFIGS.items()}
        res = tune_base_model(tune, configs, args.processes)
        res.to_csv(out / "tune.csv", index=False)
        table = res.groupby(["source", "config"]).agg(mase=("mase", "mean"), mase_naive=("mase_naive", "mean"), series=("series", "nunique")).round(3)
        (out / "tune.md").write_text("# Base model validation (static model, MASE)\n\n" + table.to_markdown() + "\n", encoding="utf-8")
        print(table.to_string())
        return
    if not args.report:
        # the long ENTSO-E series go first, so they run alongside the synthetic ones
        series = (entsoe_series(str(ENTSOE_FILE)) if real else []) + synthetic_series(models(), list(range(args.seeds)))
        runs = run_adapt(series, args.processes, log=sys.stderr)
        runs.to_csv(out / "runs.csv", index=False)
    runs = pd.read_csv(out / "runs.csv")
    summ = write_adapt_report(runs, out)
    adapt_examples(models, out, real, recompute=not args.report)
    print(f"done in {time.time() - t:.0f} s -> {out}")
    print(summ.round(3).to_string(index=False))


def write_adapt_report(runs: pd.DataFrame, out: Path) -> pd.DataFrame:
    from .adapt import oracle_picks, summarize_adapt
    from .plots_adapt import plot_quality_cost

    summ = summarize_adapt(runs)
    summ.to_csv(out / "summary.csv", index=False)
    picks = oracle_picks(runs)
    picks.to_csv(out / "oracle_picks.csv", index=False)
    lines = ["# Stream B (RQ3): reference adaptation strategies and the oracles", "",
             "Day-ahead LightGBM forecasts, a decision about the model every day (always, oracle) or week (scheduled, oracle_weekly).",
             "MASE is scaled by the weekly seasonal naive error on the training data. Regret = MASE after the change minus the ideal oracle's.",
             "Retrains count deployed retrainings only (for the oracles: the chosen actions, not the trial fits).",
             "gain_vs_nothing = MASE(do nothing) - MASE(strategy) after the change; share_gain_significant = share of series where the lower bound of the 95% moving block bootstrap interval is above 0.", "",
             summ.round(3).to_markdown(index=False), "", "## Actions chosen by the oracles (share of decisions)", "",
             picks.to_markdown(index=False), ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    plot_quality_cost(summ[summ.strategy != "naive"], out / "quality_cost.png")
    return summ


def adapt_examples(models, out: Path, real: bool, recompute: bool):
    """Two example series (synthetic level shift, Portugal 2020): forecasts are stored as CSV, then plotted."""
    from .adapt import STRATEGIES, backtest, entsoe_series, synthetic_series
    from .forecast import mase_scale
    from .plots_adapt import example_frame, plot_adapt_example

    def build(s, before, after):
        preds = {st.name: backtest(s["y"], s["F"], s["t_deploy"], st, s["base_features"])["pred"]
                 for st in STRATEGIES if st.name in ("nothing", "scheduled", "oracle")}
        return example_frame(s["y"], preds, s["t_change"], mase_scale(s["y"][: s["t_deploy"]]), before, after)

    csv = out / "example_level_shift.csv"
    if recompute or not csv.exists():
        m = max(models(), key=lambda m: m.amplitude)  # the client with the largest seasonal amplitude
        df = build([x for x in synthetic_series([m], [0]) if x["scenario"] == "level_shift"][0], 7, 21)
        df.insert(0, "client", m.client)
        df.to_csv(csv, index=False)
    df = pd.read_csv(csv)
    plot_adapt_example(df, f"Client {df.client.iloc[0]}: level shift of 2σ, day-ahead forecasts", out / "example_level_shift.png", "load, kW")
    if real:
        csv = out / "example_entsoe_PT.csv"
        if recompute or not csv.exists():
            build(entsoe_series(str(ENTSOE_FILE), countries=("PT",))[0], 14, 35).to_csv(csv, index=False)
        plot_adapt_example(pd.read_csv(csv), "Portugal, national load: measures of 16.03.2020, day-ahead forecasts", out / "example_entsoe_PT.png", "load, MW")


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
    ad = sub.add_parser("adapt", help="stream B: reference adaptation strategies and the oracle")
    ad.add_argument("--clients", type=int, default=20)
    ad.add_argument("--seeds", type=int, default=3)
    ad.add_argument("--processes", type=int, default=None)
    ad.add_argument("--out", default="results")
    ad.add_argument("--tune", action="store_true", help="validate base-model settings instead of running the strategies")
    ad.add_argument("--no-real", action="store_true", help="skip the ENTSO-E series")
    ad.add_argument("--report", action="store_true", help="rebuild tables and figures from results/adapt without recomputing")
    ad.set_defaults(func=cmd_adapt)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
