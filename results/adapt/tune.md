# Base model validation (static model, MASE)

|                                                    |   mase |   mase_naive |   series |
|:---------------------------------------------------|-------:|-------------:|---------:|
| ('entsoe', 'A: 200 rounds, lr 0.05, 31 leaves')    |  0.486 |        0.806 |        8 |
| ('entsoe', 'B: 400 rounds, lr 0.05, 63 leaves')    |  0.481 |        0.806 |        8 |
| ('entsoe', 'C: 300 rounds, lr 0.03, 15 leaves')    |  0.512 |        0.806 |        8 |
| ('entsoe', 'D: 200 rounds, lr 0.10, 31 leaves')    |  0.498 |        0.806 |        8 |
| ('synthetic', 'A: 200 rounds, lr 0.05, 31 leaves') |  0.945 |        1.04  |       40 |
| ('synthetic', 'B: 400 rounds, lr 0.05, 63 leaves') |  0.967 |        1.04  |       40 |
| ('synthetic', 'C: 300 rounds, lr 0.03, 15 leaves') |  0.933 |        1.04  |       40 |
| ('synthetic', 'D: 200 rounds, lr 0.10, 31 leaves') |  0.973 |        1.04  |       40 |
