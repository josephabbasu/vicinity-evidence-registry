# Master script. From an R session with working directory set to
# dissertation/paper1_biomarkers/ (or after sourcing 00_config.R with an
# absolute path adjusted), run:
#
#   source("R/06_run_all.R")
#
# This expects either:
#   (a) config$panel_path set in R/00_config.R to a file readable by
#       readRDS() or read.csv(), or
#   (b) a data frame named `panel` already in the global environment before
#       you source this script.

this_dir <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) "R")
if (is.na(this_dir) || this_dir == "") this_dir <- "R"

source(file.path(this_dir, "00_config.R"))
source(file.path(this_dir, "utils_checks.R"))
source(file.path(this_dir, "utils_al_index.R"))
source(file.path(this_dir, "utils_exposure.R"))
source(file.path(this_dir, "utils_stats.R"))
source(file.path(this_dir, "01_build_analytic_sample.R"))
source(file.path(this_dir, "02_model_core.R"))
source(file.path(this_dir, "03_model_by_biomarker.R"))
source(file.path(this_dir, "04_model_moderation.R"))
source(file.path(this_dir, "05_model_robustness.R"))

if (!is.null(config$panel_path)) {
  message("Loading panel from ", config$panel_path)
  panel <- if (grepl("\\.rds$", config$panel_path, ignore.case = TRUE)) {
    readRDS(config$panel_path)
  } else {
    utils::read.csv(config$panel_path, stringsAsFactors = FALSE)
  }
} else if (!exists("panel")) {
  stop("No `panel` data frame found and config$panel_path is NULL. ",
       "Either load your panel into a variable named `panel` before sourcing ",
       "this script, or set config$panel_path in R/00_config.R.", call. = FALSE)
}

message("\n== Building analytic samples ==")
samples <- build_analytic_samples(panel, config)
message(sprintf("bio_first: %d respondents at their first biomarker wave.", nrow(samples$bio_first)))
message(sprintf("bio_change: %d person-interval rows for within-person change models.", nrow(samples$bio_change)))

message("\n== Core models (Model A + Model B, composite outcomes) ==")
core_results <- run_core_models(samples, config)

message("\n== Per-biomarker models (with BH-FDR correction) ==")
biomarker_results <- run_biomarker_specific_models(samples, config)

message("\n== Moderation models ==")
moderation_results_count  <- run_moderation_models(samples, config, outcome = "AL_count")
moderation_results_zmean  <- run_moderation_models(samples, config, outcome = "AL_zmean")
moderation_results <- do.call(rbind, Filter(Negate(is.null),
                                              list(moderation_results_count, moderation_results_zmean)))

message("\n== Robustness checks ==")
robustness_results <- run_robustness_checks(samples, config, al_panel = samples$panel_al)

if (!dir.exists(config$output_dir)) dir.create(config$output_dir, recursive = TRUE)

write_if_not_null <- function(x, filename) {
  if (is.null(x)) {
    message("(nothing to write for ", filename, " -- see warnings above)")
    return(invisible(NULL))
  }
  path <- file.path(config$output_dir, filename)
  utils::write.csv(x, path, row.names = FALSE)
  message("Wrote ", path)
}

write_if_not_null(core_results, "01_core_models.csv")
write_if_not_null(biomarker_results, "02_biomarker_specific_models.csv")
write_if_not_null(moderation_results, "03_moderation_models.csv")
write_if_not_null(robustness_results, "04_robustness_checks.csv")

message("\nDone. Review output/ and the warnings printed above (missing optional ",
        "variables, skipped checks) before interpreting results.")
