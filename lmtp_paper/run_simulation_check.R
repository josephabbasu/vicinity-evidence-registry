# ------------------------------------------------------------------
# run_simulation_check.R
# Does the pipeline recover a KNOWN policy effect from data with attrition?
#   truth    : re-run the generating process with involvement set to 0 (N = 200k)
#   estimate : build_design() + ice_gcomp() on a masked sample with dropout
# Usage:  Rscript run_simulation_check.R [reps] [n] [type]
#         type = "strong" (default; verifies the code) or "calibrated"
#         (paper-sized effects; shows the REALISTIC effect size and the power problem)
# ------------------------------------------------------------------
args <- commandArgs(TRUE)
reps <- if (length(args) >= 1) as.integer(args[1]) else 4
n    <- if (length(args) >= 2) as.integer(args[2]) else 6000
type <- if (length(args) >= 3) args[3] else "strong"
source("R/00_config.R"); source("R/utils.R"); source("R/01_simulate_cohort.R")
source("R/02_build_design_data.R"); source("R/04_gcomp_validation.R")
par <- sim_params(type)
cat(sprintf("signal=%s  reps=%d  n=%d\n\n", type, reps, n))

designs <- cfg$designs
res <- list()
for (dn in names(designs)) {
  des <- designs[[dn]]
  truth <- sapply(cfg$policy_names, function(p)
    sim_truth(des, policy_waves(des, p), N = 150000, par = par)["diff"])
  tnat <- sim_truth(des, integer(0), N = 150000, par = par)["natural"]
  for (r in seq_len(reps)) {
    w  <- simulate_cohort(n, seed = 100 + r, par = par)
    bd <- build_design(w, des, "any", "post", verbose = FALSE)
    set.seed(r)
    g  <- gcomp_policies(bd, cfg$policy_names)
    cc <- mean(bd$data[[bd$spec$outcome]], na.rm = TRUE)       # complete-case mean
    res[[length(res) + 1]] <- data.frame(
      design = dn, rep = r, n_elig = nrow(bd$data),
      policy = c("natural", cfg$policy_names),
      est = g$est, diff_est = g$diff_vs_natural,
      truth_diff = c(0, unname(truth)),
      truth_natural = unname(tnat), cc_mean = cc)
  }
}
R <- do.call(rbind, res)
S <- aggregate(cbind(diff_est, truth_diff) ~ design + policy, R[R$policy != "natural", ],
               function(x) c(mean = mean(x), sd = sd(x)))
out <- data.frame(S[, 1:2], est_mean = S$diff_est[, "mean"], est_sd = S$diff_est[, "sd"],
                  truth = S$truth_diff[, "mean"])
out$bias <- out$est_mean - out$truth
nat <- aggregate(cbind(est, cc_mean, truth_natural) ~ design, R[R$policy == "natural", ], mean)
cat("== Policy effect (difference vs natural course) ==\n"); print(out, digits = 3, row.names = FALSE)
cat("\n== Natural-course mean: ICE vs complete-case vs truth ==\n"); print(nat, digits = 4, row.names = FALSE)
cat("\nReading: |bias| should be small relative to est_sd; the ICE natural mean should sit\n",
    "closer to the truth than the complete-case mean when dropout is informative.\n")
dir.create("output", showWarnings = FALSE)
write.csv(R, sprintf("output/sim_check_%s.csv", type), row.names = FALSE)
