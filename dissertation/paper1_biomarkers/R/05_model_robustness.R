# Tier-1 robustness checks, mirroring the dissertation's own robustness plan
# (alternative functional forms, lag structures, complete-case vs.
# available-case) applied to the AL_count composite. Add per-biomarker
# versions yourself by swapping the outcome if a given check proves useful.
#
# What's deliberately NOT here: multiple imputation. The dissertation uses MI
# with chained equations for covariates/moderators (never for the crime or
# CES-D/biomarker measures themselves). This module does not implement MI --
# faking imputed draws here would be worse than not having them. If you need
# MI, run `mice` (or your preferred implementation) upstream in your secure
# session and feed the completed data sets through these same models,
# pooling with Rubin's rules across the completed data sets.

#' Categorical (tertile) recoding of the cumulative crime-exposure measure,
#' to check whether the continuous/log-linear form in the main models masks
#' a nonlinear (e.g. threshold) relationship.
model_a_tertile_form <- function(samples, config, outcome = "AL_count") {
  d <- samples$bio_first
  if (!"cum_crime_exposure_z" %in% names(d)) return(NULL)
  d$crime_tertile <- tryCatch(
    cut(d$cum_crime_exposure_z,
        breaks = stats::quantile(d$cum_crime_exposure_z, probs = c(0, 1/3, 2/3, 1), na.rm = TRUE),
        include.lowest = TRUE, labels = c("low", "mid", "high")),
    error = function(e) NULL
  )
  if (is.null(d$crime_tertile)) {
    warning("Could not form crime tertiles (too little variation) -- skipping tertile-form robustness check.")
    return(NULL)
  }
  covs <- intersect(c(config$baseline_covariates, config$time_varying_covariates), names(d))
  rhs <- c("crime_tertile", "cum_violence_exposure_z", covs)
  form <- stats::as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))
  fit_and_tidy(form, d, cluster_var = config$id_var,
               label = paste0("Robustness (tertile form): ", outcome, " ~ crime tertile"))
}

#' Model B, but with the *level* of AL at wave_from added as a covariate
#' (Hypothesis-2a-style "net of prior level" conditional model), instead of
#' relying purely on the first-difference. Compare against the plain Model B
#' from 02_model_core.R to see whether conditioning on the lagged level
#' changes the exposure coefficient materially.
model_b_lagged_level <- function(samples, config, outcome = "AL_count") {
  panel_change <- samples$bio_change
  outcome_col <- paste0("d_", outcome)
  lag_col <- paste0(outcome, "_from")

  # bio_change doesn't carry the wave_from level directly; reconstruct it by
  # noting AL_from = AL_to - d_AL is NOT available without the original wide
  # values, so instead pull the level from bio_first-style long data if the
  # caller stored it. Simpler: recompute from the panel-level AL columns
  # attached earlier in 01_build_analytic_sample.R's bio_change_raw step is
  # not retained, so this check needs the raw AL panel passed in explicitly.
  if (!"AL_count_from" %in% names(panel_change) && !lag_col %in% names(panel_change)) {
    warning("Lagged-level AL not attached to bio_change -- pass `al_panel` to add_lagged_level() first. Skipping.")
    return(NULL)
  }

  covs <- intersect(paste0(config$time_varying_covariates, "_from"), names(panel_change))
  rhs <- c("d_crime_exposure", "d_violence_exposure", lag_col, covs)
  form <- stats::as.formula(paste(outcome_col, "~", paste(rhs, collapse = " + ")))
  fit_and_tidy(form, panel_change, cluster_var = config$id_var,
               label = paste0("Robustness (lagged level): change in ", outcome, " ~ change in exposure + lagged level"))
}

#' Attach the wave_from level of each outcome onto bio_change, so
#' model_b_lagged_level() has something to condition on. Call this once
#' after build_analytic_samples() if you want the lagged-level check.
add_lagged_level <- function(samples, config, al_panel, outcomes = c("AL_count", "AL_zmean")) {
  id <- config$id_var; wv <- config$wave_var
  d <- samples$bio_change
  for (oc in outcomes) {
    lvl_tbl <- al_panel[c(id, wv, oc)]
    names(lvl_tbl) <- c(id, "wave_from", paste0(oc, "_from"))
    d <- merge(d, lvl_tbl, by = c(id, "wave_from"), all.x = TRUE)
  }
  samples$bio_change <- d
  samples
}

#' Complete-case (all AL components observed) vs. available-case (current
#' default, using whatever AL components are non-missing) comparison for
#' Model A on AL_count.
model_a_complete_case <- function(samples, config, outcome = "AL_count") {
  d <- samples$bio_first
  n_col <- paste0(outcome, "_n")
  if (!n_col %in% names(d)) return(NULL)
  n_expected <- if (outcome == "AL_count") length(samples$al_vars_used) else length(samples$z_vars_used)
  complete <- d[!is.na(d[[n_col]]) & d[[n_col]] == n_expected, ]
  if (nrow(complete) < 30) {
    warning(sprintf("Only %d complete cases for %s -- skipping complete-case robustness check.",
                     nrow(complete), outcome))
    return(NULL)
  }
  covs <- intersect(c(config$baseline_covariates, config$time_varying_covariates), names(complete))
  rhs <- c("cum_crime_exposure_z", "cum_violence_exposure_z", covs)
  form <- stats::as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))
  fit_and_tidy(form, complete, cluster_var = config$id_var,
               label = paste0("Robustness (complete-case): ", outcome, " ~ cumulative exposure"))
}

#' Exploratory heterogeneity by race x gender x neighborhood-poverty tertile
#' (Hypothesis-3d analogue). Reports cell sizes and, only for cells with at
#' least `min_n`, the exposure coefficient -- underpowered cells are listed
#' but not fit, rather than reporting an unstable estimate.
model_a_subgroup_exploratory <- function(samples, config, outcome = "AL_count", min_n = 30) {
  d <- samples$bio_first
  needed <- c("race", "gender", "poverty_z")
  if (!all(needed %in% names(d))) {
    warning("race/gender/poverty_z not all present -- skipping Hypothesis-3d-style subgroup exploration.")
    return(NULL)
  }
  d$poverty_tertile <- tryCatch(
    cut(d$poverty_z, breaks = stats::quantile(d$poverty_z, probs = c(0, 1/3, 2/3, 1), na.rm = TRUE),
        include.lowest = TRUE, labels = c("low", "mid", "high")),
    error = function(e) NULL
  )
  if (is.null(d$poverty_tertile)) return(NULL)

  cells <- split(d, list(d$race, d$gender, d$poverty_tertile), drop = TRUE)
  out <- lapply(names(cells), function(cell_name) {
    cell <- cells[[cell_name]]
    if (nrow(cell) < min_n) {
      return(data.frame(term = "cum_crime_exposure_z", estimate = NA_real_, std.error = NA_real_,
                          statistic = NA_real_, df = NA_real_, p.value = NA_real_,
                          conf.low = NA_real_, conf.high = NA_real_,
                          model_label = paste0("Subgroup (n=", nrow(cell), ", underpowered, not fit): ", cell_name),
                          n_obs = nrow(cell)))
    }
    covs <- intersect(config$time_varying_covariates, names(cell))
    rhs <- c("cum_crime_exposure_z", "cum_violence_exposure_z", covs)
    form <- stats::as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))
    tryCatch(
      fit_and_tidy(form, cell, cluster_var = config$id_var,
                    label = paste0("Subgroup (H3d-style, exploratory): ", cell_name)),
      error = function(e) NULL
    )
  })
  out <- do.call(rbind, Filter(Negate(is.null), out))
  rownames(out) <- NULL
  out
}

run_robustness_checks <- function(samples, config, al_panel = NULL) {
  results <- list()

  tertile <- model_a_tertile_form(samples, config)
  if (!is.null(tertile)) results$tertile_form <- tertile

  cc <- model_a_complete_case(samples, config)
  if (!is.null(cc)) results$complete_case <- cc

  if (!is.null(al_panel)) {
    samples_lag <- add_lagged_level(samples, config, al_panel)
    lagged <- model_b_lagged_level(samples_lag, config)
    if (!is.null(lagged)) results$lagged_level <- lagged
  }

  subgroup <- model_a_subgroup_exploratory(samples, config)
  if (!is.null(subgroup)) results$subgroup_h3d <- subgroup

  if (length(results) == 0) return(NULL)
  out <- do.call(rbind, results)
  rownames(out) <- NULL
  out
}
