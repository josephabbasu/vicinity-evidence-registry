# Construction of the two exposure families:
#   - cumulative county-level violent crime through config$crime_wave_cutoff
#   - cumulative self-reported violence/victimization through
#     config$victimization_wave_cutoff
#
# These are built per-person as of a given wave cutoff, so they can be
# attached to whichever biomarker wave comes after them (Model A), and their
# *increments* between two adult waves can be computed for Model B.

#' For each person, take the value of a cumulative-style variable observed at
#' the last wave <= `cutoff_wave`, per person. Cumulative variables in the
#' panel (violent_cumulative, violent_cum_log, violent_exp_total_cum, ...) are
#' already running totals as of each wave, so "cumulative exposure through
#' wave 3" is just that variable's value at the last observed wave <= 3.
last_value_through_wave <- function(data, config, var, cutoff_wave) {
  assert_vars_exist(data, var, "last_value_through_wave")
  id <- config$id_var; wv <- config$wave_var
  sub <- data[data[[wv]] <= cutoff_wave & !is.na(data[[var]]), c(id, wv, var)]
  if (nrow(sub) == 0) {
    warning(sprintf("No non-missing '%s' observed at or before wave %d.", var, cutoff_wave),
            call. = FALSE)
    return(data.frame(id = unique(data[[id]]), value = NA_real_) |>
             stats::setNames(c(id, var)))
  }
  sub <- sub[order(sub[[id]], sub[[wv]]), ]
  last_rows <- !duplicated(sub[[id]], fromLast = TRUE)
  out <- sub[last_rows, c(id, var)]
  names(out) <- c(id, var)
  out
}

#' Build the Model-A exposure table: one row per person, with cumulative
#' county crime through the crime cutoff and cumulative victimization through
#' the victimization cutoff, on both raw and standardized scales.
build_cumulative_exposure_table <- function(data, config) {
  id <- config$id_var

  crime_var <- config$crime_vars$cumulative_log %||% config$crime_vars$cumulative
  vict_var  <- config$victimization_vars$cum_log %||% config$victimization_vars$cum

  crime_tbl <- last_value_through_wave(data, config, crime_var, config$crime_wave_cutoff)
  vict_tbl  <- last_value_through_wave(data, config, vict_var, config$victimization_wave_cutoff)

  out <- merge(crime_tbl, vict_tbl, by = id, all = TRUE)
  names(out)[names(out) == crime_var] <- "cum_crime_exposure"
  names(out)[names(out) == vict_var]  <- "cum_violence_exposure"

  out$cum_crime_exposure_z    <- as.numeric(scale(out$cum_crime_exposure))
  out$cum_violence_exposure_z <- as.numeric(scale(out$cum_violence_exposure))
  out
}

`%||%` <- function(a, b) if (is.null(a)) b else a

#' Build the Model-B increment table: for each person with >=2 biomarker
#' waves, the change in the *interwave* crime/violence measures between
#' consecutive biomarker waves. This is the direct analogue of Paper 1's
#' "change in crime between waves t-1 and t" predictor, just evaluated over
#' the adult inter-biomarker-wave interval instead of the adolescent one.
build_interwave_increment_table <- function(data, config, bio_waves) {
  id <- config$id_var; wv <- config$wave_var
  crime_var <- config$crime_vars$interwave_log %||% config$crime_vars$interwave_avg
  vict_var  <- config$victimization_vars$cum_log %||% config$victimization_vars$cum
  assert_vars_exist(data, c(crime_var, vict_var), "build_interwave_increment_table")

  sub <- data[data[[wv]] %in% bio_waves, c(id, wv, crime_var, vict_var)]
  sub <- sub[order(sub[[id]], sub[[wv]]), ]

  split_by_id <- split(sub, sub[[id]])
  rows <- lapply(split_by_id, function(person) {
    if (nrow(person) < 2) return(NULL)
    d_crime <- diff(person[[crime_var]])
    d_vict  <- diff(person[[vict_var]])
    data.frame(
      id_val   = person[[id]][-1],
      wave_from = person[[wv]][-nrow(person)],
      wave_to   = person[[wv]][-1],
      d_crime_exposure   = d_crime,
      d_violence_exposure = d_vict
    )
  })
  out <- do.call(rbind, rows)
  if (is.null(out) || nrow(out) == 0) {
    stop("No respondent has >=2 biomarker waves -- Model B (within-person change) cannot be fit. ",
         "Check that biomarker waves were detected correctly.", call. = FALSE)
  }
  names(out)[names(out) == "id_val"] <- id
  out
}
