# Moderation models, analogous to the dissertation's Paper 1/Hypothesis 3
# interaction specification: AL ~ exposure + moderator + exposure:moderator.
# Run on Model A (cumulative exposure -> first biomarker wave), since that is
# where the moderators (measured once, or as baseline/avg scores) naturally
# attach; Model B's within-person change frame has far less power for
# interactions given only 1-2 wave-pairs per person.
#
# Moderators tested, each in its own model (not all interacted at once, per
# the dissertation's approach of separate models per primary/secondary
# moderator):
#   - family_connection_z        (primary; Hypothesis 3a analogue)
#   - neighborhood_poverty (poverty_z) / neighborhood_disadv (Hypothesis 3c)
#   - school_connect_baseline / school_connect_avg (secondary/exploratory)
#   - religion_attend_z          (secondary/exploratory)
#   - peer_risk                  (secondary; only if present in the data)

run_moderation_models <- function(samples, config, outcome = "AL_count") {
  d <- samples$bio_first
  covs <- intersect(c(config$baseline_covariates, config$time_varying_covariates), names(d))

  moderators_to_test <- config$moderators[c("family_connection_z", "neighborhood_poverty",
                                              "neighborhood_disadv", "school_connect",
                                              "school_connect_avg", "religion_attend",
                                              "peer_risk")]

  results <- list()
  for (mod_label in names(moderators_to_test)) {
    mod_var <- moderators_to_test[[mod_label]]
    if (is.null(mod_var) || !optional_var_exists(d, mod_var, mod_label)) next

    for (exposure_var in c("cum_crime_exposure_z", "cum_violence_exposure_z")) {
      rhs <- c(exposure_var, mod_var, paste0(exposure_var, ":", mod_var), covs)
      form <- stats::as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))
      lbl <- sprintf("Moderation: %s ~ %s x %s", outcome, exposure_var, mod_label)
      tidy <- tryCatch(
        fit_and_tidy(form, d, cluster_var = config$id_var, label = lbl),
        error = function(e) {
          warning(sprintf("Skipping '%s': %s", lbl, conditionMessage(e)), call. = FALSE)
          NULL
        }
      )
      if (!is.null(tidy)) results[[lbl]] <- tidy
    }
  }

  if (length(results) == 0) {
    warning("No moderators were available in the data -- moderation models were all skipped.")
    return(NULL)
  }
  out <- do.call(rbind, results)
  rownames(out) <- NULL
  out
}
