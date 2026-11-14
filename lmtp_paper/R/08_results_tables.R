# ------------------------------------------------------------------
# 08_results_tables.R -- tidy tables from fit_lmtp_design() output
# ------------------------------------------------------------------
if (!exists("fmt_ci")) source("R/utils.R")

tidy_design_result <- function(res, design_name, timing, exposure, estimator) {
  e <- res$estimates; c <- res$contrasts
  e$design <- design_name; e$timing <- timing; e$exposure <- exposure; e$estimator <- estimator
  c$design <- design_name; c$timing <- timing; c$exposure <- exposure; c$estimator <- estimator
  list(estimates = e, contrasts = c)
}

write_results <- function(all, dir = "output") {
  dir.create(dir, showWarnings = FALSE, recursive = TRUE)
  E <- do.call(rbind, lapply(all, `[[`, "estimates"))
  C <- do.call(rbind, lapply(all, `[[`, "contrasts"))
  C$diff_ci <- fmt_ci(C$diff, C$lo, C$hi)
  utils::write.csv(E, file.path(dir, "lmtp_mean_outcomes.csv"), row.names = FALSE)
  utils::write.csv(C, file.path(dir, "lmtp_contrasts.csv"),     row.names = FALSE)
  invisible(list(estimates = E, contrasts = C))
}
