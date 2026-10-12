"""Figures for the MVP report (matplotlib, static PNG)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .detectors import seasonal_residuals
from .generator import WEEK

# categorical palette, fixed order
COLORS = {"KS-1d": "#2a78d6", "KS-1w": "#6250d6", "PSI-1d": "#eb6834", "PSI-1w": "#e34948", "ADWIN": "#1baf7a", "PageHinkley": "#eda100", "KSWIN": "#e87ba4"}
STYLE = {"raw": dict(linestyle="--", alpha=0.75), "resid": dict(linestyle="-")}
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "font.size": 10,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "lines.linewidth": 2,
        "lines.markersize": 6,
    }
)


def _save(fig, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_example(control: np.ndarray, shifted: np.ndarray, t0: int, warmup: int, client: str, magnitude: float, out: Path):
    lo, hi = t0 - 2 * WEEK, t0 + 2 * WEEK
    t = np.arange(lo, hi) / 24.0
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True)
    axes[0].plot(t, control[lo:hi], color=COLORS["KS-1w"], linewidth=1.2, label="control series (no change)")
    axes[0].plot(t, shifted[lo:hi], color=COLORS["PSI-1w"], linewidth=1.2, alpha=0.85, label=f"level shift of {magnitude:g} sigma")
    axes[0].axvline(t0 / 24.0, color=MUTED, linewidth=1, linestyle=":")
    axes[0].set_ylabel("load, kW")
    axes[0].set_title(f"Client {client}: synthetic series with real seasonal profile", loc="left")
    axes[0].legend(loc="upper left", ncol=2)
    r0 = seasonal_residuals(control, warmup)
    r1 = seasonal_residuals(shifted, warmup)
    axes[1].plot(t, r0[lo:hi], color=COLORS["KS-1w"], linewidth=1.2)
    axes[1].plot(t, r1[lo:hi], color=COLORS["PSI-1w"], linewidth=1.2, alpha=0.85)
    axes[1].axvline(t0 / 24.0, color=MUTED, linewidth=1, linestyle=":")
    axes[1].set_ylabel("residual, kW")
    axes[1].set_xlabel("day")
    axes[1].set_title("Residuals after removing the hour-of-week profile estimated on the warm-up window", loc="left")
    _save(fig, out)


def plot_far(far: pd.DataFrame, kind: str, out: Path, title: str, setting: str = "default"):
    d = far[(far.kind == kind) & (far.setting == setting)].pivot(index="detector", columns="variant", values="far_mean").reindex(list(COLORS))
    fig, ax = plt.subplots(figsize=(8, 4.6))
    y = np.arange(len(d))
    h = 0.36
    ax.barh(y - h / 2, d["raw"], height=h - 0.04, color=[COLORS[k] for k in d.index], alpha=0.45, hatch="///", edgecolor="white", label="raw series")
    ax.barh(y + h / 2, d["resid"], height=h - 0.04, color=[COLORS[k] for k in d.index], edgecolor="white", label="seasonal residuals")
    for yi, (r, s) in enumerate(zip(d["raw"], d["resid"])):
        ax.text(r + 0.5, yi - h / 2, f"{r:.1f}", va="center", fontsize=9, color=TEXT)
        ax.text(s + 0.5, yi + h / 2, f"{s:.1f}", va="center", fontsize=9, color=TEXT)
    ax.set_yticks(y, d.index)
    ax.invert_yaxis()
    ax.set_xlabel("alarms per 1000 points")
    ax.set_title(title, loc="left")
    ax.legend(loc="lower right")
    ax.grid(axis="y", visible=False)
    _save(fig, out)


def _curve(det: pd.DataFrame, kind: str, value: str, ylabel: str, title: str, out: Path, ylim=None, setting: str = "calibrated"):
    d = det[(det.kind == kind) & (det.setting == setting)]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, color in COLORS.items():
        for variant, st in STYLE.items():
            s = d[(d.detector == name) & (d.variant == variant)].sort_values("magnitude")
            if s.empty:
                continue
            ax.plot(s.magnitude, s[value], color=color, marker="o", label=f"{name}, {variant}", **st)
    ax.set_xlabel("change magnitude, in residual sigma")
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks(sorted(d.magnitude.unique()))
    ax.set_title(title, loc="left")
    ax.legend(ncol=2, fontsize=8.5, loc="best")
    _save(fig, out)


def plot_detectability(det: pd.DataFrame, kind: str, out: Path, setting: str = "calibrated"):
    _curve(det, kind, "detect_rate", "share detected within one week", f"Detectability: {kind.replace('_', ' ')} ({setting} thresholds)", out, ylim=(-0.03, 1.03), setting=setting)


def plot_delay(det: pd.DataFrame, kind: str, out: Path, setting: str = "calibrated"):
    _curve(det, kind, "delay_median", "median delay, hours", f"Detection delay: {kind.replace('_', ' ')} ({setting} thresholds)", out, setting=setting)
