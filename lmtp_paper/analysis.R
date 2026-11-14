# ==================================================================
# analysis.R -- counterfactual (LMTP) analysis of preventing weapon involvement
#
# USE: in the RStudio session that already holds these objects, run
#        source("analysis.R")
#   panel                        long, aid x wave (1-5): weapon_victimization,
#                                weapon_violence, weapon_witnessing, depression, age,
#                                gender, race, neigh_conc_disadv_raw, cty_violent_rate_log,
#                                poverty_z, *_baseline social-resource columns
#   biomarkers_panel_long_w456   long, waves 4-6: sbp, bmi, med_bp
#   sib_prof                     aid, FAMID  (optional; clusters = families)
# NEEDS: data.table, lmtp (+ the learner packages it asks for)
# OUTPUT: output/lmtp_mean_outcomes.csv, output/lmtp_contrasts.csv
# ==================================================================
suppressPackageStartupMessages(library(data.table))

# ---- 1. CONFIG (pre-register these) -------------------------------
CFG <- list(
  exposure = "any",               # "any" (victimization or perpetration), "vic", "perp"
  timings  = c("post", "pre"),    # same-wave ordering assumption; report both
  designs  = list(                # outcome must be measured AFTER the last treatment wave
    dep_III_IV = list(outcome = "dep_5", trt_waves = c(3, 4)),
    sbp_IV     = list(outcome = "sbp_5", trt_waves = 4),
    sbp_IV_V   = list(outcome = "sbp_6", trt_waves = c(4, 5))),
  policies = c("prevent_all", "prevent_first", "prevent_last"),
  folds = 5, k = Inf, seed = 20260101, out_dir = "output")

# your column names (CHECK the ones marked)
MAP <- list(vic = "weapon_victimization", perp = "weapon_violence", wit = "weapon_witnessing",
            dep = "depression",                       # CHECK: harmonised 0-9 sum
            age = "age", nbhd = "neigh_conc_disadv_raw",
            ccrime = "cty_violent_rate_log",          # waves 1-3 only
            pov = "poverty_z",                        # CHECK: all waves?
            sex = "gender", race = "race", race_ref = "white",   # CHECK coding
            famconn = "family_connection_baseline", schconn = "school_connect_baseline",
            nbcoh = "nb_cohesion_baseline",
            bio = list(sbp = "sbp", bmi = "bmi", med = "med_bp"))

policy_waves <- function(design, policy) {
  tw <- design$trt_waves
  switch(policy, prevent_all = tw, prevent_first = tw[1], prevent_last = tw[length(tw)],
         stop("unknown policy: ", policy))
}

# ---- 2. YOUR OBJECTS -> ONE WIDE FILE (vic_1..., dep_1..., sbp_4...) -
to_wave_int <- function(x) {
  m <- c("1" = 1, "2" = 2, "3" = 3, "4" = 4, "5" = 5, "6" = 6,
         "I" = 1, "II" = 2, "III" = 3, "IV" = 4, "V" = 5, "VI" = 6)
  y <- unname(m[as.character(x)])
  if (anyNA(y)) stop(sum(is.na(y)), " rows have unmapped waves")
  as.integer(y)
}
as_female <- function(x) {
  if (is.factor(x) || is.character(x)) {
    y <- tolower(trimws(as.character(x)))
    return(ifelse(y %in% c("female", "f", "2"), 1L, ifelse(y %in% c("male", "m", "1"), 0L, NA_integer_)))
  }
  message("NOTE: numeric sex assumed 1 = male, 2 = female. CHECK.")
  as.integer(x == 2)
}
as_minority <- function(x, ref) {
  if (is.numeric(x)) stop("race is numeric: recode to labels or edit as_minority()")
  y <- tolower(trimws(as.character(x)))
  out <- as.integer(!grepl(ref, y)); out[is.na(x) | y == ""] <- NA_integer_; out
}

build_wide <- function(panel, bio, sib) {
  P <- as.data.table(panel)
  miss <- setdiff(c("aid", "wave", MAP$vic, MAP$perp, MAP$dep), names(P))
  if (length(miss)) stop("panel is missing: ", paste(miss, collapse = ", "))
  P[, aid := as.character(aid)]; P[, wave := to_wave_int(wave)]
  if (anyDuplicated(P[, .(aid, wave)])) stop("duplicate aid x wave rows in panel")
  col <- function(nm) if (!is.null(nm) && nm %in% names(P)) P[[nm]] else rep(NA_real_, nrow(P))

  L <- data.table(aid = P$aid, wave = P$wave,
                  vic = as.integer(col(MAP$vic) > 0), perp = as.integer(col(MAP$perp) > 0),
                  wit = as.integer(col(MAP$wit) > 0), dep = as.numeric(col(MAP$dep)),
                  age = as.numeric(col(MAP$age)), nbhd = as.numeric(col(MAP$nbhd)),
                  ccrime = as.numeric(col(MAP$ccrime)), pov = as.numeric(col(MAP$pov)))
  L[wave > 3, ccrime := NA_real_]

  B <- as.data.table(bio); B[, aid := as.character(aid)]; B[, wave := to_wave_int(wave)]
  bc <- function(nm) if (nm %in% names(B)) as.numeric(B[[nm]]) else rep(NA_real_, nrow(B))
  B2 <- data.table(aid = B$aid, wave = B$wave, sbp = bc(MAP$bio$sbp),
                   bmi = bc(MAP$bio$bmi), med = bc(MAP$bio$med))
  if (anyDuplicated(B2[, .(aid, wave)])) stop("duplicate aid x wave rows in biomarker panel")
  L <- merge(L, B2, by = c("aid", "wave"), all = TRUE)

  # earlier-report counts, same definition as make_history(): cumsum(current, NA -> 0)
  setorder(L, aid, wave)
  L[, cumv := cumsum(fifelse(is.na(vic),  0L, vic)),  by = aid]
  L[, cump := cumsum(fifelse(is.na(perp), 0L, perp)), by = aid]
  L[wave > 5, `:=`(cumv = NA_integer_, cump = NA_integer_)]

  W <- dcast(L, aid ~ wave, sep = "_", value.var = c("vic", "perp", "wit", "dep", "age", "nbhd",
                                                     "ccrime", "pov", "cumv", "cump", "sbp", "bmi", "med"))
  keep <- names(W)[vapply(W, function(z) any(!is.na(z)), logical(1)) | names(W) == "aid"]
  W <- W[, ..keep]

  setorder(P, aid, wave); first <- P[, .SD[1], by = aid]
  fixed <- data.table(aid = first$aid, female = as_female(first[[MAP$sex]]),
                      minority = as_minority(first[[MAP$race]], MAP$race_ref))
  bcols <- c(famconn_base = MAP$famconn, schconn_base = MAP$schconn, nbcoh_base = MAP$nbcoh)
  bcols <- bcols[bcols %in% names(P)]
  if (length(bcols)) {
    nn <- P[, lapply(.SD, function(z) z[!is.na(z)][1]), by = aid, .SDcols = unname(bcols)]
    setnames(nn, unname(bcols), names(bcols)); fixed <- merge(fixed, nn, by = "aid", all.x = TRUE)
  }
  W <- merge(W, fixed, by = "aid", all.x = TRUE)
  W[, age1 := age_1]
  if (!is.null(sib)) {
    S <- as.data.table(sib); setnames(S, tolower(names(S)))
    S <- unique(S[, .(aid = as.character(aid), fam = as.character(famid))])
    W <- merge(W, S, by = "aid", all.x = TRUE); W[is.na(fam), fam := aid]
  } else W[, fam := aid]
  W[, id := aid]
  cat(sprintf("wide file: %d persons, %d columns\n", nrow(W), ncol(W)))
  W[]
}

# ---- 3. LMTP DATA STRUCTURE + TIME-ORDERING GUARD ------------------
# per treatment wave w, covariates measured BEFORE the exposure: waves <= w-1,
# plus area context and age at w.  'pre' also allows same-wave dep/bmi/sbp/med.
wave_of   <- function(v) { w <- suppressWarnings(as.integer(sub(".*_", "", v)))
                          w[!grepl("_[0-9]+$", v)] <- NA_integer_; w }
family_of <- function(v) sub("_[0-9]+$", "", v)

check_time_ordering <- function(spec, tw, timing) {
  for (k in seq_along(tw)) {
    v <- spec$time_vary[[k]]; fam <- family_of(v)
    allowed <- ifelse(fam %in% c("cdis", "ccrime", "nbhd", "age"), tw[k],
               ifelse(timing == "pre" & fam %in% c("dep", "bmi", "sbp", "med"), tw[k], tw[k] - 1))
    bad <- v[!is.na(wave_of(v)) & wave_of(v) > allowed]
    if (length(bad)) stop(sprintf("Time-ordering violation (treatment wave %d): %s", tw[k],
                                  paste(bad, collapse = ", ")), call. = FALSE)
  }
  b <- spec$baseline
  if (any(!is.na(wave_of(b)) & wave_of(b) > tw[1] - 2)) stop("baseline contains too-recent variables")
  if (wave_of(spec$outcome) <= max(tw)) stop("outcome must follow the last treatment wave")
}

build_design <- function(wide, design, exposure, timing) {
  W <- as.data.frame(wide); tw <- design$trt_waves; K <- length(tw); avail <- names(W)
  for (w in tw) {
    v <- W[[paste0("vic_", w)]]; p <- W[[paste0("perp_", w)]]
    W[[paste0("A_", w)]] <- switch(exposure,
      any = ifelse(!is.na(v) & v == 1 | !is.na(p) & p == 1, 1, ifelse(is.na(v) | is.na(p), NA_real_, 0)),
      vic = v, perp = p, stop("exposure must be any, vic or perp"))
  }
  trt <- paste0("A_", tw)

  lagged <- c("dep", "vic", "perp", "wit", "bmi", "sbp", "med", "pov", "cumv", "cump")
  tv <- lapply(tw, function(w) {
    v <- c(if (w > 1) paste0(lagged, "_", w - 1), paste0(c("cdis_", "ccrime_", "nbhd_"), w), paste0("age_", w))
    if (timing == "pre") v <- c(v, paste0(c("dep", "bmi", "sbp", "med"), "_", w))
    intersect(v, avail)
  })
  base <- c("female", "minority", "age1", "famconn_base", "schconn_base", "nbcoh_base")
  if (tw[1] - 2 >= 1) for (s in 1:(tw[1] - 2))
    base <- c(base, paste0(c("dep", "vic", "perp", "wit", "ccrime", "nbhd", "pov", "cumv", "cump"), "_", s))
  base <- intersect(base, avail); seen <- base
  for (k in seq_len(K)) {                     # drop duplicates across blocks and all-NA columns
    tv[[k]] <- setdiff(tv[[k]], seen)
    tv[[k]] <- tv[[k]][vapply(tv[[k]], function(v) any(!is.na(W[[v]])), logical(1))]
    seen <- c(seen, tv[[k]])
  }
  spec <- list(trt = trt, outcome = design$outcome, baseline = base, time_vary = tv,
               cens = paste0("C_", seq_len(K)), id = "fam")
  check_time_ordering(spec, tw, timing)

  # C_k = 1 if the next block (A, covariates) / the outcome is observed; monotone
  C <- sapply(seq_len(K), function(k) if (k < K)
    as.integer(!is.na(W[[trt[k + 1]]]) & complete.cases(W[, tv[[k + 1]], drop = FALSE]))
    else as.integer(!is.na(W[[design$outcome]])))
  C <- matrix(C, nrow(W), K); C <- t(apply(C, 1, cumprod)); if (K == 1) C <- matrix(C, ncol = 1)
  for (k in seq_len(K)) W[[spec$cens[k]]] <- C[, k]
  for (k in seq_len(K - 1)) W[C[, k] == 0, c(trt[k + 1], tv[[k + 1]])] <- NA
  W[[design$outcome]][C[, K] == 0] <- NA

  elig <- complete.cases(W[, c(base, tv[[1]], trt[1]), drop = FALSE])
  dd <- W[elig, c("id", "fam", base, unlist(tv), trt, spec$cens, design$outcome)]
  dd <- dd[, !duplicated(names(dd))]
  cat(sprintf("[%s | %s | %s] eligible n=%d\n", design$outcome, exposure, timing, nrow(dd)))
  list(data = dd, spec = spec, design = design)
}

# P(exposed) by wave and prior involvement: inspect BEFORE fitting
positivity_table <- function(bd) {
  dd <- bd$data; trt <- bd$spec$trt
  do.call(rbind, lapply(seq_along(trt), function(k) {
    a <- dd[[trt[k]]]
    prev <- if (k > 1) dd[[trt[k - 1]]] else {
      cv <- paste0(c("vic_", "perp_"), bd$design$trt_waves[1] - 1)
      if (all(cv %in% names(dd))) pmax(dd[[cv[1]]], dd[[cv[2]]]) else rep(NA_real_, nrow(dd))
    }
    f <- function(m) { m <- m & !is.na(a); data.frame(n = sum(m), exposed = sum(a[m] == 1)) }
    r <- rbind(cbind(trt = trt[k], stratum = "all", f(rep(TRUE, nrow(dd)))),
               cbind(trt = trt[k], stratum = "prior=0", f(!is.na(prev) & prev == 0)),
               cbind(trt = trt[k], stratum = "prior=1", f(!is.na(prev) & prev == 1)))
    r$flag <- ifelse(r$exposed < 30 & r$n > 0, "FEW EXPOSED", ""); r
  }))
}

# ---- 4. LMTP ESTIMATION (targeted, double-robust, super learner) ----
make_shift <- function(cols) { force(cols)
  function(data, trt) if (trt %in% cols) rep(0, nrow(data)) else data[[trt]] }

learners <- function() {                       # learner names differ by lmtp version
  v <- utils::packageVersion("lmtp")
  if (v >= "1.4.0") c("mean", "glm", "glmnet", "ranger") else c("SL.mean", "SL.glm", "SL.glmnet", "SL.ranger")
}
one <- function(f) data.frame(theta = f$theta, se = f$standard_error, lo = f$low, hi = f$high)
contrast <- function(a, b) { v <- lmtp::lmtp_contrast(a, ref = b, type = "additive")
  v <- if (is.null(v$vals)) v$estimates else v$vals
  data.frame(diff = v$theta, se = v$std.error, lo = v$conf.low, hi = v$conf.high, p = v$p.value) }

fit_design <- function(bd) {
  dd <- bd$data; sp <- bd$spec; des <- bd$design; L <- learners()
  pol <- if (length(des$trt_waves) == 1) "prevent_all" else CFG$policies
  args <- list(data = dd, trt = sp$trt, outcome = sp$outcome, baseline = sp$baseline,
               time_vary = sp$time_vary, cens = sp$cens, k = CFG$k, outcome_type = "continuous",
               id = sp$id, learners_outcome = L, learners_trt = L, folds = CFG$folds)
  set.seed(CFG$seed)
  fits <- list(natural = do.call(lmtp::lmtp_tmle, c(args, list(shift = NULL))))
  for (p in pol) fits[[p]] <- do.call(lmtp::lmtp_tmle,
    c(args, list(shift = make_shift(paste0("A_", policy_waves(des, p))))))
  est <- do.call(rbind, lapply(names(fits), function(n) cbind(policy = n, one(fits[[n]]))))
  ctr <- do.call(rbind, lapply(pol, function(p)
    cbind(contrast = paste(p, "- natural"), contrast(fits[[p]], fits$natural))))
  if (all(c("prevent_first", "prevent_last") %in% pol))        # the timing contrast
    ctr <- rbind(ctr, cbind(contrast = "prevent_first - prevent_last",
                            contrast(fits$prevent_first, fits$prevent_last)))
  list(estimates = est, contrasts = ctr)
}

# ---- 5. RUN ---------------------------------------------------------
if (!(exists("panel") && exists("biomarkers_panel_long_w456")))
  stop("Create `panel` and `biomarkers_panel_long_w456` (and optionally `sib_prof`) first.")
wide <- build_wide(panel, biomarkers_panel_long_w456, if (exists("sib_prof")) sib_prof else NULL)

est <- ctr <- list()
for (dn in names(CFG$designs)) for (tm in CFG$timings) {
  bd <- build_design(wide, CFG$designs[[dn]], CFG$exposure, tm)
  print(positivity_table(bd))
  r <- fit_design(bd)
  tag <- data.frame(design = dn, timing = tm, exposure = CFG$exposure)
  est[[length(est) + 1]] <- cbind(tag, r$estimates)
  ctr[[length(ctr) + 1]] <- cbind(tag, r$contrasts)
}
est <- do.call(rbind, est); ctr <- do.call(rbind, ctr)
ctr$diff_ci <- sprintf("%.3f (%.3f, %.3f)", ctr$diff, ctr$lo, ctr$hi)
dir.create(CFG$out_dir, showWarnings = FALSE)
write.csv(est, file.path(CFG$out_dir, "lmtp_mean_outcomes.csv"), row.names = FALSE)
write.csv(ctr, file.path(CFG$out_dir, "lmtp_contrasts.csv"),     row.names = FALSE)
print(ctr[, c("design", "timing", "contrast", "diff_ci", "p")], row.names = FALSE)
