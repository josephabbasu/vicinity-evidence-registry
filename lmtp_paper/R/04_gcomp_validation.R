# ------------------------------------------------------------------
# 04_gcomp_validation.R
# Iterated-conditional-expectation (sequential regression) g-computation with a
# cross-validated "discrete super learner" (elastic net vs random forest).
# Same estimand as the lmtp analysis (deterministic set-to-0 policies, monotone
# censoring handled by fitting only on rows still observed).
#
# Role: (1) validation target on simulated data (known truth),
#       (2) an independent cross-check of the lmtp fit on real data.
# It is a PLUG-IN estimator (no targeting step, no cross-fitting): expect it to
# be less robust than lmtp::lmtp_tmle/lmtp_sdr; do not use it as the headline.
# ------------------------------------------------------------------
suppressPackageStartupMessages({ library(glmnet); library(ranger) })

.learners <- list(
  glmnet = list(
    fit  = function(X, y) glmnet::cv.glmnet(as.matrix(X), y, alpha = .5, nfolds = 5),
    pred = function(m, X) as.numeric(predict(m, as.matrix(X), s = "lambda.min"))),
  ranger = list(
    fit  = function(X, y) ranger::ranger(y ~ ., data = cbind(y = y, X), num.trees = 300,
                                         min.node.size = 20, num.threads = 2),
    pred = function(m, X) predict(m, data = X)$predictions)
)

discrete_sl <- function(X, y, cands = c("glmnet", "ranger"), v = 5) {
  X <- as.data.frame(X)
  if (length(cands) == 1) best <- cands else {
    fold <- sample(rep_len(seq_len(v), nrow(X)))
    cv <- sapply(cands, function(cn) {
      mean(sapply(seq_len(v), function(f) {
        m <- .learners[[cn]]$fit(X[fold != f, , drop = FALSE], y[fold != f])
        mean((y[fold == f] - .learners[[cn]]$pred(m, X[fold == f, , drop = FALSE]))^2)
      }))
    })
    best <- cands[which.min(cv)]
  }
  m <- .learners[[best]]$fit(X, y)
  list(learner = best, predict = function(Xn) .learners[[best]]$pred(m, as.data.frame(Xn)))
}

ice_gcomp <- function(dd, spec, policy_cols = character(0),
                      cands = c("glmnet", "ranger")) {
  K <- length(spec$trt); n <- nrow(dd)
  alive <- matrix(TRUE, n, K)
  if (K > 1) for (k in 2:K) alive[, k] <- alive[, k - 1] & dd[[spec$cens[k - 1]]] == 1
  Q <- dd[[spec$outcome]]
  chosen <- character(K)
  for (k in K:1) {
    Hv <- c(spec$baseline, unlist(spec$time_vary[1:k]),
            if (k > 1) spec$trt[1:(k - 1)])
    X  <- dd[, c(Hv, spec$trt[k]), drop = FALSE]
    use <- alive[, k] & dd[[spec$cens[k]]] == 1 & !is.na(Q)
    m <- discrete_sl(X[use, , drop = FALSE], Q[use], cands)
    chosen[k] <- m$learner
    Xd <- X
    if (spec$trt[k] %in% policy_cols) Xd[[spec$trt[k]]] <- 0
    Qk <- rep(NA_real_, n)
    Qk[alive[, k]] <- m$predict(Xd[alive[, k], , drop = FALSE])
    Q <- Qk
  }
  structure(mean(Q[alive[, 1]]), learners = chosen)
}

# natural course + policies for one built design
gcomp_policies <- function(bd, policy_names, cands = c("glmnet", "ranger")) {
  des <- bd$design
  if (length(des$trt_waves) == 1) policy_names <- "prevent_all"
  out <- data.frame(policy = c("natural", policy_names), est = NA_real_)
  out$est[1] <- ice_gcomp(bd$data, bd$spec, character(0), cands)
  for (i in seq_along(policy_names)) {
    cols <- paste0("A_", policy_waves(des, policy_names[i]))
    out$est[i + 1] <- ice_gcomp(bd$data, bd$spec, cols, cands)
  }
  out$diff_vs_natural <- out$est - out$est[1]
  out
}
