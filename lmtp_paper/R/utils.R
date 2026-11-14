# ------------------------------------------------------------------
# utils.R -- helpers and the time-ordering guard
# ------------------------------------------------------------------
expit <- function(x) 1 / (1 + exp(-x))

wave_of <- function(v) {
  # trailing integer of names like dep_3 ; NA for time-fixed variables
  m <- regmatches(v, regexpr("[0-9]+$", v))
  out <- rep(NA_integer_, length(v))
  out[grepl("[0-9]+$", v)] <- as.integer(m)
  out
}

# Variable families that may be measured at the treatment wave itself
# (slow-moving area context, deterministic age).
.ctx_family <- c("cdis", "ccrime", "nbhd", "age")
family_of <- function(v) sub("_[0-9]+$", "", v)

# Stops if any covariate in a block is measured after it is allowed to be.
#   post mode: dep/vic/perp/wit/bmi/sbp must come from waves <= w-1
#   pre  mode: dep/bmi/sbp/med may also come from wave w (same wave)
#   context/age: waves <= w
#   baseline : waves <= first treatment wave - 2 (earlier history)
#   outcome  : wave > last treatment wave
check_time_ordering <- function(spec, trt_waves, timing = "post") {
  K <- length(trt_waves)
  for (k in seq_len(K)) {
    w  <- trt_waves[k]
    v  <- spec$time_vary[[k]]
    wv <- wave_of(v); fam <- family_of(v)
    allowed <- ifelse(fam %in% .ctx_family, w,
               ifelse(timing == "pre" & fam %in% c("dep", "bmi", "sbp", "med"), w, w - 1))
    bad <- v[!is.na(wv) & wv > allowed]
    if (length(bad))
      stop(sprintf("Time-ordering violation in block %d (treatment wave %d): %s",
                   k, w, paste(bad, collapse = ", ")), call. = FALSE)
  }
  b  <- spec$baseline; wb <- wave_of(b)
  badb <- b[!is.na(wb) & wb > trt_waves[1] - 2]
  if (length(badb))
    stop("Baseline contains variables too close to / after first exposure: ",
         paste(badb, collapse = ", "), call. = FALSE)
  if (wave_of(spec$outcome) <= max(trt_waves))
    stop("Outcome ", spec$outcome, " is not measured after the last treatment wave.",
         call. = FALSE)
  invisible(TRUE)
}

fmt_ci <- function(est, lo, hi, d = 3)
  sprintf(paste0("%.", d, "f (%.", d, "f, %.", d, "f)"), est, lo, hi)
