import numpy as np

from sdrift.actions import ACTIONS, CATALOG, apply_action
from sdrift.adapt import STRATEGIES, backtest, mase, mase_gain_ci
from sdrift.forecast import BASE_FEATURES, DAY, WEEK, Model, calendar_from_index, feature_table, mase_scale

N, T_DEPLOY, T_CHANGE = 16 * WEEK, 8 * WEEK, 11 * WEEK


def toy(shift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(N)
    y = 100 + 20 * np.sin(2 * np.pi * t / DAY) + 8 * np.sin(2 * np.pi * t / WEEK) + rng.normal(0, 3, N)
    y[T_CHANGE:] += shift
    hour, dow = calendar_from_index(N)
    return y, feature_table(y, hour, dow)


def test_features_do_not_see_the_forecast_day():
    y, F = toy()
    y2 = y.copy()
    y2[T_DEPLOY:] += 1000.0  # change everything from the origin on
    hour, dow = calendar_from_index(N)
    F2 = feature_table(y2, hour, dow)
    rows = np.arange(0, T_DEPLOY + DAY)  # the whole first forecast day must be unaffected
    for f in BASE_FEATURES:
        assert np.allclose(F[f][rows], F2[f][rows], equal_nan=True), f


def test_catalog_actions_run_and_retrain_count():
    y, F = toy(shift=15)
    model, _ = apply_action(ACTIONS["retrain_full"], Model(BASE_FEATURES), F, y, T_DEPLOY, BASE_FEATURES)
    for a in CATALOG:
        m, fits = apply_action(a, model, F, y, T_CHANGE + WEEK, BASE_FEATURES)
        assert fits == (1 if a.kind == "retrain" else 0)
        assert np.isfinite(m.predict(F, np.arange(T_CHANGE + WEEK, T_CHANGE + WEEK + DAY))).all()


def test_oracle_is_never_worse_than_scheduled_and_beats_nothing_after_a_shift():
    y, F = toy(shift=15)
    by = {s.name: s for s in STRATEGIES}
    scale = mase_scale(y[:T_DEPLOY])
    cache = {}
    r = {k: backtest(y, F, T_DEPLOY, by[k], BASE_FEATURES, cache=cache) for k in ("nothing", "scheduled", "oracle_weekly")}
    end = r["nothing"]["end"]
    m = {k: mase(y, v["pred"], T_DEPLOY, end, scale) for k, v in r.items()}
    assert m["oracle_weekly"] <= m["scheduled"] + 1e-9
    assert m["oracle_weekly"] < m["nothing"]
    assert r["scheduled"]["retrains"] == (end - T_DEPLOY) // DAY // 7 - (1 if ((end - T_DEPLOY) // DAY) % 7 == 0 else 0)


def test_mase_gain_ci_sign():
    y, _ = toy()
    biased = y + 5.0
    perfect = y.copy()
    g, lo, hi = mase_gain_ci(y, biased, perfect, T_DEPLOY, T_DEPLOY + 4 * WEEK, scale=mase_scale(y[:T_DEPLOY]))
    assert g > 0 and lo > 0 and lo <= g <= hi
    g, lo, hi = mase_gain_ci(y, perfect, biased, T_DEPLOY, T_DEPLOY + 4 * WEEK, scale=mase_scale(y[:T_DEPLOY]))
    assert g < 0 and hi < 0
