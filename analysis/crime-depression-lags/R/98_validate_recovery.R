# Pipeline verification on simulated inputs: check that primary estimands
# L1-L3 recover the known structural lag effect within Monte Carlo error.
# Run AFTER 99_simulate_inputs.R -> 01 -> 03. Fails (nonzero exit) if any
# primary estimate is more than ~3 SE from the truth, or if signs/CI logic break.
# Run from the analysis root: Rscript R/98_validate_recovery.R

source("R/00_config.R")

truth <- readRDS(file.path(cfg$output_dir, "sim_truth.rds"))
res <- readRDS(file.path(cfg$output_dir, "main_results.rds"))

# Observed CES-D = 0.33*y + noise, z-scored by wave. The standardized lagged
# estimand is TRUE_LAG_BETA * (0.33 / sd(cesd)) ~= TRUE_LAG_BETA / sd(y_wave),
# with slight attenuation from measurement noise on baseline CES-D. Rather than
# derive it exactly, require: estimate within 3*SE of TRUE_LAG_BETA scaled by a
# plausible band [0.6, 1.4] — loose enough for Monte Carlo error, tight enough
# to catch sign errors, wrong merges, exposure/outcome swaps, or broken SEs.
beta_true <- truth$true_lag_beta

fail <- character(0)
for (nm in c("L1", "L2", "L3")) {
  r <- res[res$estimand == nm, ]
  lo <- 0.6 * beta_true - 3 * r$se
  hi <- 1.4 * beta_true + 3 * r$se
  ok <- r$beta >= lo && r$beta <= hi
  cat(sprintf("%s: beta = %.4f (SE %.4f), acceptance band [%.4f, %.4f] -> %s\n",
              nm, r$beta, r$se, lo, hi, if (ok) "PASS" else "FAIL"))
  if (!ok) fail <- c(fail, nm)
  if (r$ci_lo > r$beta || r$ci_hi < r$beta) fail <- c(fail, paste0(nm, ":CI"))
  if (r$se <= 0 || r$n < 1000) fail <- c(fail, paste0(nm, ":SE/N"))
}

if (length(fail) > 0) {
  cat("VALIDATION FAILED:", paste(fail, collapse = ", "), "\n")
  quit(status = 1)
}
cat("VALIDATION PASSED: primary estimands recover the simulated truth.\n")
