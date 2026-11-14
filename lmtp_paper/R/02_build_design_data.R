# ------------------------------------------------------------------
# 02_build_design_data.R
# Turns the canonical wide file into the structure LMTP needs:
#   baseline  ->  L_1, A_1  ->  C_1  ->  L_2, A_2  ->  ...  ->  C_K -> Y
# and enforces the time-ordering rules (see utils.R::check_time_ordering).
# ------------------------------------------------------------------
source_if <- function(f) if (!exists("check_time_ordering")) source(f)
source_if("R/utils.R")

make_exposure <- function(W, w, exposure = "any") {
  v <- W[[paste0("vic_", w)]]; p <- W[[paste0("perp_", w)]]
  switch(exposure,
         any  = ifelse(!is.na(v) & v == 1 | !is.na(p) & p == 1, 1,
                       ifelse(is.na(v) | is.na(p), NA_real_, 0)),
         vic  = v,
         perp = p,
         stop("exposure must be any, vic or perp"))
}

ctx_names <- function(w) paste0(c("cdis_", "ccrime_", "nbhd_"), w)   # whichever exist in the data

# covariates measured BEFORE the exposure of treatment wave w
tv_names <- function(w, timing, avail) {
  p <- w - 1
  v <- character(0)
  if (p >= 1) v <- c(v, paste0(c("dep", "vic", "perp", "wit", "bmi", "sbp", "med", "pov", "cumv", "cump"), "_", p))
  v <- c(v, ctx_names(w), paste0("age_", w))
  if (timing == "pre") v <- c(v, paste0(c("dep", "bmi", "sbp", "med"), "_", w))
  intersect(v, avail)
}

baseline_names <- function(w1, avail) {
  b <- c("female", "minority", "ses", "age1")
  if (w1 - 2 >= 1) for (s in 1:(w1 - 2))
    b <- c(b, paste0(c("dep", "vic", "perp", "wit", "cdis", "ccrime", "nbhd", "pov", "cumv", "cump"), "_", s))
  b <- c(b, "famconn_base", "schconn_base", "nbcoh_base")   # adolescent social resources, if present
  intersect(b, avail)
}

build_design <- function(wide, design, exposure = "any", timing = "post",
                         verbose = TRUE) {
  W   <- as.data.frame(wide)
  tw  <- design$trt_waves; K <- length(tw)
  avail <- names(W)
  for (w in tw) W[[paste0("A_", w)]] <- make_exposure(W, w, exposure)
  trt <- paste0("A_", tw)

  base <- baseline_names(tw[1], avail)
  tv <- lapply(tw, tv_names, timing = timing, avail = avail)
  # drop all-NA columns and duplicates across blocks
  seen <- base
  for (k in seq_len(K)) {
    tv[[k]] <- setdiff(tv[[k]], seen)
    tv[[k]] <- tv[[k]][vapply(tv[[k]], function(v) any(!is.na(W[[v]])), logical(1))]
    seen <- c(seen, tv[[k]])
  }
  spec <- list(trt = trt, outcome = design$outcome, baseline = base,
               time_vary = tv, cens = paste0("C_", seq_len(K)), id = "fam")
  check_time_ordering(spec, tw, timing)

  # censoring indicators: 1 = next block (A_{k+1}, L_{k+1}) / outcome observed
  C <- matrix(1L, nrow(W), K)
  for (k in seq_len(K)) {
    C[, k] <- if (k < K) {
      as.integer(!is.na(W[[trt[k + 1]]]) &
                 stats::complete.cases(W[, tv[[k + 1]], drop = FALSE]))
    } else as.integer(!is.na(W[[design$outcome]]))
  }
  C <- t(apply(C, 1, cumprod))                       # monotone
  if (K == 1) C <- matrix(C, ncol = 1)
  for (k in seq_len(K)) W[[spec$cens[k]]] <- C[, k]
  # blank out blocks after censoring (what is truly unobserved)
  for (k in seq_len(K - 1)) {
    gone <- C[, k] == 0
    W[gone, c(trt[k + 1], tv[[k + 1]])] <- NA
  }
  W[[design$outcome]][C[, K] == 0] <- NA

  # eligibility: complete baseline, first block and first exposure
  elig <- stats::complete.cases(W[, c(base, tv[[1]], trt[1]), drop = FALSE])
  dd <- W[elig, c("id", "fam", base, unlist(tv), trt, spec$cens, design$outcome)]
  dd <- dd[, !duplicated(names(dd))]
  if (verbose) {
    cat(sprintf("[%s | exposure=%s | timing=%s] eligible n=%d; censored: %s; exposed share: %s\n",
        design$label, exposure, timing, nrow(dd),
        paste(sprintf("C%d=%.1f%%", seq_len(K), 100 * (1 - colMeans(dd[spec$cens]))), collapse = " "),
        paste(sprintf("%s=%.1f%%", trt, 100 * colMeans(dd[trt], na.rm = TRUE)), collapse = " ")))
  }
  list(data = dd, spec = spec, timing = timing, design = design)
}
