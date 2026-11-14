# ------------------------------------------------------------------
# 03_fit_lmtp.R
# Primary estimator: longitudinal modified treatment policies (LMTP) with
# targeted/double-robust estimation and a super-learner ensemble.
#   lmtp::lmtp_tmle  (primary)     lmtp::lmtp_sdr (sensitivity)
# STATUS: written against the lmtp API from its documentation; it could NOT be
# executed in the sandbox where this repo was prepared (CRAN unreachable).
# Run 06_check_lmtp_api.R first on your machine: it fits a tiny model on the
# simulated data and fails loudly if any argument name differs in your version.
# ------------------------------------------------------------------
if (!exists("policy_waves")) source("R/00_config.R")

# Deterministic "set to 0" shift at chosen treatment columns; identity elsewhere.
make_shift <- function(policy_cols) {
  force(policy_cols)
  function(data, trt) {
    if (trt %in% policy_cols) rep(0, nrow(data)) else data[[trt]]
  }
}

# learner names changed across lmtp versions (SuperLearner -> mlr3superlearner)
default_learners <- function() {
  v <- tryCatch(utils::packageVersion("lmtp"), error = function(e) NULL)
  if (!is.null(v) && v >= "1.4.0") {
    L <- c("mean", "glm", "glmnet", "ranger")
  } else {
    L <- c("SL.mean", "SL.glm", "SL.glmnet", "SL.ranger")
  }
  list(outcome = L, trt = L)
}

.extract <- function(fit) {
  data.frame(theta = fit$theta, se = fit$standard_error,
             lo = fit$low, hi = fit$high)
}
.extract_contrast <- function(ct) {
  v <- ct$vals
  if (is.null(v)) v <- ct$estimates
  data.frame(diff = v$theta, se = v$std.error, lo = v$conf.low, hi = v$conf.high,
             p = v$p.value)
}

fit_lmtp_design <- function(bd, policy_names = cfg$policy_names,
                            estimator = c("tmle", "sdr"),
                            learners = default_learners(),
                            folds = cfg$folds, k = cfg$k, seed = cfg$seed) {
  estimator <- match.arg(estimator)
  fn <- switch(estimator, tmle = lmtp::lmtp_tmle, sdr = lmtp::lmtp_sdr)
  dd <- bd$data; spec <- bd$spec; des <- bd$design
  common <- list(data = dd, trt = spec$trt, outcome = spec$outcome,
                 baseline = spec$baseline, time_vary = spec$time_vary,
                 cens = spec$cens, k = k, outcome_type = "continuous",
                 id = spec$id, learners_outcome = learners$outcome,
                 learners_trt = learners$trt, folds = folds)
  set.seed(seed)
  fits <- list(natural = do.call(fn, c(common, list(shift = NULL))))
  for (p in policy_names) {
    cols <- paste0("A_", policy_waves(des, p))
    fits[[p]] <- do.call(fn, c(common, list(shift = make_shift(cols))))
  }
  est <- do.call(rbind, lapply(names(fits), function(n) cbind(policy = n, .extract(fits[[n]]))))
  ctr <- do.call(rbind, lapply(policy_names, function(p)
    cbind(contrast = paste(p, "- natural"),
          .extract_contrast(lmtp::lmtp_contrast(fits[[p]], ref = fits$natural, type = "additive")))))
  # the timing contrast: early vs late prevention (only meaningful when K >= 2)
  if (all(c("prevent_first", "prevent_last") %in% policy_names) &&
      length(des$trt_waves) > 1) {
    ctr <- rbind(ctr, cbind(contrast = "prevent_first - prevent_last",
          .extract_contrast(lmtp::lmtp_contrast(fits$prevent_first, ref = fits$prevent_last,
                                                type = "additive"))))
  }
  list(estimates = est, contrasts = ctr, fits = fits,
       weights = tryCatch(lapply(fits, function(f) summary(as.vector(f$density_ratios))),
                          error = function(e) NULL))
}
