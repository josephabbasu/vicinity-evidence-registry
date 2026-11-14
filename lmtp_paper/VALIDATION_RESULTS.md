# Validation results (simulated data; R 4.3.3; independent g-computation estimator)

`Rscript run_simulation_check.R 3 5000 strong` -- 3 replicate cohorts, n = 5,000, informative dropout.
"Strong" parameters inflate effects so the code can be verified at modest n. They are NOT Add Health estimates.

| design | policy | estimate (mean) | SD across reps | truth | bias |
|---|---|---|---|---|---|
| dep_III_IV | prevent_all | -0.125 | 0.021 | -0.136 | +0.012 |
| dep_III_IV | prevent_first | -0.086 | 0.016 | -0.095 | +0.009 |
| dep_III_IV | prevent_last | -0.041 | 0.011 | -0.049 | +0.009 |
| sbp_IV | prevent_all | -0.444 | 0.067 | -0.482 | +0.038 |
| sbp_IV_V | prevent_all | -0.513 | 0.150 | -0.533 | +0.020 |
| sbp_IV_V | prevent_first | -0.294 | 0.122 | -0.276 | -0.018 |
| sbp_IV_V | prevent_last | -0.234 | 0.061 | -0.267 | +0.033 |

Natural-course mean (depressive symptoms, design dep_III_IV): ICE 1.473, complete-case 1.441, truth 1.488.

Reading: estimates track the truth; 8 of 9 biases attenuate toward zero (about 8-17% of the
effect), the expected shrinkage of a plug-in estimator with penalised/forest learners. The
doubly robust lmtp estimator is designed to reduce this; it could not be run here.
Only 3 replicates: SDs and biases are rough, coverage was not assessed.

## Realistic effect sizes (paper-calibrated parameters, truth from N = 100,000)
| design | policy | natural mean | true effect |
|---|---|---|---|
| dep_III_IV | prevent_all | 1.163 | -0.034 points (~0.02 SD) |
| dep_III_IV | prevent_first | 1.163 | -0.022 |
| dep_III_IV | prevent_last | 1.163 | -0.014 |
| sbp_IV | prevent_all | 117.5 | -0.19 mmHg |
| sbp_IV_V | prevent_all | 118.8 | -0.21 mmHg |
| sbp_IV_V | prevent_first / last | 118.8 | -0.11 / -0.10 mmHg |

At n = 5,000 the SD of the policy-effect estimate was about 0.02 points (strong run), so a true
effect of 0.03 points is roughly 1.5 SD: expect to need a much larger analytic sample or to report
wide intervals. Real BP identifying variation is smaller than in this simulator (183 and 41 additions).
