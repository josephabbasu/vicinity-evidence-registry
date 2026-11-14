# ------------------------------------------------------------------
# 06_diagnostics.R -- positivity / overlap, and the lmtp API smoke test
# ------------------------------------------------------------------
# P(exposure = 1) by wave and by prior-wave involvement. Rows with very few
# exposed (or unexposed) units flag positivity problems BEFORE any model is run.
positivity_table <- function(bd) {
  dd <- bd$data; trt <- bd$spec$trt
  out <- lapply(seq_along(trt), function(k) {
    a <- dd[[trt[k]]]
    prev <- if (k > 1) dd[[trt[k - 1]]] else {
      w0 <- bd$design$trt_waves[1] - 1
      cv <- paste0(c("vic_", "perp_"), w0)
      if (all(cv %in% names(dd))) pmax(dd[[cv[1]]], dd[[cv[2]]]) else rep(NA_real_, nrow(dd))
    }
    f <- function(m) data.frame(n = sum(m, na.rm = TRUE), n_exposed = sum(a[m] == 1, na.rm = TRUE),
                                share = mean(a[m] == 1, na.rm = TRUE))
    rbind(cbind(wave_trt = trt[k], stratum = "all", f(!is.na(a))),
          cbind(wave_trt = trt[k], stratum = "prior=0", f(!is.na(prev) & prev == 0)),
          cbind(wave_trt = trt[k], stratum = "prior=1", f(!is.na(prev) & prev == 1)))
  })
  out <- do.call(rbind, out)
  out$flag <- ifelse(out$n_exposed < 30 & out$n > 0, "FEW EXPOSED (<30)", "")
  out
}

# Minimal lmtp smoke test on simulated data (n small, 2 cheap learners).
# Run this on YOUR machine before the real analysis.
check_lmtp_api <- function(n = 1500) {
  stopifnot(requireNamespace("lmtp", quietly = TRUE))
  source("R/01_simulate_cohort.R"); source("R/02_build_design_data.R")
  wide <- simulate_cohort(n, seed = 7)
  bd <- build_design(wide, cfg$designs$dep_III_IV, "any", "post", verbose = FALSE)
  v <- utils::packageVersion("lmtp")
  lr <- if (v >= "1.4.0") c("mean", "glm") else c("SL.mean", "SL.glm")
  fit <- lmtp::lmtp_tmle(bd$data, trt = bd$spec$trt, outcome = bd$spec$outcome,
                         baseline = bd$spec$baseline, time_vary = bd$spec$time_vary,
                         cens = bd$spec$cens, shift = make_shift("A_4"),
                         outcome_type = "continuous", folds = 2,
                         learners_outcome = lr, learners_trt = lr)
  stopifnot(is.numeric(fit$theta), is.numeric(fit$standard_error))
  message("lmtp ", as.character(v), " API check passed; theta = ", round(fit$theta, 3))
  invisible(fit)
}
