# Core models for the two composite allostatic-load outcomes (AL_count,
# AL_zmean): Model A (cumulative exposure -> first biomarker wave) and
# Model B (within-person change across biomarker waves, the direct analogue
# of Paper 1's core CES-D specification).

#' Model A: AL ~ cumulative crime exposure (through wave 3) +
#'               cumulative violence/victimization exposure (through wave 5) +
#'               covariates
#' Reported with individual-clustered SEs by default; a family-clustered /
#' sibling-demeaned version is added as a robustness row when a family id
#' is available (closest available substitute for fixed effects before any
#' biomarker exists).
model_a_composite <- function(samples, config, outcome = "AL_count") {
  d <- samples$bio_first
  covs <- intersect(c(config$baseline_covariates, config$time_varying_covariates), names(d))
  rhs <- c("cum_crime_exposure_z", "cum_violence_exposure_z", covs)
  form <- stats::as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))

  main <- fit_and_tidy(form, d, cluster_var = config$id_var,
                        label = paste0("A: ", outcome, " ~ cumulative exposure (individual-clustered SE)"))

  results <- list(main = main)

  if (!is.null(samples$family_id) && samples$family_id %in% names(d)) {
    fam_var <- samples$family_id
    n_fam <- length(unique(d[[fam_var]][!is.na(d[[fam_var]])]))
    if (n_fam >= 2 && n_fam < nrow(d)) {
      # Family-demean the outcome and the two exposures of interest (the
      # Frisch-Waugh-Lovell partialling-out step for a family/sibling fixed
      # effect). Other covariates (gender, race, birth_year, ...) are left
      # un-demeaned as ordinary controls rather than being converted to
      # numeric dummies and demeaned themselves -- this is a lightweight
      # approximation to a full LSDV family-FE model, adequate for a
      # robustness check but not a substitute for `fixest::feols(y ~ x |
      # family_id)` in your real (CRAN-connected) analysis environment.
      dm_vars <- c(outcome, "cum_crime_exposure_z", "cum_violence_exposure_z")
      d_dm <- demean_by_group(d, dm_vars, fam_var)
      dm_rhs <- paste0(dm_vars[-1], "_dm")
      form_dm <- stats::as.formula(paste0(outcome, "_dm ~ ",
                                            paste(c(dm_rhs, covs), collapse = " + ")))
      fam_clustered <- fit_and_tidy(form_dm, d_dm, cluster_var = fam_var,
                                     label = paste0("A-robustness: ", outcome,
                                                     " ~ cumulative exposure, family-demeaned (sibling FE approx.)"))
      results$family_fe <- fam_clustered
    } else {
      message("Family id present but has <2 families or one row per family -- skipping sibling-FE robustness check.")
    }
  }

  results
}

#' Model B: change in AL between consecutive biomarker waves ~ change in
#' interwave crime exposure + change in cumulative violence exposure,
#' clustered by person (multiple wave-pairs per person for those observed at
#' 3 biomarker waves).
model_b_composite <- function(samples, config, outcome = "AL_count") {
  d <- samples$bio_change
  outcome_col <- paste0("d_", outcome)
  covs <- intersect(paste0(config$time_varying_covariates, "_from"), names(d))
  rhs <- c("d_crime_exposure", "d_violence_exposure", covs)
  form <- stats::as.formula(paste(outcome_col, "~", paste(rhs, collapse = " + ")))

  fit_and_tidy(form, d, cluster_var = config$id_var,
               label = paste0("B: change in ", outcome, " ~ change in exposure (within-person, individual-clustered SE)"))
}

#' Run both models for both composite outcomes and return one combined,
#' tidy results table.
run_core_models <- function(samples, config) {
  outcomes <- c("AL_count", "AL_zmean")
  all_results <- list()

  for (oc in outcomes) {
    a <- model_a_composite(samples, config, oc)
    all_results[[paste0("A_", oc, "_main")]] <- a$main
    if (!is.null(a$family_fe)) all_results[[paste0("A_", oc, "_family_fe")]] <- a$family_fe

    b <- model_b_composite(samples, config, oc)
    all_results[[paste0("B_", oc)]] <- b
  }

  out <- do.call(rbind, all_results)
  rownames(out) <- NULL
  out
}
