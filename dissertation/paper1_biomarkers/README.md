# Paper 1 (Biomarker Extension) — Analysis Plan and Code

This module implements a biomarker-outcome companion to Paper 1 of the dissertation
*"Safe Streets, Healthy Minds"* (Abbas, Rutgers–Camden, Prevention Science). Paper 1
as proposed tests whether within-person changes in neighborhood violent crime predict
within-person changes in **depressive symptoms** across Add Health Waves I–V. This
module tests the parallel hypothesis for **biological embedding**: whether
adolescent/young-adult exposure to neighborhood violent crime and self-reported
violence/victimization predicts **allostatic load biomarkers** collected later in
adulthood.

It lives outside `backend/` and `frontend/` because those directories are the
VICINITY living-evidence-registry web app (a separate project on this repo) and share
no code or data with this analysis.

## Restricted data notice

Add Health is restricted-use data. Per the dissertation's Ethics section, all analysis
must run inside the Add Health secure environment, and no person-, school-, or
neighborhood-identifiable output may leave it. **This repository does not and must
not contain any Add Health extract.** The scripts here expect you to point
`config$panel_path` (see `R/00_config.R`) at a local file inside your secure session;
nothing is read from or written to this git repo except code, and `output/` is
git-ignored (see below) so accidental result exports don't get committed.

## What the panel screenshot tells us

Your `names(panel)` dump shows three variable families relevant here:

1. **Contextual county violent crime** (`violent_rate`, `violent_rate_log`,
   `violent_rate_lag1`, `violent_interwave_avg/dose/log`, `violent_cumulative`,
   `violent_cum_log/dose`) — these are the Paper-1 exposure variables built from
   county-level crime linkage. Your message says this linkage is only usable through
   **Wave III**, which the code treats as a configurable cutoff
   (`config$crime_wave_cutoff <- 3`).
2. **Self-reported violence exposure / victimization**, cumulative through Wave V
   (`violent_exp_total_cum`, `violent_exp_total_cum_log`, `violent_flow_early/mid/
   late/young_adult`) — treated as a second, complementary exposure with cutoff
   `config$victimization_wave_cutoff <- 5`.
3. **Biomarkers**, collected at whichever waves your data has them (Wave IV and
   Wave V per Add Health's actual biomarker collections; your message also flags
   Wave VI, so the code auto-detects rather than hardcoding): `crp`, `il6`, `glucose`,
   `hbalc` (HbA1c), `tg`, `tc`, `hdl`, `non_hdl`, `sbp`, `dbp`, `bmi`, `waist`, their
   `z_*` standardized versions, and ten `al_risk_*` clinical-risk flags (CRP, IL-6,
   glucose, HbA1c, triglycerides, non-HDL, low HDL, SBP, DBP, BMI) that make up a
   standard Add Health allostatic-load battery.

**Assumptions I'm making that you should confirm or correct:**

- `wave` is a numeric 1–6 wave indicator in a long (person-wave) panel, keyed by `aid`.
- A biomarker wave is any wave with non-missing `crp`/`il6`/`glucose` etc. — the code
  detects this from the data rather than assuming it's exactly Wave IV/V.
- There is no explicit `peer_risk` variable in the visible variable list (it was cut
  off in the photo, or not yet built). Peer risk is treated as **optional**: models
  run if the column exists, and are skipped with a warning otherwise.
- `family_connection`, `nb_cohesion_baseline`, `school_connect_baseline/avg`,
  `religion_attend`, and `neigh_conc_disadv_z`/`poverty_z` are the moderators pulled
  in for Hypotheses 3a/3c-analogues.
- Sibling/twin fixed effects require a family-linkage id. None is visible in the
  screenshot (Add Health typically supplies one in a separate roster file, e.g.
  a household/family id). The code looks for `famid`, `family_id`, or `hhid` and
  skips the sibling-FE robustness check with a warning if none is found — **you'll
  need to merge that id in before this check will run.**

If any of these assumptions are wrong, the scripts fail loudly (with a clear
"variable not found" message) rather than silently using the wrong column — see
`R/utils_checks.R`.

## Why the design differs from the CES-D Paper 1

CES-D is measured at every wave (I–V), so Paper 1 can fit a genuine individual
fixed-effects model with many within-person observations. Biomarkers are only
measured 2–3 times, and only in adulthood, long after most of the adolescent
crime/violence exposure accrued. That changes what "within-person" can mean here.
The code therefore fits **two complementary models**, both grounded in the
dissertation's own identification strategy (fixed effects as the core, sibling
comparisons and alternative-form checks as robustness):

- **Model A — Cumulative-exposure model (cross-sectional at first biomarker wave).**
  Allostatic load at the respondent's first observed biomarker wave, regressed on
  cumulative adolescent county crime exposure (through the Wave-III cutoff) and
  cumulative violence/victimization exposure (through Wave V), plus baseline
  covariates. This is the direct biomarker analogue of the dissertation's Paper 2
  cumulative-exposure logic (since a true within-person contrast isn't available
  before any biomarkers exist), but reported as an anchor for Paper 1's substantive
  question ("does more exposure mean worse biology"). Robustness: family
  (sibling/twin) fixed effects where a family id is available, since that is the
  closest available substitute for removing shared time-invariant confounding when
  a true individual panel isn't possible pre-biomarker.

- **Model B — Within-person change model (the direct Paper-1 analogue).** For the
  subset of respondents with ≥2 biomarker waves, first-differences (equivalent to
  individual fixed effects when T=2) in allostatic load are regressed on the
  crime/violence exposure accrued in the corresponding inter-wave interval, exactly
  mirroring Paper 1's core specification, just applied to the adult biomarker window
  instead of the adolescent CES-D window. This is the model that lets you say
  "when this person's exposure rose between two adult waves, did their allostatic
  load rise too, net of their own baseline."

Both models are fit for (a) a summary allostatic-load score — a count of `al_risk_*`
flags in the high-risk range, and a z-score composite of the standardized biomarkers
— and (b) each biomarker individually, so you can see whether any single biomarker
(e.g., CRP, an inflammatory marker with the most theoretical support for a
stress-embedding pathway) is driving a composite result.

## Files

```
R/
  00_config.R            variable-name / cutoff configuration (edit this first)
  utils_checks.R          "does this column exist" guards; fail loudly, not silently
  utils_al_index.R        allostatic-load composite construction
  utils_exposure.R         cumulative exposure construction + standardization
  utils_stats.R            hand-rolled cluster-robust SEs, within (demeaning) FE,
                            tidy output — base R only, no packages required, with
                            optional fixest/plm/sandwich use if installed
  01_build_analytic_sample.R   builds bio_first (Model A) and bio_change (Model B)
  02_model_core.R         fits Model A and Model B for the composite AL outcomes
  03_model_by_biomarker.R  fits Model A and Model B separately for each biomarker
  04_model_moderation.R    interaction models: crime x family connection / school
                            connectedness / neighborhood disadvantage (+ peer risk
                            if present)
  05_model_robustness.R    Tier-1 checks: log vs. tertile crime, lag structures,
                            complete-case vs. available-case, race x gender x
                            poverty exploratory subgroup (H3d analogue)
  06_run_all.R             master script — source this
tests/
  test_synthetic.R          builds a fake panel with the same column names and
                            confirms every script runs end-to-end without error;
                            this is what stood in for real data during development,
                            since Add Health data cannot leave the secure enclave
output/                     git-ignored; tidy result tables land here when you run
                            06_run_all.R against your real panel
```

## Running this in your secure Add Health session

1. Load your constructed `panel` data frame (or point `config$panel_path` in
   `R/00_config.R` at an `.rds`/`.csv` inside the secure environment).
2. Open `R/00_config.R` and correct any variable names / cutoffs that don't match
   your actual build.
3. `source("R/06_run_all.R")`.
4. Inspect the printed run log for warnings about missing optional variables
   (peer risk, family id) before trusting the robustness checks that depend on them.

## What this code does *not* do

- It does not fabricate or assume any coefficient, p-value, or effect size — there
  is no real data in this repo to run it against, only a synthetic smoke test.
- It does not pick which biomarkers "should" show an effect. It reports all of them
  and flags multiple-comparison correction (Benjamini-Hochberg across the
  biomarker-specific models) so you don't over-interpret one significant biomarker
  out of a dozen.
- It does not silently substitute a different variable if the one it expects is
  missing.
