# County Violent Crime (Waves 1–3) → Depressive Symptoms (Waves 1–5)

Analysis pipeline for lagged associations between county violent crime and
depressive symptoms in Add Health. The design, estimands, and every model are
pre-specified in [`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) —
read that first; this file covers only mechanics.

**Core design decision:** Add Health inter-wave gaps are unequal (≈1, 5.5, 6.5,
and 15 years), so "one-wave-lag" coefficients pooled across pairs would average
incompatible estimands. Each exposure→outcome pair is estimated separately
(L1: W1→W2, L2: W2→W3, L3: W3→W4, L4: W3→W5), with cumulative-exposure models
(L5) and a within-person fixed-effects contemporaneous model (C1) as complements.

## Data protection

Add Health restricted-use data (including county FIPS linkages) must **never**
be committed. `input/` and `output/` are gitignored. Before releasing any output
table, confirm it satisfies your Add Health security plan (no geographic
identifiers, no cells with n < 5). `00_config.R` blocks FIPS columns from
written tables, but that check is a backstop, not a substitute for review.

## Requirements

R ≥ 4.3 with `survey`, `mitools`, `mice`, `lme4`
(Debian/Ubuntu: `apt-get install r-cran-survey r-cran-mice r-cran-lme4`).

## Verify the pipeline (no real data needed)

```sh
cd analysis/crime-depression-lags
CRIMEDEP_MI_M=5 Rscript R/run_all.R --simulate
```

This generates synthetic Add Health–like inputs with a known lagged effect
(0.05 SD), runs every step, and fails loudly if the primary estimands L1–L3 do
not recover the truth. It is a smoke test of the full pipeline (merges, lag
construction, weighting, MI, SEs) — not a simulation study.

## Run on real data

1. Prepare the three input files below from restricted-use Add Health sources
   (do this inside your secure data environment).
2. `Rscript R/run_all.R` (uses m = 20 imputations by default; set
   `CRIMEDEP_MI_M=0` for a complete-case-only run).
3. Outputs land in `output/`: `table_2_main_results.csv`,
   `table_3_sensitivity.csv`, `table_S1`–`S3` descriptives/attrition.

## Input schemas

The pipeline consumes *prepared* files, never raw Add Health files. Scale
construction happens in your data prep, per the SAP.

### `input/persons.csv` — one row per respondent

| column | description |
|---|---|
| `aid` | respondent ID |
| `psu` | school (Add Health PSU) |
| `stratum` | region stratum |
| `sex_female` | 0/1 |
| `race_eth` | `NHWhite` / `NHBlack` / `Hispanic` / `NHAsian` / `NHOther` |
| `parent_educ` | `lt_hs` / `hs` / `some_college` / `college_plus` |
| `log_hh_income_w1` | log W1 household income (missing allowed; MI handles it) |
| `family_structure_w1` | `two_bio` / `other` |

### `input/person_waves.csv` — one row per completed interview

| column | description |
|---|---|
| `aid`, `wave` | wave 1–5; row present only if interviewed |
| `age` | age at interview |
| `cesd_full` | mean item score (0–3) of the wave's **full** CES-D set, ≥80% items answered, else NA. Verify item names per wave against restricted-use codebooks (e.g., W1 `H1FS1–H1FS19`) |
| `cesd_common` | same, restricted to the item subset common to all five waves |
| `county_fips` | county of residence at interview |
| `weight` | wave-specific grand sample weight (choose per Chen & Harris Add Health weighting guidance; NA if no valid weight) |

### `input/county_crime.csv` — one row per county × wave (waves 1–3)

| column | description |
|---|---|
| `county_fips`, `wave` | |
| `violent_rate` | violent crimes per 100,000 (state provenance in the manuscript: UCR county files / CDR cleaned / Add Health contextual) |
| `county_poverty` | proportion in poverty |
| `urbanicity` | `rural` / `suburban` / `urban` |
| `log_pop_density` | log persons per sq. mile |
| `coverage_pct` | optional: % population covered by reporting agencies; enables sensitivity S5 (Maltz–Targonski county-UCR quality problem) |

## Scripts

| script | role |
|---|---|
| `R/00_config.R` | paths, estimand definitions, MI settings, disclosure backstop |
| `R/01_build_panel.R` | exposure/outcome standardization, lag-pair datasets |
| `R/02_descriptives.R` | analytic samples, exposure distributions, attrition |
| `R/03_models.R` | primary (L1–L3), secondary (L4–L5), fixed-effects (C1); MI + Rubin's rules; BH q-values |
| `R/04_sensitivity.R` | S1–S7 per the SAP |
| `R/99_simulate_inputs.R` / `R/98_validate_recovery.R` | synthetic-data pipeline verification |
| `R/run_all.R` | orchestrates everything |

## Before submission — items code cannot do for you

- Verify CES-D item names/counts per wave against the restricted-use codebooks;
  update data prep and the SAP if they differ from assumptions.
- Choose and document the exact weight variable per estimand (outcome-wave grand
  sample weights are the default here) against current Add Health guidance.
- Document crime data provenance and county-linkage procedure.
- Date-stamp the SAP before touching real data; report any deviation as such.
- STROBE checklist and sample flow diagram per estimand.
