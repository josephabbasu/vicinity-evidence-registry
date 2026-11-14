# ------------------------------------------------------------------
# 05_fe_benchmark.R
# Within-person (fixed-effects) benchmark so the LMTP estimates can be
# triangulated against the dissertation's association papers.
# Uses fixest if installed; otherwise a base-R within estimator with
# person-clustered standard errors (tested on simulated data).
# ------------------------------------------------------------------
suppressPackageStartupMessages(library(data.table))

to_long <- function(wide, waves = 1:5) {
  W <- as.data.table(wide)
  rows <- lapply(waves, function(t) {
    data.table(id = W$id, fam = W$fam, wave = t,
               dep  = W[[paste0("dep_", t)]],
               vic  = W[[paste0("vic_", t)]],
               perp = W[[paste0("perp_", t)]],
               vic_next  = if (t < max(waves)) W[[paste0("vic_",  t + 1)]] else NA_real_,
               perp_next = if (t < max(waves)) W[[paste0("perp_", t + 1)]] else NA_real_)
  })
  L <- rbindlist(rows)
  setorder(L, id, wave)
  # earlier-report counts use only EARLIER observed waves
  L[, earlier_vic  := shift(cumsum(fifelse(is.na(vic),  0, vic)),  1, fill = 0), by = id]
  L[, earlier_perp := shift(cumsum(fifelse(is.na(perp), 0, perp)), 1, fill = 0), by = id]
  L[, any_next := pmax(vic_next, perp_next)]
  L[]
}

fe_within <- function(L, y, xs) {
  d <- L[stats::complete.cases(L[, c(y, xs), with = FALSE])]
  d <- d[d[, .N, by = id][N >= 2], on = "id"]
  setorder(d, id, wave)
  Wd <- model.matrix(~ 0 + factor(wave), d)[, -1, drop = FALSE]
  X  <- cbind(as.matrix(d[, ..xs]), Wd); yv <- d[[y]]
  gid <- d$id; cnt <- as.numeric(table(factor(gid, levels = unique(gid))))
  idx <- rep(seq_along(cnt), cnt)
  dm  <- function(M) { M <- as.matrix(M); M - (rowsum(M, gid, reorder = FALSE) / cnt)[idx, , drop = FALSE] }
  Xd <- dm(X); yd <- as.numeric(dm(matrix(yv, ncol = 1)))
  keep <- apply(Xd, 2, sd) > 1e-10; Xd <- Xd[, keep, drop = FALSE]
  bread <- solve(crossprod(Xd)); b <- bread %*% crossprod(Xd, yd)
  e <- yd - as.numeric(Xd %*% b)
  S <- rowsum(Xd * e, gid, reorder = FALSE)
  G <- nrow(S); p <- ncol(Xd)
  V <- bread %*% crossprod(S) %*% bread * (G / (G - 1))
  se <- sqrt(diag(V))
  res <- data.frame(term = colnames(Xd), est = as.numeric(b), se = se,
             lo = as.numeric(b) - 1.96 * se, hi = as.numeric(b) + 1.96 * se,
             row.names = NULL)
  res[res$term %in% xs, ]
}

# Association benchmark: past-year vs earlier reports (+ lead placebo)
fe_benchmark <- function(wide, waves = 1:5) {
  L <- to_long(wide, waves)
  main <- fe_within(L, "dep", c("vic", "earlier_vic", "perp", "earlier_perp"))
  plc  <- fe_within(L[!is.na(any_next)], "dep", c("vic", "earlier_vic", "perp", "earlier_perp", "any_next"))
  list(main = main, lead_placebo = plc[plc$term == "any_next", ])
}
