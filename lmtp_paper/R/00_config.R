# ------------------------------------------------------------------
# 00_config.R  --  all analysis choices live here (pre-register these)
# ------------------------------------------------------------------
# Canonical wide-data naming convention (one row per respondent):
#   <name>_<wave>, wave = 1..6  (I..VI)
#   vic_w   weapon victimization, past year (0/1)
#   perp_w  weapon perpetration, past year (0/1)
#   wit_w   witnessed shooting/stabbing, past year (0/1)
#   dep_w   3-item CES-D sum, 0-9, harmonised (Wave V rescored to 0-3 per item)
#   bmi_w   BMI (waves 3-6)           sbp_w  systolic BP (waves 4-6)
#   cdis_w, ccrime_w  county disadvantage / log violent crime (waves 1-3)
#   nbhd_w  neighbourhood disadvantage (waves 4-5)
#   age_w   age at interview
# Time-fixed: id, fam (family id for clustering), female, minority, ses, age1
# See data/DATA_DICTIONARY_template.csv

cfg <- list(
  seed = 20260101,

  # Exposure the policy acts on: "any" (victimization OR perpetration),
  # "vic", or "perp".  The other role stays in the confounder set.
  exposure = "any",

  # Within-wave ordering assumption for same-wave symptoms/BMI/BP:
  #   "post": same-wave outcomes are measured AFTER the past-year exposure
  #           (they are mediators / later confounders, never confounders of
  #           the same-wave exposure).
  #   "pre" : same-wave outcomes are treated as measured BEFORE it
  #           (reverse-causation bracket; adjusts for possible mediators).
  # Report both; they bracket the order-of-events uncertainty.
  timings = c("post", "pre"),

  # Designs: treatment waves, outcome. Outcome must be measured AFTER the
  # last treatment wave (checked by check_time_ordering()).
  designs = list(
    dep_III_IV = list(label = "Depressive symptoms at Wave V; involvement at Waves III-IV",
                      outcome = "dep_5", trt_waves = c(3, 4)),
    sbp_IV     = list(label = "Systolic BP at Wave V; involvement at Wave IV",
                      outcome = "sbp_5", trt_waves = 4),
    sbp_IV_V   = list(label = "Systolic BP at Wave VI; involvement at Waves IV-V",
                      outcome = "sbp_6", trt_waves = c(4, 5))
  ),

  # Policies: deterministic 'set to 0' at chosen treatment waves.
  #   prevent_all   : no involvement at any treatment wave of the design
  #   prevent_first : only at the first treatment wave   (early prevention)
  #   prevent_last  : only at the last treatment wave    (late prevention)
  # The early-vs-late contrast is the timing question of the dissertation.
  policy_names = c("prevent_all", "prevent_first", "prevent_last"),

  # lmtp settings
  folds = 5,
  k = Inf   # use full history; set to 1 for a Markov-1 sensitivity run
)

policy_waves <- function(design, policy) {
  tw <- design$trt_waves
  switch(policy,
         natural       = integer(0),
         prevent_all   = tw,
         prevent_first = tw[1],
         prevent_last  = tw[length(tw)],
         stop("unknown policy: ", policy))
}
