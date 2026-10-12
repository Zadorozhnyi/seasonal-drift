import numpy as np
import pandas as pd

from sdrift.detectors import BATCH, STREAM, run_batch, run_stream, seasonal_residuals, transform
from sdrift.generator import WEEK, Change, fit_seasonal_model, inject, make_control


def toy_series(n=12 * WEEK, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return pd.Series(100 + 20 * np.sin(2 * np.pi * t / 24) + 8 * np.sin(2 * np.pi * t / 168) + rng.normal(0, 5, n))


def test_control_has_profile_and_no_trend():
    m = fit_seasonal_model(toy_series(), client="toy")
    x = make_control(m, 12 * WEEK, seed=1)
    weeks = x.reshape(12, WEEK)
    assert abs(weeks.mean(axis=1).max() - weeks.mean(axis=1).min()) < 3 * m.sigma / np.sqrt(WEEK) * 4
    assert np.corrcoef(weeks[0], weeks[5])[0, 1] > 0.9


def test_residuals_remove_seasonality():
    m = fit_seasonal_model(toy_series(), client="toy")
    x = make_control(m, 12 * WEEK, seed=2)
    r = seasonal_residuals(x, 4 * WEEK)
    assert r[4 * WEEK :].std() < 0.3 * x.std()


def test_level_shift_is_detected():
    m = fit_seasonal_model(toy_series(), client="toy")
    x = make_control(m, 12 * WEEK, seed=3)
    y = inject(x, m, Change("level_shift", 3.0, 8 * WEEK))
    z = transform("resid", y, 4 * WEEK)
    idx, vals = run_batch("KS-1w", z, 4 * WEEK)
    post = vals[(idx >= 8 * WEEK) & (idx < 9 * WEEK)]
    assert post.max() > 0.3
    alarms = run_stream("ADWIN", z, 4 * WEEK, STREAM["ADWIN"]["default"])
    assert any(8 * WEEK <= a < 9 * WEEK for a in alarms)
    assert set(BATCH) == {"KS-1d", "KS-1w", "PSI-1d", "PSI-1w"}
