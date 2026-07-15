# Master runner. From the analysis root (analysis/crime-depression-lags):
#   Real data:      Rscript R/run_all.R            (inputs already in input/)
#   Pipeline test:  Rscript R/run_all.R --simulate (synthetic inputs + validation)

args <- commandArgs(trailingOnly = TRUE)
simulate <- "--simulate" %in% args

run <- function(script) {
  cat(sprintf("\n==== %s ====\n", script))
  status <- system2("Rscript", file.path("R", script))
  if (status != 0) stop(sprintf("%s failed (exit %d)", script, status))
}

if (simulate) run("99_simulate_inputs.R")
run("01_build_panel.R")
run("02_descriptives.R")
run("03_models.R")
run("04_sensitivity.R")
if (simulate) run("98_validate_recovery.R")

cat("\nAll steps completed. Outputs in output/.\n")
