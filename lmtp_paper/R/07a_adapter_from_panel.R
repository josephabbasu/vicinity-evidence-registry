# ------------------------------------------------------------------
# 07a_adapter_from_panel.R
# Converts the objects that already exist in your analysis session into the
# canonical wide file the LMTP pipeline uses.  NO new coding of raw Add Health
# items: it reuses the variables your Papers 2-4 scripts built.
#
#   panel                       long, one row per aid x wave (waves 1-5)
#   biomarkers_panel_long_w456  long, bio waves 4-6: sbp, bmi, med_bp
#   sib_prof                    aid, FAMID   (family id for clustered folds)
#
# Mapping (edit ADAPTER_MAP if your column names differ).  Assumptions that are
# NOT verifiable from the photographed code are marked CHECK.
# ------------------------------------------------------------------
suppressPackageStartupMessages(library(data.table))

ADAPTER_MAP <- list(
  vic = "weapon_victimization",   # >0 -> 1, as in your make_history() set-up (vict)
  perp = "weapon_violence",       # >0 -> 1 (perp)
  wit = "weapon_witnessing",
  dep = "depression",             # CHECK: must be the harmonised 0-9 three-item sum used in Papers 2-3
  age = "age",
  nbhd = "neigh_conc_disadv_raw", # neighbourhood concentrated disadvantage, waves 1-5
  ccrime = "cty_violent_rate_log",# county violent crime (log); used for waves 1-3 only
  pov = "poverty_z",              # CHECK: available for waves 1-5?  higher = more poverty
  sex = "gender", race = "race", race_ref = "white",   # CHECK coding (see as_female / as_minority)
  famconn = "family_connection_baseline",
  schconn = "school_connect_baseline",
  nbcoh   = "nb_cohesion_baseline",
  bio = list(sbp = "sbp", bmi = "bmi", med = "med_bp")
)

to_wave_int <- function(x) {
  map <- c("1" = 1, "2" = 2, "3" = 3, "4" = 4, "5" = 5, "6" = 6,
           "I" = 1, "II" = 2, "III" = 3, "IV" = 4, "V" = 5, "VI" = 6)
  y <- unname(map[as.character(x)])
  if (anyNA(y)) stop(sum(is.na(y)), " rows have unmapped waves. Check the wave column.")
  as.integer(y)
}

as_female <- function(x) {
  if (is.factor(x) || is.character(x)) {
    y <- tolower(trimws(as.character(x)))
    return(ifelse(y %in% c("female", "f", "2"), 1L, ifelse(y %in% c("male", "m", "1"), 0L, NA_integer_)))
  }
  message("NOTE: numeric sex assumed Add Health BIO_SEX coding (1 = male, 2 = female). CHECK.")
  as.integer(x == 2)
}

as_minority <- function(x, ref = "white") {
  if (is.numeric(x)) stop("race is numeric: recode to labels first, or edit as_minority() for your coding.")
  y <- tolower(trimws(as.character(x)))
  out <- as.integer(!grepl(ref, y)); out[is.na(x) | y == ""] <- NA_integer_
  out
}

build_wide_from_panel <- function(panel, bio = NULL, sib = NULL, map = ADAPTER_MAP,
                                  verbose = TRUE) {
  P <- as.data.table(panel)
  need <- c("aid", "wave", map$vic, map$perp, map$dep)
  miss <- setdiff(need, names(P))
  if (length(miss)) stop("panel is missing: ", paste(miss, collapse = ", "))
  P[, aid := as.character(aid)]; P[, wave := to_wave_int(wave)]
  if (anyDuplicated(P[, .(aid, wave)])) stop("panel has duplicate aid x wave rows")
  col <- function(nm) if (!is.null(nm) && nm %in% names(P)) P[[nm]] else rep(NA_real_, nrow(P))

  L <- data.table(aid = P$aid, wave = P$wave,
                  vic  = as.integer(col(map$vic)  > 0),
                  perp = as.integer(col(map$perp) > 0),
                  wit  = as.integer(col(map$wit)  > 0),
                  dep  = as.numeric(col(map$dep)),
                  age  = as.numeric(col(map$age)),
                  nbhd = as.numeric(col(map$nbhd)),
                  ccrime = as.numeric(col(map$ccrime)),
                  pov  = as.numeric(col(map$pov)))
  L[wave > 3, ccrime := NA_real_]            # county crime exists through Wave III only

  if (!is.null(bio)) {
    B <- as.data.table(bio); B[, aid := as.character(aid)]; B[, wave := to_wave_int(wave)]
    bc <- function(nm) if (nm %in% names(B)) as.numeric(B[[nm]]) else rep(NA_real_, nrow(B))
    B2 <- data.table(aid = B$aid, wave = B$wave, sbp = bc(map$bio$sbp),
                     bmi = bc(map$bio$bmi), med = bc(map$bio$med))
    if (anyDuplicated(B2[, .(aid, wave)])) stop("biomarker panel has duplicate aid x wave rows")
    L <- merge(L, B2, by = c("aid", "wave"), all = TRUE)
  } else L[, `:=`(sbp = NA_real_, bmi = NA_real_, med = NA_real_)]

  # earlier-report counts: same definition as your make_history()
  # (.cur0 = coalesce(.cur, 0); count through wave t, NA if no row at t)
  setorder(L, aid, wave)
  L[, cumv := cumsum(fifelse(is.na(vic),  0L, vic)),  by = aid]
  L[, cump := cumsum(fifelse(is.na(perp), 0L, perp)), by = aid]
  L[wave > 5, `:=`(cumv = NA_integer_, cump = NA_integer_)]

  vars <- c("vic", "perp", "wit", "dep", "age", "nbhd", "ccrime", "pov",
            "cumv", "cump", "sbp", "bmi", "med")
  W <- dcast(L, aid ~ wave, value.var = vars, sep = "_")
  keep <- names(W)[vapply(W, function(z) any(!is.na(z)), logical(1)) | names(W) == "aid"]
  W <- W[, ..keep]

  # time-fixed characteristics from each person's first row
  setorder(P, aid, wave)
  first <- P[, .SD[1], by = aid]
  fixed <- data.table(aid = first$aid,
                      female   = as_female(first[[map$sex]]),
                      minority = as_minority(first[[map$race]], map$race_ref))
  base_cols <- c(famconn_base = map$famconn, schconn_base = map$schconn, nbcoh_base = map$nbcoh)
  base_cols <- base_cols[base_cols %in% names(P)]
  if (length(base_cols)) {
    nn <- P[, lapply(.SD, function(z) z[!is.na(z)][1]), by = aid, .SDcols = unname(base_cols)]
    setnames(nn, unname(base_cols), names(base_cols))
    fixed <- merge(fixed, nn, by = "aid", all.x = TRUE)
  }
  W <- merge(W, fixed, by = "aid", all.x = TRUE)
  W[, age1 := if ("age_1" %in% names(W)) age_1 else NA_real_]

  if (!is.null(sib)) {
    S <- as.data.table(sib); setnames(S, tolower(names(S)))
    S <- unique(S[, .(aid = as.character(aid), fam = as.character(famid))])
    W <- merge(W, S, by = "aid", all.x = TRUE)
    W[is.na(fam), fam := aid]
  } else W[, fam := aid]
  W[, id := aid]

  if (verbose) {
    cat(sprintf("wide file: %d persons, %d columns\n", nrow(W), ncol(W)))
    allna <- setdiff(c(paste0(rep(c("vic", "perp", "wit", "dep"), each = 5), "_", 1:5)), names(W))
    if (length(allna)) cat("WARNING: no data for:", paste(allna, collapse = ", "), "\n")
    cat(sprintf("minority share %.2f; female share %.2f\n",
                mean(W$minority, na.rm = TRUE), mean(W$female, na.rm = TRUE)))
  }
  W[]
}
