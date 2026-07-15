# Statistical Analysis Plan

## County Violent Crime (Waves 1–3) and Depressive Symptoms (Waves 1–5)

**Status:** Pre-specified analysis plan. Finalize and date this document *before* running
any model on real data. Deviations must be reported as such in the manuscript.

**Data:** National Longitudinal Study of Adolescent to Adult Health (Add Health),
restricted-use in-home interview files (Waves I–V) linked to restricted-use geographic
identifiers (county FIPS at each interview) and county-level violent crime rates
available for Waves I–III.

---

## 1. Rationale and positioning in the literature

Neighborhood crime shows small but consistent associations with depression in the
pooled literature (Baranyi et al., 2021, *Social Science & Medicine*: pooled r ≈ 0.04
for depression across 63 studies). Two features of that literature motivate this
design:

1. **Objective (recorded) crime shows weaker associations than perceived crime**, and
   associations attenuate after adjustment for area deprivation. Small estimates are
   therefore the *expected* result, not a failed analysis, and the analysis is
   framed and powered accordingly.
2. **Temporal ordering is the main gap.** Most studies are cross-sectional. Add Health
   permits exposure measured strictly before the outcome, with adjustment for prior
   depressive symptoms.

Because Add Health inter-wave intervals are radically unequal (W1→W2 ≈ 1 year,
W2→W3 ≈ 5.5 years, W3→W4 ≈ 6.5 years, W3→W5 ≈ 15 years), **we do not pool "one-wave
lags" into a single coefficient.** A pooled lag-1 coefficient would average a 1-year
effect with 5–6-year effects — different estimands. Each exposure→outcome wave pair is
estimated separately, and elapsed time is treated as a substantive dimension
(developmental timing), not a nuisance label.

## 2. Hypotheses

- **H1 (short/medium lag):** Higher county violent crime at wave *t* is associated
  with higher depressive symptoms at wave *t+1*, adjusting for symptoms at wave *t*
  (estimands L1–L3 below).
- **H2 (adolescent exposure, adult outcome):** Cumulative adolescent exposure
  (mean of W1–W3 standardized crime) is associated with adult depressive symptoms at
  W4 and W5, adjusting for W1 symptoms.
- **H3 (decay):** Associations weaken as elapsed time between exposure and outcome
  increases (descriptive comparison of L1–L4; formal test in sensitivity model S1).

All hypotheses are two-sided. Given the meta-analytic prior (r ≈ 0.04) and county-level
exposure misclassification, anticipated standardized effects are ≤ 0.05 SD; null results
are informative and will be published regardless of direction or significance.

## 3. Measures

### 3.1 Outcome: depressive symptoms (CES-D, Waves 1–5)

The CES-D item set differs by wave (19 items at W1/W2; ~9–10 at W3/W4; 5 at W5).
**Verify exact item names against the restricted-use codebooks before data prep**
(e.g., W1 feelings scale `H1FS1–H1FS19`; confirm W2–W5 equivalents).

- **Primary outcome:** wave-specific mean item score (0–3) over the wave's full CES-D
  item set, requiring ≥ 80% items answered, **z-standardized within outcome wave** in
  the analytic sample. Coefficients are therefore in outcome-wave SD units. Because
  every model uses a single outcome wave, within-wave standardization does not distort
  cross-wave comparisons of standardized coefficients.
- **Sensitivity outcome (S2):** mean of the item subset common to all five waves
  (the W5 negative-affect items), identically constructed, to address measurement
  non-invariance across wave-specific versions.

CES-D scores are symptom counts, not diagnoses; the manuscript will say "depressive
symptoms," never "depression diagnosis."

### 3.2 Exposure: county violent crime rate (Waves 1–3)

Violent crime rate per 100,000 population for the respondent's county of residence at
the interview date of the exposure wave. Transformation: `ln(rate + 1)`, then
z-standardized against the pooled W1–W3 person-wave distribution of the analytic
sample (one fixed mean/SD pair, so 1 unit = 1 SD of adolescent exposure in every
model).

**Data-quality caution (must be addressed in the manuscript):** county-level UCR
aggregates suffer from missing-agency imputation problems (Maltz & Targonski, 2002,
*J. Quantitative Criminology*). If the crime source provides agency-coverage
information, sensitivity S5 re-estimates primary models excluding county-waves with
< 90% population coverage. State the crime data provenance (UCR county files, CDR
cleaned version, or Add Health contextual files) explicitly.

### 3.3 Covariates

Measured at or before the exposure wave; all specified a priori:

- **Individual:** age at outcome interview, sex, race/ethnicity, parental education,
  log household income (W1), family structure (W1).
- **County (exposure wave):** poverty rate (deprivation proxy — required, per the
  moderator finding in Baranyi et al. that deprivation adjustment attenuates crime
  effects; omitting it would inflate estimates), urbanicity, population density.
- **Design:** region stratum; school (PSU) enters through the survey design, not as a
  covariate.

Prior depressive symptoms (exposure-wave CES-D z) are included in every lagged model:
this is the key defense against reverse causation via selective residence in
higher-crime counties.

## 4. Estimands and models

### 4.1 Primary: lag-pair-specific conditional-change models

For each pair, survey-weighted linear regression (design-based SEs; strata = region,
PSU = school, weight = outcome-wave grand sample weight):

```
CESD_z(t+1) = b0 + b1*CRIME_z(t) + b2*CESD_z(t) + covariates + e
```

| Estimand | Exposure | Outcome | Elapsed time |
|----------|----------|---------|--------------|
| L1 | W1 crime | W2 CES-D | ≈ 1 year |
| L2 | W2 crime | W3 CES-D | ≈ 5.5 years |
| L3 | W3 crime | W4 CES-D | ≈ 6.5 years |

`b1` per estimand is the primary quantity: SD change in depressive symptoms per 1 SD
ln county violent crime, conditional on prior symptoms.

### 4.2 Secondary

- **L4:** W3 crime → W5 CES-D | W3 CES-D (≈ 15 years).
- **L5a/L5b:** cumulative adolescent exposure (person mean of W1–W3 CRIME_z) → W4 /
  W5 CES-D, adjusting for W1 CES-D and covariates.

### 4.3 Contemporaneous within-person model (C1)

Person fixed-effects model on the W1–W3 person-wave panel (persons with ≥ 2 waves):

```
CESD_z(it) = a_i + g1*CRIME_z(it) + g2*AGE(it) + g3*CTYPOV(it) + wave dummies + e_it
```

Identification comes from within-person change (movers and within-county temporal
change in crime), removing all time-invariant confounding — the strongest available
answer to selection. Estimated unweighted (within estimator), cluster-robust SEs by
person; report as a design-complementary estimate, not pooled with L1–L4.

### 4.4 Inference and multiplicity

- Report point estimates, 95% CIs, and exact p-values for every pre-specified model.
  No results suppressed; no model added post hoc without labeling it exploratory.
- Three primary estimands (L1–L3): report unadjusted p-values as primary, with
  Benjamini–Hochberg q-values across L1–L4 as supplementary.
- Standardized coefficients are the effect-size metric; compare against the
  meta-analytic benchmark (r ≈ 0.04) in the discussion.

## 5. Missing data and attrition

- **Primary:** multiple imputation by chained equations (m = 20) within each
  lag-pair's eligible sample (respondents interviewed at both waves of the pair with
  valid outcome-wave weight), imputing item-missing covariates, exposure, and baseline
  CES-D. Outcome imputed but MI-then-delete (imputed outcomes excluded from analysis).
  Pooling by Rubin's rules with design-based variance (mitools::MIcombine).
- **Sensitivity S3:** complete-case estimates alongside MI.
- Attrition table: baseline (exposure-wave) characteristics of retained vs lost per
  pair. Outcome-wave grand sample weights incorporate Add Health's nonresponse
  adjustments; residual selective attrition is a stated limitation.

## 6. Sensitivity analyses (all pre-specified)

| ID | Analysis | Purpose |
|----|----------|---------|
| S1 | Pooled lag model with elapsed-time interaction (`CRIME_z × years`) across L1–L4 person-pairs, clustered by person | Formal H3 decay test |
| S2 | Common-item CES-D outcome in L1–L4 | Measurement non-invariance |
| S3 | Complete-case versions of L1–L4 | MI robustness |
| S4 | L1–L3 restricted to respondents in the same county at exposure and outcome waves; plus mover-indicator adjustment in full sample | Residential mobility / exposure misclassification during the lag |
| S5 | Exclude county-waves with < 90% UCR agency coverage (if coverage data available) | Maltz–Targonski county-UCR quality problem |
| S6 | County random-intercept mixed model (unweighted) for L1–L3 | Exposure-level clustering beyond school PSU |
| S7 | L1–L3 without county poverty | Bounding: shows how much deprivation adjustment moves the estimate |

## 7. Power note

With n ≈ 9,000–13,000 per pair (typical Add Health pair retention), 80% power at
α = .05 for a standardized b1 detects ≈ 0.025–0.03 SD before design-effect
inflation; with design effects of ~2, minimal detectable effects are ≈ 0.04 SD —
i.e., the analysis is powered near the meta-analytic expectation. Precision, not
significance, is the reporting emphasis.

## 8. Known limitations (to be stated, not discovered by reviewers)

1. County is a coarse proxy for neighborhood; exposure misclassification biases
   toward the null. This is an *exposure-resolution* limitation, not a reason to
   reinterpret null results as absence of neighborhood effects.
2. County-level UCR data quality (Maltz & Targonski, 2002).
3. CES-D versions differ across waves (addressed by S2, but 5 common items is a
   floor, not a fix).
4. W4/W5 outcomes are adult outcomes; L3–L5 estimate adolescent-exposure →
   adult-outcome developmental effects and must not be described as contemporaneous
   neighborhood effects.
5. No exposure measured at W4/W5, so adult contemporaneous context cannot be
   adjusted; unmeasured time-varying confounding remains possible in L3–L5.
6. Observational design; language throughout: "associated with," never "caused."

## 9. Reporting standards

STROBE checklist; flow diagram of analytic samples per estimand; all code released
(this repository); crime data provenance and county-linkage procedure documented;
Add Health security plan compliance (no county identifiers or cell sizes < 5 in any
released output).
