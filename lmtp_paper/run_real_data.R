# ------------------------------------------------------------------
# run_real_data.R -- the real-data analysis (RUN INSIDE YOUR APPROVED Add Health
# environment; restricted data must not leave it).
#   1. Put the canonical wide file at data/analysis_wide.csv  (see DATA_DICTIONARY_template.csv)
#   2. Rscript run_real_data.R
# Needs: lmtp (+ its learner packages), data.table, glmnet, ranger.
# Run  source('R/06_diagnostics.R'); check_lmtp_api()  once first.
# ------------------------------------------------------------------
source("R/00_config.R"); source("R/utils.R"); source("R/02_build_design_data.R")
source("R/03_fit_lmtp.R"); source("R/04_gcomp_validation.R"); source("R/05_fe_benchmark.R")
source("R/06_diagnostics.R"); source("R/08_results_tables.R")
suppressPackageStartupMessages(library(data.table))

# Option A (recommended): run inside the RStudio session that already holds your objects
#   panel, biomarkers_panel_long_w456, sib_prof   (see R/07a_adapter_from_panel.R)
# Option B: a saved canonical wide file.
source("R/07a_adapter_from_panel.R")
if (exists("panel") && exists("biomarkers_panel_long_w456")) {
  wide <- build_wide_from_panel(panel, biomarkers_panel_long_w456,
                                if (exists("sib_prof")) sib_prof else NULL)
} else wide <- fread("data/analysis_wide.csv")
need <- c("id", "fam", "female", "minority", "age1", "vic_1", "perp_1", "dep_1")
stopifnot(all(need %in% names(wide)))

all <- list(); i <- 0
for (dn in names(cfg$designs)) for (tm in cfg$timings) {
  bd <- build_design(wide, cfg$designs[[dn]], cfg$exposure, tm)
  print(positivity_table(bd))                       # inspect BEFORE fitting
  res <- fit_lmtp_design(bd, estimator = "tmle")    # primary
  i <- i + 1; all[[i]] <- tidy_design_result(res, dn, tm, cfg$exposure, "tmle")
  # independent cross-check (plug-in; not the headline)
  gc <- gcomp_policies(bd, cfg$policy_names)
  write.csv(gc, sprintf("output/gcomp_crosscheck_%s_%s.csv", dn, tm), row.names = FALSE)
}
write_results(all)

# Secondary analyses (pre-specify): role-specific exposure, SDR estimator, k = 1
# for (ex in c("vic", "perp")) { ... build_design(wide, des, ex, "post") ... }
# fit_lmtp_design(bd, estimator = "sdr");  fit_lmtp_design(bd, k = 1)

# Association benchmark for triangulation with Papers 2-4
fb <- fe_benchmark(wide); print(fb$main); print(fb$lead_placebo)
write.csv(fb$main, "output/fe_benchmark.csv", row.names = FALSE)
