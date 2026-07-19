# Same two models as 02_model_core.R, but fit separately for each individual
# biomarker rather than the composites -- so a single driver (e.g. CRP) isn't
# hidden inside an aggregate score. Benjamini-Hochberg FDR correction is
# applied across biomarkers within each exposure term, since running ~12
# near-duplicate models multiplies the chance of a spurious "significant"
# result if read one at a time.

model_a_single_biomarker <- function(samples, config, biomarker) {
  d <- samples$bio_first
  if (!biomarker %in% names(d) || all(is.na(d[[biomarker]]))) return(NULL)
  covs <- intersect(c(config$baseline_covariates, config$time_varying_covariates), names(d))
  rhs <- c("cum_crime_exposure_z", "cum_violence_exposure_z", covs)
  form <- stats::as.formula(paste(biomarker, "~", paste(rhs, collapse = " + ")))
  fit_and_tidy(form, d, cluster_var = config$id_var,
               label = paste0("A: ", biomarker, " ~ cumulative exposure"))
}

model_b_single_biomarker <- function(samples, config, biomarker) {
  d <- samples$bio_change
  outcome_col <- paste0("d_", biomarker)
  if (!outcome_col %in% names(d) || all(is.na(d[[outcome_col]]))) return(NULL)
  covs <- intersect(paste0(config$time_varying_covariates, "_from"), names(d))
  rhs <- c("d_crime_exposure", "d_violence_exposure", covs)
  form <- stats::as.formula(paste(outcome_col, "~", paste(rhs, collapse = " + ")))
  fit_and_tidy(form, d, cluster_var = config$id_var,
               label = paste0("B: change in ", biomarker, " ~ change in exposure"))
}

#' Run Model A and Model B across every configured biomarker, apply
#' BH correction within each exposure term x model combination, and return a
#' single tidy table.
run_biomarker_specific_models <- function(samples, config) {
  biomarkers <- intersect(config$biomarker_vars, names(samples$bio_first))
  if (length(biomarkers) == 0) {
    warning("No configured biomarker_vars present in bio_first -- skipping per-biomarker models.")
    return(NULL)
  }

  a_results <- Filter(Negate(is.null), lapply(biomarkers, model_a_single_biomarker,
                                                samples = samples, config = config))
  b_results <- Filter(Negate(is.null), lapply(biomarkers, model_b_single_biomarker,
                                                samples = samples, config = config))

  a_tbl <- if (length(a_results) > 0) do.call(rbind, a_results) else NULL
  b_tbl <- if (length(b_results) > 0) do.call(rbind, b_results) else NULL

  if (!is.null(a_tbl)) {
    a_tbl <- add_fdr_correction(a_tbl, "cum_crime_exposure_z")
    a_tbl <- add_fdr_correction(a_tbl, "cum_violence_exposure_z")
  }
  if (!is.null(b_tbl)) {
    b_tbl <- add_fdr_correction(b_tbl, "d_crime_exposure")
    b_tbl <- add_fdr_correction(b_tbl, "d_violence_exposure")
  }

  out <- do.call(rbind, list(a_tbl, b_tbl))
  rownames(out) <- NULL
  out
}
