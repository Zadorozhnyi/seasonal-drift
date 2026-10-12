# MVP results

Clients: 20 (MT_001, MT_002, MT_003, MT_004, MT_005, MT_006, MT_007, MT_008, MT_009, MT_010, MT_011, MT_013, MT_014, MT_016, MT_017, MT_018, MT_019, MT_020, MT_021, MT_022). Seeds per client: 3.
Series length 2016 h, warm-up 672 h, change at point 1344, detection window 168 h.
Settings: `default` = textbook thresholds (KS p < 0.05, PSI > 0.1, River defaults); `calibrated` = thresholds chosen on separate control series so that every detector gives about 2 false alarms per 1000 points.

## Calibrated parameters

| detector    | variant   | parameter   |   default |   calibrated |
|:------------|:----------|:------------|----------:|-------------:|
| KS-1d       | raw       | threshold   |    0.2821 |       0.3642 |
| KS-1d       | resid     | threshold   |    0.2821 |       0.4476 |
| KS-1w       | raw       | threshold   |    0.1171 |       0.1027 |
| KS-1w       | resid     | threshold   |    0.1171 |       0.1756 |
| PSI-1d      | raw       | threshold   |    0.1    |       2.51   |
| PSI-1d      | resid     | threshold   |    0.1    |       3.172  |
| PSI-1w      | raw       | threshold   |    0.1    |       0.1181 |
| PSI-1w      | resid     | threshold   |    0.1    |       0.2416 |
| ADWIN       | raw       | delta       |    0.002  |       0.05   |
| ADWIN       | resid     | delta       |    0.002  |       0.05   |
| PageHinkley | raw       | threshold   |   50      |      50      |
| PageHinkley | resid     | threshold   |   50      |      50      |
| KSWIN       | raw       | alpha       |    0.005  |       0.0001 |
| KSWIN       | resid     | alpha       |    0.005  |       1e-05  |

# Setting: default

## False alarms on control series without changes (alarms per 1000 points, mean over series)

| detector    |   raw |   resid |
|:------------|------:|--------:|
| ADWIN       |  0.32 |    0.48 |
| KS-1d       |  5.67 |   13.75 |
| KS-1w       |  0.66 |   12    |
| KSWIN       |  4.75 |    6.14 |
| PSI-1d      | 40.85 |   41.57 |
| PSI-1w      |  2.79 |   18.4  |
| PageHinkley |  0.94 |    2    |

## Alarms on the real source series, autumn 2013, unlabelled (alarms per 1000 points)

| detector    |   raw |   resid |
|:------------|------:|--------:|
| ADWIN       |  1.6  |    2.6  |
| KS-1d       | 19.05 |   29.13 |
| KS-1w       | 32.44 |   34.56 |
| KSWIN       |  4.91 |    6.21 |
| PSI-1d      | 41.52 |   41.29 |
| PSI-1w      | 35.19 |   36.16 |
| PageHinkley |  3.27 |    4.13 |

## Change type: level_shift

Share of series where the change was detected within one week (columns: variant, magnitude in sigma):

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |           0.07 |           0.28 |           0.68 |           0.95 |             0.7  |             0.95 |             0.97 |             0.97 |
| KS-1d       |           0.7  |           0.82 |           0.93 |           1    |             1    |             1    |             1    |             1    |
| KS-1w       |           0.48 |           0.9  |           1    |           1    |             0.98 |             1    |             1    |             1    |
| KSWIN       |           0.68 |           0.73 |           0.77 |           0.83 |             0.93 |             0.93 |             0.92 |             0.93 |
| PSI-1d      |           1    |           1    |           1    |           1    |             1    |             1    |             1    |             1    |
| PSI-1w      |           0.75 |           0.98 |           1    |           1    |             1    |             1    |             1    |             1    |
| PageHinkley |           0.45 |           0.83 |           0.9  |           0.92 |             0.82 |             0.97 |             1    |             1    |

Median delay in hours among detected series:

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |            159 |            127 |             95 |             63 |               95 |               63 |               31 |               31 |
| KS-1d       |             95 |             47 |             23 |             23 |               23 |               23 |               23 |               23 |
| KS-1w       |            119 |             95 |             71 |             47 |               71 |               47 |               23 |               23 |
| KSWIN       |             84 |             78 |             36 |             38 |               59 |               36 |               26 |               26 |
| PSI-1d      |             23 |             23 |             23 |             23 |               23 |               23 |               23 |               23 |
| PSI-1w      |            119 |             95 |             47 |             47 |               47 |               23 |               23 |               23 |
| PageHinkley |             97 |            114 |             63 |             42 |               86 |               46 |               20 |               14 |

## Change type: trend_ramp

Share of series where the change was detected within one week (columns: variant, magnitude in sigma):

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |           0.05 |           0.05 |           0.25 |           0.47 |             0.45 |             0.83 |                1 |                1 |
| KS-1d       |           0.63 |           0.75 |           0.9  |           0.98 |             0.98 |             1    |                1 |                1 |
| KS-1w       |           0.12 |           0.43 |           0.87 |           0.97 |             0.95 |             1    |                1 |                1 |
| KSWIN       |           0.77 |           0.8  |           0.82 |           0.83 |             0.93 |             0.98 |                1 |                1 |
| PSI-1d      |           1    |           1    |           1    |           1    |             1    |             1    |                1 |                1 |
| PSI-1w      |           0.42 |           0.67 |           0.9  |           1    |             0.98 |             1    |                1 |                1 |
| PageHinkley |           0.25 |           0.42 |           0.82 |           0.92 |             0.7  |             0.92 |                1 |                1 |

Median delay in hours among detected series:

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |            159 |            159 |            159 |            127 |              159 |              127 |               95 |               95 |
| KS-1d       |            143 |            143 |             95 |             95 |               47 |               47 |               47 |               47 |
| KS-1w       |            143 |            143 |            143 |            119 |               71 |               71 |               71 |               71 |
| KSWIN       |             93 |             93 |             85 |             85 |               74 |               70 |               64 |               56 |
| PSI-1d      |             23 |             23 |             23 |             23 |               23 |               23 |               23 |               23 |
| PSI-1w      |             71 |             95 |            119 |            119 |               47 |               47 |               47 |               47 |
| PageHinkley |            139 |            117 |            135 |            115 |              127 |              104 |               84 |               72 |

# Setting: calibrated

## False alarms on control series without changes (alarms per 1000 points, mean over series)

| detector    |   raw |   resid |
|:------------|------:|--------:|
| ADWIN       |  1.53 |    2.13 |
| KS-1d       |  2.16 |    2.58 |
| KS-1w       |  1.5  |    1.85 |
| KSWIN       |  2.13 |    1.7  |
| PSI-1d      |  2.01 |    1.96 |
| PSI-1w      |  1.53 |    1.46 |
| PageHinkley |  0.94 |    2    |

## Alarms on the real source series, autumn 2013, unlabelled (alarms per 1000 points)

| detector    |   raw |   resid |
|:------------|------:|--------:|
| ADWIN       |  3.09 |    3.94 |
| KS-1d       | 11.16 |   15.66 |
| KS-1w       | 33.67 |   30.32 |
| KSWIN       |  2.42 |    1.9  |
| PSI-1d      | 11.16 |   13.36 |
| PSI-1w      | 34.3  |   30.62 |
| PageHinkley |  3.27 |    4.13 |

## Change type: level_shift

Share of series where the change was detected within one week (columns: variant, magnitude in sigma):

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |           0.25 |           0.5  |           0.93 |           0.95 |             0.75 |             0.9  |             0.92 |             0.92 |
| KS-1d       |           0.37 |           0.52 |           0.77 |           0.93 |             0.88 |             1    |             1    |             1    |
| KS-1w       |           0.58 |           0.95 |           1    |           1    |             0.9  |             1    |             1    |             1    |
| KSWIN       |           0.35 |           0.4  |           0.48 |           0.58 |             0.35 |             0.58 |             0.88 |             0.88 |
| PSI-1d      |           0.33 |           0.55 |           0.9  |           0.93 |             0.72 |             1    |             1    |             1    |
| PSI-1w      |           0.6  |           0.97 |           1    |           1    |             0.87 |             1    |             1    |             1    |
| PageHinkley |           0.45 |           0.83 |           0.9  |           0.92 |             0.82 |             0.97 |             1    |             1    |

Median delay in hours among detected series:

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |            159 |             95 |             95 |             63 |               63 |               31 |               31 |               31 |
| KS-1d       |            107 |             47 |             23 |             23 |               71 |               23 |               23 |               23 |
| KS-1w       |            119 |             95 |             71 |             47 |              107 |               71 |               47 |               47 |
| KSWIN       |             81 |             54 |             39 |             24 |               34 |               28 |               21 |               19 |
| PSI-1d      |            119 |             95 |             47 |             23 |               71 |               23 |               23 |               23 |
| PSI-1w      |            119 |             95 |             71 |             47 |              119 |               95 |               47 |               47 |
| PageHinkley |             97 |            114 |             63 |             42 |               86 |               46 |               20 |               14 |

## Change type: trend_ramp

Share of series where the change was detected within one week (columns: variant, magnitude in sigma):

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |           0.18 |           0.23 |           0.52 |           0.78 |             0.68 |             0.93 |             0.98 |             1    |
| KS-1d       |           0.37 |           0.37 |           0.62 |           0.77 |             0.68 |             0.98 |             1    |             1    |
| KS-1w       |           0.23 |           0.53 |           0.92 |           1    |             0.52 |             0.9  |             1    |             1    |
| KSWIN       |           0.33 |           0.35 |           0.5  |           0.57 |             0.37 |             0.55 |             0.9  |             0.98 |
| PSI-1d      |           0.28 |           0.45 |           0.72 |           0.87 |             0.53 |             0.9  |             1    |             1    |
| PSI-1w      |           0.28 |           0.55 |           0.88 |           0.98 |             0.38 |             0.83 |             1    |             1    |
| PageHinkley |           0.25 |           0.42 |           0.82 |           0.92 |             0.7  |             0.92 |             1    |             1    |

Median delay in hours among detected series:

| detector    |   ('raw', 0.5) |   ('raw', 1.0) |   ('raw', 2.0) |   ('raw', 3.0) |   ('resid', 0.5) |   ('resid', 1.0) |   ('resid', 2.0) |   ('resid', 3.0) |
|:------------|---------------:|---------------:|---------------:|---------------:|-----------------:|-----------------:|-----------------:|-----------------:|
| ADWIN       |            159 |            159 |            159 |            127 |              127 |               95 |               95 |               63 |
| KS-1d       |            167 |            143 |            119 |             95 |               95 |               95 |               95 |               71 |
| KS-1w       |            107 |            143 |            119 |            107 |              119 |              143 |               95 |               95 |
| KSWIN       |            142 |             96 |             92 |             86 |               92 |               96 |               92 |               74 |
| PSI-1d      |            143 |            143 |            119 |             95 |              119 |              119 |               95 |               71 |
| PSI-1w      |            143 |            143 |            119 |            119 |              143 |              143 |              119 |               95 |
| PageHinkley |            139 |            117 |            135 |            115 |              127 |              104 |               84 |               72 |
