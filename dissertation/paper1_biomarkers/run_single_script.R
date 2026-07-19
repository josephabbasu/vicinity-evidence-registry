# Paper 1 biomarker model -- single-file version.
# Assumes `panel` is already loaded in your R session (long format, one row
# per person-wave, key columns aid/wave). Paste this whole thing in and run.
# Base R only -- no packages needed.

stopifnot(exists("panel"))
id_var <- "aid"; wave_var <- "wave"

## ---- 1. Allostatic-load outcome: count of al_risk_* flags + z composite --
al_vars <- grep("^al_risk_", names(panel), value = TRUE)
z_vars  <- c("z_log_crp","z_log_il6","z_glucose","z_hbalc","z_tg",
             "z_hdl","z_non_hdl","z_sbp","z_dbp","z_bmi")
z_vars  <- intersect(z_vars, names(panel))

stopifnot(length(al_vars) > 0, length(z_vars) > 0)

al_mat <- as.matrix(panel[al_vars]); storage.mode(al_mat) <- "double"
panel$AL_count <- ifelse(rowSums(!is.na(al_mat)) == 0, NA,
                          rowSums(al_mat, na.rm = TRUE))

z_mat <- as.matrix(panel[z_vars]); storage.mode(z_mat) <- "double"
n_z <- rowSums(!is.na(z_mat))
panel$AL_zmean <- ifelse(n_z == 0, NA, rowSums(z_mat, na.rm = TRUE) / n_z)

## ---- 2. Which waves have biomarkers? --------------------------------------
bio_waves <- sort(unique(panel[[wave_var]][!is.na(panel$AL_count)]))
message("Biomarker waves detected: ", paste(bio_waves, collapse = ", "))

## ---- 3. Cumulative exposure through the wave cutoffs ----------------------
# County violent crime usable through wave 3; self-reported violence/
# victimization usable through wave 5. Adjust the two cutoffs below if wrong.
crime_wave_cutoff <- 3
vict_wave_cutoff   <- 5

last_through <- function(var, cutoff) {
  sub <- panel[panel[[wave_var]] <= cutoff & !is.na(panel[[var]]), c(id_var, wave_var, var)]
  sub <- sub[order(sub[[id_var]], sub[[wave_var]]), ]
  sub[!duplicated(sub[[id_var]], fromLast = TRUE), c(id_var, var)]
}

crime_tbl <- last_through("violent_cum_log", crime_wave_cutoff)      # cumulative county crime
vict_tbl  <- last_through("violent_exp_total_cum_log", vict_wave_cutoff)  # cumulative victimization

exposure_tbl <- merge(crime_tbl, vict_tbl, by = id_var, all = TRUE)
names(exposure_tbl)[names(exposure_tbl) == "violent_cum_log"] <- "cum_crime_exposure"
names(exposure_tbl)[names(exposure_tbl) == "violent_exp_total_cum_log"] <- "cum_violence_exposure"
exposure_tbl$cum_crime_exposure_z    <- as.numeric(scale(exposure_tbl$cum_crime_exposure))
exposure_tbl$cum_violence_exposure_z <- as.numeric(scale(exposure_tbl$cum_violence_exposure))

## ---- 4. Model A: cumulative adolescent exposure -> first biomarker wave --
first_wave <- panel[panel[[wave_var]] %in% bio_waves, ]
first_wave <- first_wave[order(first_wave[[id_var]], first_wave[[wave_var]]), ]
first_wave <- first_wave[!duplicated(first_wave[[id_var]]), ]

bio_first <- merge(first_wave, exposure_tbl, by = id_var, all.x = TRUE)

covs <- intersect(c("gender", "race", "birth_year", "age"), names(bio_first))
form_a <- as.formula(paste("AL_count ~ cum_crime_exposure_z + cum_violence_exposure_z",
                            if (length(covs)) paste(c("", covs), collapse = " + ") else ""))
fit_a_count <- lm(form_a, data = bio_first)

form_a_z <- as.formula(paste("AL_zmean ~ cum_crime_exposure_z + cum_violence_exposure_z",
                              if (length(covs)) paste(c("", covs), collapse = " + ") else ""))
fit_a_zmean <- lm(form_a_z, data = bio_first)

## ---- 5. Model B: within-person change (needs >=2 biomarker waves/person) --
bio_change <- NULL
if (length(bio_waves) >= 2) {
  sub <- panel[panel[[wave_var]] %in% bio_waves,
               c(id_var, wave_var, "AL_count", "AL_zmean", "violent_interwave_log", "violent_exp_total_cum_log")]
  sub <- sub[order(sub[[id_var]], sub[[wave_var]]), ]
  by_person <- split(sub, sub[[id_var]])
  diffs <- lapply(by_person, function(p) {
    if (nrow(p) < 2) return(NULL)
    data.frame(
      aid = p[[id_var]][-1],
      d_AL_count  = diff(p$AL_count),
      d_AL_zmean  = diff(p$AL_zmean),
      d_crime_exposure    = diff(p$violent_interwave_log),
      d_violence_exposure = diff(p$violent_exp_total_cum_log)
    )
  })
  bio_change <- do.call(rbind, diffs)

  fit_b_count <- lm(d_AL_count ~ d_crime_exposure + d_violence_exposure, data = bio_change)
  fit_b_zmean <- lm(d_AL_zmean ~ d_crime_exposure + d_violence_exposure, data = bio_change)
} else {
  message("Only 1 biomarker wave detected -- Model B (within-person change) needs >=2 and is skipped.")
}

## ---- 6. Cluster-robust SEs (clustered by person) --------------------------
# Small hand-rolled CR1 sandwich estimator -- no `sandwich`/`fixest` needed.
# `data` must be the *original* (pre-listwise-deletion) data frame the model
# was fit on, so rows dropped for missingness are matched by row name rather
# than by position -- fitting on a subset with different missingness than
# `data`'s row order would otherwise silently misassign cluster ids.
cluster_se <- function(fit, data, id_col) {
  X <- model.matrix(fit)
  used_rows <- rownames(fit$model)
  cl <- droplevels(as.factor(data[[id_col]][match(used_rows, rownames(data))]))
  u <- residuals(fit); k <- ncol(X); m <- nlevels(cl)
  meat <- matrix(0, k, k)
  for (g in levels(cl)) {
    idx <- which(cl == g)
    s <- crossprod(X[idx, , drop = FALSE], u[idx])
    meat <- meat + tcrossprod(s)
  }
  bread <- solve(crossprod(X))
  dfc <- (m / (m - 1)) * ((nrow(X) - 1) / (nrow(X) - k))
  V <- dfc * (bread %*% meat %*% bread)
  se <- sqrt(diag(V))
  b <- coef(fit)[colnames(X)]
  data.frame(term = names(b), estimate = b, cluster_se = se,
             t = b / se, p_value = 2 * pt(-abs(b / se), df = m - 1),
             row.names = NULL)
}

## ---- 7. Results -------------------------------------------------------
cat("\n===== Model A: AL_count ~ cumulative adolescent exposure (n =", nobs(fit_a_count), ") =====\n")
print(cluster_se(fit_a_count, bio_first, id_var))

cat("\n===== Model A: AL_zmean ~ cumulative adolescent exposure (n =", nobs(fit_a_zmean), ") =====\n")
print(cluster_se(fit_a_zmean, bio_first, id_var))

if (!is.null(bio_change)) {
  cat("\n===== Model B: change in AL_count ~ change in exposure (within-person, n =", nobs(fit_b_count), ") =====\n")
  print(cluster_se(fit_b_count, bio_change, "aid"))

  cat("\n===== Model B: change in AL_zmean ~ change in exposure (within-person, n =", nobs(fit_b_zmean), ") =====\n")
  print(cluster_se(fit_b_zmean, bio_change, "aid"))
}
