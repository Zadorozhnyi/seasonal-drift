"""Classical drift detectors run on a univariate stream.

Batch detectors (KS, PSI) imitate a daily monitoring job that compares the
last day (1d) or the last week (1w) with a fixed reference window, the way
Evidently-style monitors compare a current batch with a reference. They
return the test statistic of every batch; an alarm is a statistic above a
threshold. Streaming detectors come from River; their sensitivity parameter
is exposed so that it can be calibrated.

Two settings are evaluated: `default` (textbook thresholds: KS p < 0.05,
PSI > 0.1, River defaults) and `calibrated` (thresholds chosen on control
series so that every detector raises the same number of false alarms).

The `resid` variant feeds the detector with residuals after removing an
hour-of-week seasonal profile and a level estimated on the warm-up window.
"""
from __future__ import annotations

import warnings

import numpy as np
from river import drift
from scipy import stats

WEEK = 168
DAY = 24
KS_C05 = 1.358  # asymptotic KS critical value coefficient for alpha = 0.05


# ---------------------------------------------------------------- transforms
def standardize(x: np.ndarray, warmup: int) -> np.ndarray:
    ref = x[:warmup]
    sd = ref.std(ddof=1)
    return (x - ref.mean()) / (sd if sd > 0 else 1.0)


def seasonal_residuals(x: np.ndarray, warmup: int) -> np.ndarray:
    """Remove the hour-of-week profile and level estimated on x[:warmup].

    Inside the warm-up the profile is cross-fitted (leave-one-week-out), so
    the reference residuals have the same spread as the later ones; otherwise
    in-sample residuals are too narrow and every batch test fires."""
    n = len(x)
    how = np.arange(n) % WEEK
    k = warmup // WEEK
    weeks = x[: k * WEEK].reshape(k, WEEK)
    total = weeks.sum(axis=0)
    resid = np.empty(n)
    for w in range(k):
        loo = (total - weeks[w]) / (k - 1)
        resid[w * WEEK : (w + 1) * WEEK] = weeks[w] - loo
    profile = total / k
    resid[k * WEEK :] = x[k * WEEK :] - profile[how[k * WEEK :]]
    return resid


def transform(variant: str, x: np.ndarray, warmup: int) -> np.ndarray:
    z = x if variant == "raw" else seasonal_residuals(x, warmup)
    return standardize(z, warmup)


# ---------------------------------------------------------- batch detectors
def _batches(x, warmup, window, stride):
    ref = x[:warmup]
    for end in range(warmup + window, len(x) + 1, stride):
        yield end - 1, ref, x[end - window : end]


def ks_statistics(x, warmup, window, stride=DAY):
    idx, vals = [], []
    for i, ref, cur in _batches(x, warmup, window, stride):
        idx.append(i)
        vals.append(stats.ks_2samp(ref, cur, method="asymp").statistic)
    return np.array(idx), np.array(vals)


def psi_statistics(x, warmup, window, stride=DAY, bins=10, eps=1e-4):
    ref = x[:warmup]
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.clip(np.histogram(ref, edges)[0] / len(ref), eps, None)
    idx, vals = [], []
    for i, _, cur in _batches(x, warmup, window, stride):
        q = np.clip(np.histogram(cur, edges)[0] / len(cur), eps, None)
        idx.append(i)
        vals.append(float(np.sum((q - p) * np.log(q / p))))
    return np.array(idx), np.array(vals)


def ks_default_threshold(n_ref: int, window: int) -> float:
    return KS_C05 * np.sqrt((n_ref + window) / (n_ref * window))


BATCH = {
    "KS-1d": dict(fn=ks_statistics, window=DAY),
    "KS-1w": dict(fn=ks_statistics, window=WEEK),
    "PSI-1d": dict(fn=psi_statistics, window=DAY),
    "PSI-1w": dict(fn=psi_statistics, window=WEEK),
}
STRIDE = DAY


def batch_default_threshold(name: str, warmup: int) -> float:
    spec = BATCH[name]
    return ks_default_threshold(warmup, spec["window"]) if name.startswith("KS") else 0.1


def run_batch(name: str, z: np.ndarray, warmup: int):
    spec = BATCH[name]
    return spec["fn"](z, warmup, spec["window"], STRIDE)


# ------------------------------------------------------ streaming detectors
STREAM = {
    "ADWIN": dict(make=lambda p: drift.ADWIN(delta=p), param="delta", default=0.002, grid=(1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 2e-3, 1e-2, 5e-2, 0.2)),
    "PageHinkley": dict(make=lambda p: drift.PageHinkley(delta=0.005, threshold=p, alpha=0.9999), param="threshold", default=50.0, grid=(5.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 150.0, 250.0, 400.0)),
    "KSWIN": dict(make=lambda p: drift.KSWIN(alpha=p, window_size=100, stat_size=30, seed=0), param="alpha", default=0.005, grid=(1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3)),
}


def run_stream(name: str, z: np.ndarray, warmup: int, param: float) -> list[int]:
    det = STREAM[name]["make"](param)
    alarms = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i, v in enumerate(z):
            det.update(float(v))
            if det.drift_detected and i >= warmup:
                alarms.append(i)
    return alarms


DETECTORS = list(BATCH) + list(STREAM)
VARIANTS = ("raw", "resid")
