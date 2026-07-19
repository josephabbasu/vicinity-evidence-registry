# Builds the two analytic datasets used by every model script:
#   bio_first  -- one row per person, at their FIRST observed biomarker wave
#                 (Model A: cumulative adolescent exposure -> adult biology)
#   bio_change -- one row per person per consecutive pair of biomarker waves,
#                 first-differenced (Model B: within-person change, the
#                 direct Paper-1 analogue)
#
# Source order: 00_config.R, utils_checks.R, utils_al_index.R,
# utils_exposure.R, utils_stats.R must already be sourced (06_run_all.R does
# this for you).

build_analytic_samples <- function(panel, config) {
  validate_panel(panel, config)

  id <- config$id_var
  wv <- config$wave_var

  bio_waves <- detect_biomarker_waves(panel, config)
  panel_al <- add_al_composites(panel, config)

  # ---- Model A: cumulative exposure -> first biomarker wave ---------------
  first_wave_tbl <- panel_al[panel_al[[wv]] %in% bio_waves, ]
  first_wave_tbl <- first_wave_tbl[order(first_wave_tbl[[id]], first_wave_tbl[[wv]]), ]
  first_wave_tbl <- first_wave_tbl[!duplicated(first_wave_tbl[[id]]), ]

  exposure_tbl <- build_cumulative_exposure_table(panel, config)

  bio_first <- merge(first_wave_tbl, exposure_tbl, by = id, all.x = TRUE)

  # attach optional moderators / covariates if present
  moderator_cols <- unlist(config$moderators, use.names = FALSE)
  moderator_cols <- intersect(moderator_cols, names(panel))
  covariate_cols <- intersect(c(config$baseline_covariates, config$time_varying_covariates),
                              names(panel))

  extra_cols <- unique(c(moderator_cols, covariate_cols))
  extra_cols <- setdiff(extra_cols, names(bio_first))
  if (length(extra_cols) > 0) {
    extra_tbl <- panel[panel[[wv]] %in% bio_waves, c(id, wv, extra_cols)]
    extra_tbl <- extra_tbl[order(extra_tbl[[id]], extra_tbl[[wv]]), ]
    extra_tbl <- extra_tbl[!duplicated(extra_tbl[[id]]), setdiff(names(extra_tbl), wv)]
    bio_first <- merge(bio_first, extra_tbl, by = id, all.x = TRUE)
  }

  # family/sibling id, for the Model-A robustness check
  family_id <- find_first_existing(panel, config$family_id_candidates, "family/sibling")
  if (!is.null(family_id)) {
    fam_tbl <- unique(panel[c(id, family_id)])
    bio_first <- merge(bio_first, fam_tbl, by = id, all.x = TRUE)
  }

  # ---- Model B: within-person change across biomarker waves ---------------
  increment_tbl <- build_interwave_increment_table(panel, config, bio_waves)

  bio_change_raw <- panel_al[panel_al[[wv]] %in% bio_waves, ]
  bio_change_raw <- bio_change_raw[order(bio_change_raw[[id]], bio_change_raw[[wv]]), ]

  outcome_vars <- c("AL_count", "AL_zmean",
                     intersect(config$biomarker_vars, names(bio_change_raw)))

  split_by_id <- split(bio_change_raw, bio_change_raw[[id]])
  diff_rows <- lapply(split_by_id, function(person) {
    if (nrow(person) < 2) return(NULL)
    out <- lapply(seq_len(nrow(person) - 1), function(i) {
      row <- list(wave_from = person[[wv]][i], wave_to = person[[wv]][i + 1])
      row[[id]] <- person[[id]][i]
      for (v in outcome_vars) {
        row[[paste0("d_", v)]] <- person[[v]][i + 1] - person[[v]][i]
      }
      as.data.frame(row, stringsAsFactors = FALSE)
    })
    do.call(rbind, out)
  })
  bio_change_outcomes <- do.call(rbind, diff_rows)

  bio_change <- merge(bio_change_outcomes, increment_tbl,
                       by = c(id, "wave_from", "wave_to"), all.x = TRUE)

  # baseline covariates (measured at wave_from) for Model B controls
  if (length(covariate_cols) > 0) {
    cov_tbl <- panel[c(id, wv, covariate_cols)]
    names(cov_tbl)[names(cov_tbl) == wv] <- "wave_from"
    names(cov_tbl)[names(cov_tbl) %in% covariate_cols] <- paste0(covariate_cols, "_from")
    bio_change <- merge(bio_change, cov_tbl, by = c(id, "wave_from"), all.x = TRUE)
  }

  list(
    bio_waves = bio_waves,
    bio_first = bio_first,
    bio_change = bio_change,
    panel_al = panel_al,
    family_id = family_id,
    al_vars_used = attr(panel_al, "al_vars_used"),
    z_vars_used = attr(panel_al, "z_vars_used"),
    moderator_cols = moderator_cols,
    covariate_cols = covariate_cols
  )
}
