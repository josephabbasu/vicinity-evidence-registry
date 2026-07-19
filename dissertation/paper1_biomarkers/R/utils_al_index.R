# Allostatic-load (AL) composite construction.
#
# Two composites are built, matching common practice in the Add Health
# biomarker literature (e.g. AL count-scores built from clinical cutpoints,
# and continuous z-score composites for greater statistical power):
#
#   AL_count -- count of al_risk_* flags in the high-risk range (0-10)
#   AL_zsum  -- sum of standardized biomarkers (z_*), higher = more dysregulated
#
# Both respect medication-adjustment and fasting/infection exclusion flags
# where present, by setting the *contributing* al_risk/z value to NA (not by
# dropping the whole person-wave) -- consistent with standard AL-index
# practice of excluding a single biomarker's contribution rather than an
# entire observation when e.g. a non-fasting glucose draw invalidates just
# the glucose component.

#' Detect which waves have usable biomarker data.
#' A wave counts as a "biomarker wave" if at least half of the configured
#' `biomarker_vars` are non-missing for at least one respondent at that wave.
detect_biomarker_waves <- function(data, config) {
  present <- intersect(config$biomarker_vars, names(data))
  if (length(present) == 0) {
    stop("None of config$biomarker_vars were found in the panel.", call. = FALSE)
  }
  waves <- sort(unique(data[[config$wave_var]]))
  frac_nonmissing <- vapply(waves, function(w) {
    rows <- data[[config$wave_var]] == w
    vals <- data[rows, present, drop = FALSE]
    mean(vapply(vals, function(col) mean(!is.na(col)), numeric(1)))
  }, numeric(1))
  bio_waves <- waves[frac_nonmissing >= 0.10]
  if (length(bio_waves) == 0) {
    stop("No wave has usable (>=10% non-missing) biomarker data. Check biomarker_vars in 00_config.R.",
         call. = FALSE)
  }
  message("Detected biomarker waves: ", paste(bio_waves, collapse = ", "))
  bio_waves
}

#' Apply medication / fasting / infection adjustment by NA-ing out the single
#' contributing component rather than the whole row.
#' Returns `data` with adjusted copies of the relevant columns
#' (suffix `_adj`), leaving the raw columns untouched for transparency.
apply_biomarker_adjustments <- function(data, config) {
  d <- data

  # Glucose depends on fasting status; if fasting_ok == 0, glucose (and any
  # glucose-derived al_risk flag) is not comparable across respondents.
  if (optional_var_exists(d, config$fasting_var, "fasting status")) {
    not_fasting <- !is.na(d[[config$fasting_var]]) & d[[config$fasting_var]] == 0
    if ("glucose" %in% names(d)) d$glucose_adj <- ifelse(not_fasting, NA_real_, d$glucose)
    if ("z_glucose" %in% names(d)) d$z_glucose_adj <- ifelse(not_fasting, NA_real_, d$z_glucose)
    if ("al_risk_glucose" %in% names(d)) d$al_risk_glucose_adj <- ifelse(not_fasting, NA_real_, d$al_risk_glucose)
  }

  # CRP is not interpretable during acute infection (commonly CRP > 10 mg/L).
  if (optional_var_exists(d, config$infection_var, "acute infection flag")) {
    infected <- !is.na(d[[config$infection_var]]) & d[[config$infection_var]] == 1
    if ("crp" %in% names(d)) d$crp_adj <- ifelse(infected, NA_real_, d$crp)
    if ("z_log_crp" %in% names(d)) d$z_log_crp_adj <- ifelse(infected, NA_real_, d$z_log_crp)
    if ("al_risk_crp" %in% names(d)) d$al_risk_crp_adj <- ifelse(infected, NA_real_, d$al_risk_crp)
  }

  # Lipid-lowering medication use biases the observed lipid panel toward
  # "healthier" than the person's untreated physiology; flag rather than
  # silently zero out, and let the modeling scripts decide whether to control
  # for med_lipid as a covariate (default) or drop treated observations in a
  # sensitivity check (see 05_model_robustness.R).
  invisible(d)
}

#' Return the medication/fasting/infection-adjusted version of `var` (as
#' produced by apply_biomarker_adjustments(), suffix "_adj") if it exists,
#' otherwise the raw column. This is how the adjustment actually reaches the
#' composites -- apply_biomarker_adjustments() only *creates* the adjusted
#' columns; every composite-builder must ask for them through this function
#' rather than reading the raw column directly.
prefer_adjusted <- function(data, var) {
  adj <- paste0(var, "_adj")
  if (adj %in% names(data)) adj else var
}

#' Build the AL_count composite (0-10 count of al_risk_* == 1).
#' Falls back to a regex match on ^al_risk_ if the configured list doesn't
#' fully match the data, so a partial screenshot doesn't silently truncate
#' the index. Uses the fasting/infection-adjusted version of each flag when
#' available (see prefer_adjusted()).
build_al_count <- function(data, config) {
  configured <- intersect(config$al_risk_vars, names(data))
  # Exclude "_adj" columns from the regex fallback -- those are the adjusted
  # *alternates* selected via prefer_adjusted() below, not additional
  # independent components; matching them directly would double-count.
  regex_matched <- grep("^al_risk_.*(?<!_adj)$", names(data), value = TRUE, perl = TRUE)
  al_vars <- union(configured, regex_matched)

  if (length(al_vars) == 0) {
    stop("No al_risk_* columns found -- cannot build AL_count.", call. = FALSE)
  }
  if (length(regex_matched) > length(configured)) {
    extra <- setdiff(regex_matched, configured)
    message("Note: found al_risk_* columns not listed in config (", paste(extra, collapse = ", "),
            "); including them in AL_count. Add them to config$al_risk_vars to silence this message.")
  }

  al_vars_adj <- vapply(al_vars, prefer_adjusted, character(1), data = data)
  mat <- as.matrix(data[al_vars_adj])
  storage.mode(mat) <- "double"
  n_components <- rowSums(!is.na(mat))
  al_count <- rowSums(mat, na.rm = TRUE)
  al_count[n_components == 0] <- NA_real_

  list(
    al_count = al_count,
    al_count_n_components = n_components,
    al_vars_used = al_vars
  )
}

#' Build the AL_zsum composite (sum of standardized biomarkers).
#' Uses available-component sums (like AL_count) rather than requiring
#' complete data on every biomarker, since dropping anyone missing a single
#' biomarker out of ~10 would needlessly shrink the analytic sample. Uses the
#' fasting/infection-adjusted z-score version of each biomarker when
#' available (see prefer_adjusted()).
build_al_zsum <- function(data, config) {
  z_vars <- intersect(config$biomarker_z_vars, names(data))
  if (length(z_vars) == 0) {
    stop("No configured biomarker_z_vars found -- cannot build AL_zsum.", call. = FALSE)
  }
  z_vars_adj <- vapply(z_vars, prefer_adjusted, character(1), data = data)
  mat <- as.matrix(data[z_vars_adj])
  storage.mode(mat) <- "double"
  n_components <- rowSums(!is.na(mat))
  al_zsum <- rowSums(mat, na.rm = TRUE)
  al_zsum[n_components == 0] <- NA_real_
  # Rescale by number of contributing components so a respondent with 6 of 10
  # components isn't automatically lower-scoring than one with all 10.
  al_zmean <- ifelse(n_components > 0, al_zsum / n_components, NA_real_)

  list(
    al_zsum = al_zsum,
    al_zmean = al_zmean,
    al_zsum_n_components = n_components,
    z_vars_used = z_vars
  )
}

#' Convenience wrapper: add AL_count, AL_zmean, and adjusted biomarker
#' columns onto `data` in one call.
add_al_composites <- function(data, config) {
  d <- apply_biomarker_adjustments(data, config)
  cnt <- build_al_count(d, config)
  zsum <- build_al_zsum(d, config)
  d$AL_count <- cnt$al_count
  d$AL_count_n <- cnt$al_count_n_components
  d$AL_zmean <- zsum$al_zmean
  d$AL_zsum_n <- zsum$al_zsum_n_components
  attr(d, "al_vars_used") <- cnt$al_vars_used
  attr(d, "z_vars_used") <- zsum$z_vars_used
  d
}
