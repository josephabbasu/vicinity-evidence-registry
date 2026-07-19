# Estimation helpers. Base R only (lm/stats) so this runs inside a locked-down
# secure-enclave R install with no CRAN access. If `fixest` happens to be
# installed, a couple of convenience wrappers will use it for speed and nicer
# output on large panels -- but nothing here *requires* it.

#' Cluster-robust (CR1) variance-covariance matrix for an `lm` fit.
#' Standard Cameron-Gelbach-Miller small-sample-corrected sandwich estimator,
#' implemented directly so this has zero package dependencies.
#'
#' @param cluster a vector of cluster ids, positionally aligned with the rows
#'   of `stats::model.matrix(fit)` (i.e. same length and row order as the
#'   model frame actually used in estimation, after listwise deletion). This
#'   is what `fit_and_tidy()` constructs via `match()` before calling here.
vcov_cluster <- function(fit, cluster) {
  X <- stats::model.matrix(fit)
  if (length(cluster) != nrow(X)) {
    stop("`cluster` must be positionally aligned with the fitted model's rows ",
         "(", length(cluster), " cluster values vs. ", nrow(X), " model rows).",
         call. = FALSE)
  }
  cluster <- droplevels(as.factor(cluster))

  u <- stats::residuals(fit)
  n <- nrow(X)
  k <- ncol(X)
  m <- nlevels(cluster)

  meat <- matrix(0, k, k)
  for (g in levels(cluster)) {
    idx <- which(cluster == g)
    Xg <- X[idx, , drop = FALSE]
    ug <- u[idx]
    score_g <- crossprod(Xg, ug)
    meat <- meat + tcrossprod(score_g)
  }

  bread <- solve(crossprod(X))
  dfc <- (m / (m - 1)) * ((n - 1) / (n - k))
  vcov <- dfc * (bread %*% meat %*% bread)
  dimnames(vcov) <- list(colnames(X), colnames(X))
  attr(vcov, "n_clusters") <- m
  vcov
}

#' Tidy a fitted lm with cluster-robust (or model-default) SEs into a
#' data.frame: term, estimate, std.error, statistic, p.value, conf.low/high.
tidy_lm <- function(fit, cluster = NULL, conf_level = 0.95) {
  b <- stats::coef(fit)
  if (!is.null(cluster)) {
    V <- vcov_cluster(fit, cluster)
    se <- sqrt(diag(V))
    df <- attr(V, "n_clusters") - 1
  } else {
    V <- stats::vcov(fit)
    se <- sqrt(diag(V))
    df <- fit$df.residual
  }
  common <- intersect(names(b), names(se))
  b <- b[common]; se <- se[common]
  stat <- b / se
  p <- 2 * stats::pt(-abs(stat), df = df)
  crit <- stats::qt(1 - (1 - conf_level) / 2, df = df)

  data.frame(
    term = names(b),
    estimate = unname(b),
    std.error = unname(se),
    statistic = unname(stat),
    df = df,
    p.value = unname(p),
    conf.low = unname(b - crit * se),
    conf.high = unname(b + crit * se),
    row.names = NULL
  )
}

#' Fit `formula` on `data` and return a tidy data.frame, optionally with
#' cluster-robust SEs. Silently drops rows with missing values in any model
#' variable (standard listwise deletion via lm's default na.action), and
#' reports how many rows were used vs. available.
fit_and_tidy <- function(formula, data, cluster_var = NULL, label = "") {
  fit <- stats::lm(formula, data = data)
  n_used <- stats::nobs(fit)
  n_avail <- nrow(data)
  if (n_used < n_avail) {
    message(sprintf("[%s] used %d of %d rows (listwise deletion on model variables).",
                     label, n_used, n_avail))
  }
  cluster <- if (!is.null(cluster_var)) {
    used_rows <- rownames(stats::model.frame(fit))
    data[[cluster_var]][match(used_rows, rownames(data))]
  } else NULL
  out <- tidy_lm(fit, cluster = cluster)
  out$model_label <- label
  out$n_obs <- n_used
  attr(out, "fit") <- fit
  out
}

#' Benjamini-Hochberg FDR correction across a set of per-biomarker p-values,
#' applied within a named term (e.g. correct across the 10-12 biomarker
#' models' coefficient on cum_crime_exposure_z, not across every coefficient
#' in every model). Safe to call repeatedly for different terms on the same
#' table -- it only overwrites the rows matching `term_name`, preserving any
#' correction already applied to other terms.
add_fdr_correction <- function(results, term_name) {
  if (!"p.adj_BH" %in% names(results)) results$p.adj_BH <- NA_real_
  target <- results$term == term_name
  results$p.adj_BH[target] <- stats::p.adjust(results$p.value[target], method = "BH")
  results
}

#' Family/within-group demeaning -- used both for sibling fixed effects
#' (group = family id) and as a manual fallback for individual fixed effects
#' when only two waves exist per person (equivalent to first-differencing,
#' but written generally in case a future 3+ biomarker-wave panel is used).
demean_by_group <- function(data, vars, group_var) {
  d <- data
  for (v in vars) {
    grp_mean <- ave(d[[v]], d[[group_var]], FUN = function(x) mean(x, na.rm = TRUE))
    d[[paste0(v, "_dm")]] <- d[[v]] - grp_mean
  }
  d
}
