# Counterfactual risk prediction of weapon-involvement prevention (LMTP + ML)

Code for the flagship ML paper: *If weapon involvement after Wave III had been
prevented or reduced, how different would depressive symptoms (primary) and
systolic blood pressure (secondary) be at later waves?*

Estimand family: **longitudinal modified treatment policies (LMTPs)** with
double-robust estimation and a super-learner ensemble (`lmtp`). Policies are
deterministic "set involvement to 0" at chosen waves:

| policy | meaning |
|---|---|
| `prevent_all` | no involvement at any treatment wave of the design |
| `prevent_first` | prevent only at the first treatment wave (early) |
| `prevent_last` | prevent only at the last treatment wave (late) |

The contrast `prevent_first - prevent_last` is the **timing** question of the
dissertation expressed as a policy contrast.

## Layout
```
R/00_config.R              analysis choices (designs, policies, timing assumptions)
R/utils.R                  helpers + check_time_ordering() guard
R/01_simulate_cohort.R     synthetic cohort with a known causal truth
R/02_build_design_data.R   canonical wide file -> LMTP structure; censoring; eligibility
R/03_fit_lmtp.R            PRIMARY estimator: lmtp_tmle (sdr as sensitivity)
R/04_gcomp_validation.R    independent plug-in ICE g-computation (validation / cross-check)
R/05_fe_benchmark.R        within-person benchmark to triangulate with Papers 2-4
R/06_diagnostics.R         positivity table; lmtp API smoke test
R/07_harmonize_addhealth.R coding rules + raw-variable map (TODOs to fill)
R/08_results_tables.R      tidy CSV outputs
run_tests.R                unit tests (no lmtp needed)
run_simulation_check.R     recovers a known policy effect from simulated data with dropout
run_real_data.R            real-data driver (run inside the approved environment)
data/DATA_DICTIONARY_template.csv
```

## Design choices you must be able to defend
1. **Ordering inside a wave.** Past-year involvement and past-week symptoms are
   reported at the same interview, so their order is unknown. `timing = "post"`
   treats same-wave symptoms/BMI/BP as measured *after* exposure (they are never
   confounders of that wave's exposure). `timing = "pre"` treats them as
   *before* (adjusts for a possible mediator). Report both; they bracket the
   problem. `check_time_ordering()` stops the run if any covariate violates the
   chosen assumption.
2. **Time blocks.** `baseline -> L_k (waves <= w-1, plus area context/age at w) -> A_k -> C_k`.
   County crime exists only for Waves I-III and is never carried forward.
3. **Censoring.** `C_k = 1` if the next block (A_{k+1}, L_{k+1}) or the outcome is
   observed; item non-response is treated as censoring (MAR given history).
   In `post` mode the censoring model cannot condition on same-wave symptoms.
4. **Eligibility.** Complete baseline, first block and first exposure. For the
   Wave III-IV design that means observed at Waves II-III; for the BP designs,
   observed at Wave IV. Targets are the effects in these eligible populations.
5. **Identification.** Needs no unmeasured time-varying confounding given the
   measured history, positivity, and correct timing. Results are estimates under
   those assumptions, not proven causal effects.

## What was tested here (and what was not)
Tested in the sandbox where this was prepared (R 4.3.3):
* all scripts parse; `run_tests.R` passes (simulator, time-ordering guard,
  design builder for all 3 designs x 2 timing modes, positivity table, FE
  benchmark, coding rules);
* `run_simulation_check.R`: see `output/sim_check_*.log` for recovery of the known
  policy effect by the independent g-computation estimator under dropout.

**NOT tested here:** `R/03_fit_lmtp.R` (the `lmtp` package could not be installed:
CRAN was unreachable). It follows the package's documented interface, with
version-dependent learner names handled in `default_learners()`. Run
`source("R/06_diagnostics.R"); check_lmtp_api()` first; it fails loudly if a
argument name or return field differs in your installed version
(`lmtp_contrast()` output fields in `.extract_contrast()` are the likeliest spot).

## Run order on your machine
```r
install.packages(c("lmtp", "data.table", "glmnet", "ranger"))  # + SuperLearner or mlr3superlearner per lmtp version
setwd("lmtp_paper")
source("run_tests.R")                                     # fast
source("R/06_diagnostics.R"); check_lmtp_api()            # confirms lmtp interface
# fill R/07_harmonize_addhealth.R TODOs -> data/analysis_wide.csv
source("run_real_data.R")
```

## Power note (read before running)
Under effect sizes calibrated to the papers (past-year victimization ~0.20 SD,
each earlier report ~0.08 SD, no lingering perpetration effect), preventing
involvement at Waves III-IV changes Wave V symptoms by only a few hundredths of
a point in the simulator. Expect wide intervals: run
`Rscript run_simulation_check.R 3 5000 calibrated` and
`sim_truth()` at your sample size before preregistering the primary contrast.
For BP, only 183 (IV->V) and 41 (V->VI) respondents changed history in your data.

## Using your existing session objects (added after reviewing your scripts)
`R/07a_adapter_from_panel.R :: build_wide_from_panel(panel, biomarkers_panel_long_w456, sib_prof)`
converts the long objects already in your RStudio session into the canonical wide file, reusing
the variables your Papers 2-4 built (no re-coding of raw Add Health items). `run_real_data.R`
calls it automatically when those objects exist.

Mapping used (edit `ADAPTER_MAP` if wrong). **CHECK** = not verifiable from the code photographed:

| pipeline | your column | note |
|---|---|---|
| `vic_w`, `perp_w`, `wit_w` | `weapon_victimization`, `weapon_violence`, `weapon_witnessing` | `> 0` -> 1, as in your `vict`/`perp` |
| `dep_w` | `depression` | CHECK: the harmonised 0-9 sum, not a z-score |
| `nbhd_w` (waves 1-5) | `neigh_conc_disadv_raw` | from `B1..B5NRBHDDISAD` |
| `ccrime_w` (waves 1-3) | `cty_violent_rate_log` | CHECK; your county model also restricts to non-movers |
| `pov_w` | `poverty_z` | CHECK: available at all waves? higher = more poverty |
| `sbp_w`, `bmi_w`, `med_w` | biomarker panel `sbp`, `bmi`, `med_bp` | waves 4-6 |
| `cumv_w`, `cump_w` | built from the above | same definition as `make_history()`: cumsum(current, NA->0) |
| `famconn_base`, `schconn_base`, `nbcoh_base` | `*_baseline` columns | baseline social resources |
| `fam` | `sib_prof$FAMID` | clustered folds |
| `female`, `minority` | `gender`, `race` | CHECK coding (`as_female`, `as_minority`) |

Not carried over: self-esteem (waves 1-3 only), religion, `nonmover`. Add them in the adapter if wanted.
Note: `timing = "pre"` makes same-wave SBP/BMI/medication required covariates, which drops about
30% of the BP-design sample in the simulation (those without a BP measure); report `post` as primary.
