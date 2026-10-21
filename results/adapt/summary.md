# Stream B (RQ3): reference adaptation strategies and the oracles

Day-ahead LightGBM forecasts, a decision about the model every day (always, oracle) or week (scheduled, oracle_weekly).
MASE is scaled by the weekly seasonal naive error on the training data. Regret = MASE after the change minus the ideal oracle's.
Retrains count deployed retrainings only (for the oracles: the chosen actions, not the trial fits).
gain_vs_nothing = MASE(do nothing) - MASE(strategy) after the change; share_gain_significant = share of series where the lower bound of the 95% moving block bootstrap interval is above 0.

| source    | scenario      | strategy      |   series |   mase_pre |   mase_post |   regret |   retrains |   gain_vs_nothing |   share_gain_significant |
|:----------|:--------------|:--------------|---------:|-----------:|------------:|---------:|-----------:|------------------:|-------------------------:|
| entsoe    | lockdown_2020 | naive         |        8 |      0.976 |       1.025 |    0.539 |      0     |            -0.238 |                    0     |
| entsoe    | lockdown_2020 | nothing       |        8 |      0.546 |       0.787 |    0.301 |      0     |           nan     |                  nan     |
| entsoe    | lockdown_2020 | always        |        8 |      0.543 |       0.65  |    0.164 |    174     |             0.137 |                    0.75  |
| entsoe    | lockdown_2020 | scheduled     |        8 |      0.546 |       0.696 |    0.209 |     24     |             0.092 |                    0.625 |
| entsoe    | lockdown_2020 | oracle_weekly |        8 |      0.525 |       0.607 |    0.121 |     17.5   |             0.18  |                    1     |
| entsoe    | lockdown_2020 | oracle        |        8 |      0.451 |       0.486 |    0     |    139.125 |             0.301 |                    1     |
| synthetic | level_shift   | naive         |       60 |      0.924 |       1.121 |    0.228 |      0     |             0.232 |                    0.783 |
| synthetic | level_shift   | nothing       |       60 |      0.899 |       1.353 |    0.459 |      0     |           nan     |                  nan     |
| synthetic | level_shift   | always        |       60 |      0.9   |       1.004 |    0.111 |     97     |             0.349 |                    0.95  |
| synthetic | level_shift   | scheduled     |       60 |      0.899 |       1.091 |    0.198 |     13     |             0.261 |                    0.8   |
| synthetic | level_shift   | oracle_weekly |       60 |      0.871 |       1.021 |    0.128 |      9     |             0.332 |                    0.967 |
| synthetic | level_shift   | oracle        |       60 |      0.807 |       0.893 |    0     |     75.75  |             0.459 |                    1     |
| synthetic | none          | naive         |       60 |      0.924 |       1.001 |    0.214 |      0     |            -0.096 |                    0     |
| synthetic | none          | nothing       |       60 |      0.899 |       0.905 |    0.119 |      0     |           nan     |                  nan     |
| synthetic | none          | always        |       60 |      0.9   |       0.87  |    0.083 |     97     |             0.035 |                    0.75  |
| synthetic | none          | scheduled     |       60 |      0.899 |       0.87  |    0.084 |     13     |             0.035 |                    0.767 |
| synthetic | none          | oracle_weekly |       60 |      0.871 |       0.841 |    0.054 |      9.417 |             0.064 |                    0.983 |
| synthetic | none          | oracle        |       60 |      0.807 |       0.787 |    0     |     76.367 |             0.119 |                    1     |
| synthetic | trend_ramp    | naive         |       60 |      0.924 |       1.094 |    0.224 |      0     |             0.228 |                    0.817 |
| synthetic | trend_ramp    | nothing       |       60 |      0.899 |       1.322 |    0.452 |      0     |           nan     |                  nan     |
| synthetic | trend_ramp    | always        |       60 |      0.9   |       0.98  |    0.11  |     97     |             0.342 |                    0.983 |
| synthetic | trend_ramp    | scheduled     |       60 |      0.899 |       1.013 |    0.143 |     13     |             0.308 |                    0.95  |
| synthetic | trend_ramp    | oracle_weekly |       60 |      0.871 |       0.955 |    0.085 |      9     |             0.367 |                    1     |
| synthetic | trend_ramp    | oracle        |       60 |      0.807 |       0.87  |    0     |     75.167 |             0.452 |                    1     |
| synthetic | variance      | naive         |       60 |      0.924 |       1.996 |    0.463 |      0     |            -0.327 |                    0     |
| synthetic | variance      | nothing       |       60 |      0.899 |       1.669 |    0.136 |      0     |           nan     |                  nan     |
| synthetic | variance      | always        |       60 |      0.9   |       1.677 |    0.144 |     97     |            -0.008 |                    0.033 |
| synthetic | variance      | scheduled     |       60 |      0.899 |       1.673 |    0.14  |     13     |            -0.004 |                    0.05  |
| synthetic | variance      | oracle_weekly |       60 |      0.871 |       1.611 |    0.078 |      8.317 |             0.058 |                    0.667 |
| synthetic | variance      | oracle        |       60 |      0.807 |       1.533 |    0     |     74.767 |             0.136 |                    1     |

## Actions chosen by the oracles (share of decisions)

| strategy      | source    | scenario      |   decisions |   keep |   retrain_full |   retrain_8w |   retrain_2w |   reweight_1w |   add_profile |   recalibrate_level |
|:--------------|:----------|:--------------|------------:|-------:|---------------:|-------------:|-------------:|--------------:|--------------:|--------------------:|
| oracle_weekly | entsoe    | lockdown_2020 |         192 |   0.15 |           0.24 |         0.06 |         0.05 |          0.06 |          0.32 |                0.12 |
| oracle        | entsoe    | lockdown_2020 |        1392 |   0.09 |           0.18 |         0.12 |         0.12 |          0.16 |          0.22 |                0.11 |
| oracle_weekly | synthetic | level_shift   |         780 |   0.09 |           0.2  |         0.07 |         0.04 |          0.07 |          0.31 |                0.21 |
| oracle        | synthetic | level_shift   |        5820 |   0.09 |           0.16 |         0.12 |         0.11 |          0.11 |          0.28 |                0.12 |
| oracle_weekly | synthetic | none          |         780 |   0.14 |           0.27 |         0.05 |         0.01 |          0.03 |          0.36 |                0.13 |
| oracle        | synthetic | none          |        5820 |   0.1  |           0.21 |         0.11 |         0.08 |          0.1  |          0.3  |                0.11 |
| oracle_weekly | synthetic | trend_ramp    |         780 |   0.11 |           0.21 |         0.06 |         0.03 |          0.05 |          0.34 |                0.2  |
| oracle        | synthetic | trend_ramp    |        5820 |   0.1  |           0.16 |         0.11 |         0.11 |          0.1  |          0.29 |                0.13 |
| oracle_weekly | synthetic | variance      |         780 |   0.2  |           0.23 |         0.04 |         0.01 |          0.05 |          0.31 |                0.16 |
| oracle        | synthetic | variance      |        5820 |   0.12 |           0.19 |         0.1  |         0.1  |          0.1  |          0.29 |                0.11 |
