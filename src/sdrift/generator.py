"""Control series without changes and injection of changes of known type,
moment and magnitude.

A real hourly series is decomposed with MSTL (periods 24 and 168). The weekly
seasonal profile is averaged over the weeks, the trend is replaced by a
constant level, the residuals are cleaned of outliers and week-to-week
variance changes, and then resampled with a seasonal block bootstrap (daily
blocks aligned to the weekday). The result keeps the real seasonal shape and
the noise structure inside a week but has no changes by construction.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import MSTL

WEEK = 168
DAY = 24


@dataclass
class SeasonalModel:
    client: str
    profile: np.ndarray  # length 168, hour-of-week seasonal profile (mean zero)
    level: float  # constant level replacing the trend
    resid: np.ndarray  # residuals of the source series
    sigma: float  # std of residuals

    @property
    def amplitude(self) -> float:
        return float(self.profile.max() - self.profile.min())


def clean_residuals(resid: np.ndarray, winsor: float = 4.0) -> np.ndarray:
    """Make the residual process free of changes by construction: clip gross
    outliers at `winsor` robust sigmas and give every week the same spread
    (the median weekly standard deviation). Autocorrelation and the
    hour-of-week variance pattern inside a week are kept."""
    r = resid - np.median(resid)
    robust_sigma = 1.4826 * np.median(np.abs(r))
    r = np.clip(r, -winsor * robust_sigma, winsor * robust_sigma)
    n_weeks = len(r) // WEEK
    weeks = r[: n_weeks * WEEK].reshape(n_weeks, WEEK)
    weeks = weeks - weeks.mean(axis=1, keepdims=True)
    sd = weeks.std(axis=1, ddof=1)
    weeks = weeks * (np.median(sd) / sd)[:, None]
    out = weeks.ravel()
    return out - out.mean()


def fit_seasonal_model(y: pd.Series, client: str = "") -> SeasonalModel:
    values = y.to_numpy(dtype=float)
    res = MSTL(values, periods=(DAY, WEEK), stl_kwargs={"robust": True}).fit()
    seasonal = np.asarray(res.seasonal).sum(axis=1) if np.ndim(res.seasonal) == 2 else np.asarray(res.seasonal)
    trend = np.asarray(res.trend)
    resid = clean_residuals(values - seasonal - trend)
    n_weeks = len(values) // WEEK
    profile = seasonal[: n_weeks * WEEK].reshape(n_weeks, WEEK).mean(axis=0)
    profile = profile - profile.mean()
    level = float(np.median(trend))
    return SeasonalModel(client=client, profile=profile, level=level, resid=resid, sigma=float(resid.std(ddof=1)))


def block_bootstrap(resid: np.ndarray, n: int, rng: np.random.Generator, start_day: int = 0) -> np.ndarray:
    """Seasonal block bootstrap with daily blocks aligned to the day of the
    week: day d of the output is a randomly chosen source day with the same
    weekday (Politis 2001; Dudek et al. 2014). Keeps intra-day autocorrelation
    and the hour-of-week variance pattern, so whole weeks of the output have
    the same composition."""
    n_weeks = len(resid) // WEEK
    n_days = int(np.ceil(n / DAY))
    weeks = rng.integers(0, n_weeks, size=n_days)
    out = np.concatenate([resid[w * WEEK + ((d + start_day) % 7) * DAY :][:DAY] for d, w in enumerate(weeks)])
    return out[:n]


def make_control(model: SeasonalModel, n: int, seed: int, block_len: int = DAY) -> np.ndarray:
    """Series of length `n` starting at Monday 00:00 with no changes."""
    rng = np.random.default_rng(seed)
    how = np.arange(n) % WEEK
    return model.level + model.profile[how] + block_bootstrap(model.resid, n, rng)


@dataclass
class Change:
    kind: str  # level_shift | trend_ramp | variance
    magnitude: float  # in units of residual sigma (variance: multiplier of sigma)
    t0: int  # index of the first changed point


def inject(x: np.ndarray, model: SeasonalModel, change: Change, ramp_len: int = WEEK, seed: int = 0) -> np.ndarray:
    y = x.copy()
    t = np.arange(len(y))
    after = t >= change.t0
    delta = change.magnitude * model.sigma
    if change.kind == "level_shift":
        y[after] += delta
    elif change.kind == "trend_ramp":
        ramp = np.clip((t - change.t0 + 1) / ramp_len, 0, 1)
        y += delta * ramp * after
    elif change.kind == "variance":
        rng = np.random.default_rng(seed + 10_000)
        extra = block_bootstrap(model.resid, int(after.sum()), rng, start_day=change.t0 // DAY)
        y[after] += extra * np.sqrt(max(change.magnitude**2 - 1.0, 0.0))
    else:
        raise ValueError(change.kind)
    return y
