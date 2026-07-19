# Guards that fail loudly when an expected column is missing, instead of
# silently skipping a variable or (worse) matching the wrong one.

#' Assert that all `vars` are present as columns in `data`.
#' @param vars named or unnamed character vector of column names to check.
#' @param context short label used in the error message, e.g. "crime_vars".
assert_vars_exist <- function(data, vars, context = "") {
  vars <- unlist(vars, use.names = FALSE)
  missing <- setdiff(vars, names(data))
  if (length(missing) > 0) {
    stop(sprintf(
      "[%s] Missing expected column(s) in panel: %s\nEdit R/00_config.R if your build uses different names.",
      context, paste(missing, collapse = ", ")
    ), call. = FALSE)
  }
  invisible(TRUE)
}

#' Return TRUE/FALSE for whether `var` exists, warning once if not.
#' Used for genuinely optional variables (peer risk, family id) where the
#' calling script should skip a check rather than halt the whole run.
optional_var_exists <- function(data, var, label = var) {
  ok <- !is.null(var) && var %in% names(data)
  if (!ok) {
    warning(sprintf(
      "Optional variable '%s' (%s) not found -- skipping analyses that need it.",
      var, label
    ), call. = FALSE)
  }
  ok
}

#' Find the first candidate column that exists in `data`, or NULL with a
#' warning if none do. Used for the family/sibling id, where the exact name
#' varies across Add Health builds.
find_first_existing <- function(data, candidates, label = "column") {
  found <- candidates[candidates %in% names(data)]
  if (length(found) == 0) {
    warning(sprintf(
      "None of the candidate %s columns were found (%s) -- sibling/family fixed-effects checks will be skipped.",
      label, paste(candidates, collapse = ", ")
    ), call. = FALSE)
    return(NULL)
  }
  found[[1]]
}

#' Basic structural sanity checks on the panel before any modeling.
validate_panel <- function(data, config) {
  assert_vars_exist(data, config$id_var, "id_var")
  assert_vars_exist(data, config$wave_var, "wave_var")

  if (any(duplicated(data[c(config$id_var, config$wave_var)]))) {
    stop("Panel has duplicate (id, wave) rows -- expected exactly one row per person-wave.",
         call. = FALSE)
  }

  waves <- sort(unique(data[[config$wave_var]]))
  message(sprintf("Panel: %d rows, %d unique ids, waves observed: %s",
                   nrow(data), length(unique(data[[config$id_var]])),
                   paste(waves, collapse = ", ")))
  invisible(TRUE)
}
