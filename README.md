# sdrift: seasonality-aware drift detection, MVP experiments

Master's thesis project (Neoversity, MDS 6): *Development of an Information
System for Seasonality-Aware Detection of Changes in the Statistical
Properties of Time Series and Evaluation of Large Language Model
Recommendations.*

This repository holds the first experiment: classical drift detectors on
hourly electricity load, run on raw series and on seasonal residuals, with a
benchmark that has no need for hand-made change labels.

## Data

UCI ElectricityLoadDiagrams 2011-2014 (370 clients, 15-minute kW values).
The archive is downloaded into `data/raw/` and converted to an hourly table:

```
curl -L -o data/raw/electricityloaddiagrams20112014.zip \
  https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip
unzip -d data/raw data/raw/electricityloaddiagrams20112014.zip
python -m sdrift.cli prepare
```

Cleaning: timestamps are moved to the start of the interval, the March DST
hour (zeros) is interpolated, the October DST hour (two hours summed) is
halved, clients active before 2013 with almost no zero readings are kept.

## Benchmark without change labels

1. **Control series without changes.** For every client the autumn-2013
   window (12 full weeks, no public holidays) is decomposed with MSTL
   (periods 24 and 168). The weekly seasonal profile is averaged, the trend is
   replaced by a constant level, residuals are cleaned (outliers clipped,
   week-to-week variance equalised) and resampled with a seasonal block
   bootstrap: daily blocks drawn from the same weekday. The result keeps the
   real seasonal shape and the intra-week noise structure and has no changes
   by construction. False alarms are counted on these series.
2. **Injected changes** of known type, moment and magnitude: level shift and
   one-week trend ramp, magnitude 0.5, 1, 2, 3 residual sigmas. Detection
   rate inside one week after the change and the delay are measured.
3. Real, unlabelled autumn-2013 series are also run through every detector
   as an illustration (alarm counts only).

## Detectors

| Name | What it does |
|---|---|
| KS-1d, KS-1w | two-sample Kolmogorov-Smirnov: fixed 4-week reference vs the last day / last week, tested daily |
| PSI-1d, PSI-1w | population stability index with 10 reference-quantile bins, same windows |
| ADWIN, PageHinkley, KSWIN | streaming detectors from River |

Every detector runs in two variants: `raw` (the series itself) and `resid`
(residuals after removing an hour-of-week profile and level estimated on
the 4-week warm-up; inside the warm-up the profile is cross-fitted
leave-one-week-out). Inputs are standardised with warm-up statistics.

Two settings: `default` (KS p < 0.05, PSI > 0.1, River defaults) and
`calibrated` (threshold or sensitivity parameter chosen on separate control
series so that every detector gives about 2 false alarms per 1000 points).
Only the calibrated setting compares detectors fairly.

## Running

```
python -m venv .venv && . .venv/bin/activate
pip install -e .
python -m sdrift.cli run --clients 20 --seeds 3 --out results
```

Outputs in `results/`: `summary.md` (tables), `calibration.csv`,
`far_summary.csv`, `detect_summary.csv`, `runs.csv` (one row per series and
detector) and the figures `far_control_*.png`, `detectability_*.png`,
`delay_*.png`, `example_series.png`.

## Stream B (RQ3): reference adaptation strategies

A deployed LightGBM model forecasts every day the next 24 hours (all features use values at least
24 hours old: hour, weekday, lags 24/48/168/336, lagged daily and weekly means; yearly terms for the
national series). Its settings were chosen on validation windows that do not overlap the test runs
(`adapt --tune`, results in `results/adapt/tune.md`).

Initial action catalog (`src/sdrift/actions.py`): do nothing, retrain on all history, retrain on the
last 8 weeks, shorten the window to 2 weeks, reweight recent data (half-life 1 week), add a seasonal
feature (4-week hour-of-week profile), recalibrate the forecast level on the last week. Interval
recalibration is listed but not used until prediction intervals exist.

Strategies (`src/sdrift/adapt.py`): `nothing`, `always` (retrain daily), `scheduled` (retrain weekly),
`oracle_weekly` and `oracle` (the catalog action with the lowest error on the next week / day, chosen
in hindsight; upper bounds, not deployable). Metrics: MASE (scaled by the weekly seasonal naive error
on the training data) before and after the change, regret against the ideal oracle, number of
retrainings, and the gain over `nothing` with a 95% moving block bootstrap interval over days.

Data: 240 synthetic series (20 UCI clients x 3 seeds x {no change, level shift 2 sigma, one-week
ramp 2 sigma, noise x2}, 24 weeks, deployment at week 10, change at week 13) and the national load of
8 countries (ENTSO-E via Open Power System Data, 2017-2020, deployment 6 January 2020, the change is
the date of the March 2020 measures).

```
python -m sdrift.cli adapt --tune          # base model validation
python -m sdrift.cli adapt --clients 20 --seeds 3
python -m sdrift.cli adapt --report        # rebuild tables and figures without recomputing
```

The full run takes about 40 minutes on 16 cores. Set `OMP_NUM_THREADS=1`: every process trains its own
models, and extra threads only compete for the same cores.

Outputs in `results/adapt/`: `summary.md`, `summary.csv`, `runs.csv`, `oracle_picks.csv`, `tune.md`,
`quality_cost.png`, and the examples `example_level_shift.*` and `example_entsoe_PT.*` (forecasts
as CSV and the figure).

## Known limitations of this MVP

* The seasonal profile of the control series is constant, so the residual
  variant is evaluated in the setting it was designed for; real series have
  slowly changing seasonality (see the unlabelled real-series table).
* Residuals of load series are autocorrelated within a day; distribution
  tests assume independent samples, which is why default thresholds give
  more false alarms on residuals and calibration is necessary.
* Only two change types are injected so far; seasonal-amplitude and
  variance changes and the TCPDBench check are planned next.
