# Descriptives: analytic-sample table per estimand, exposure distribution,
# attrition comparison (exposure-wave characteristics of retained vs lost).
# Run from the analysis root: Rscript R/02_descriptives.R

source("R/00_config.R")

panel <- readRDS(file.path(cfg$output_dir, "panel.rds"))
pw <- panel$person_waves
pair_data <- panel$pair_data

# --- Sample sizes and key variable summaries per lag-pair estimand
desc <- do.call(rbind, lapply(names(pair_data), function(nm) {
  d <- pair_data[[nm]]
  crime_col <- if ("crime_z" %in% names(d)) d$crime_z else d$crime_cum_z
  data.frame(
    estimand = nm,
    n = nrow(d),
    crime_z_mean = round(mean(crime_col, na.rm = TRUE), 3),
    crime_z_sd = round(sd(crime_col, na.rm = TRUE), 3),
    cesd_out_missing_pct = round(100 * mean(is.na(d$cesd_z_out)), 1),
    same_county_pct = if ("same_county" %in% names(d))
      round(100 * mean(d$same_county, na.rm = TRUE), 1) else NA,
    stringsAsFactors = FALSE
  )
}))
cfg$assert_disclosure_safe(desc)
write.csv(desc, file.path(cfg$output_dir, "table_S1_analytic_samples.csv"), row.names = FALSE)

# --- Exposure distribution per wave (raw rate and z), county- and person-level
exp_desc <- do.call(rbind, lapply(cfg$exposure_waves, function(w) {
  pv <- pw[pw$wave == w & !is.na(pw$violent_rate), ]
  data.frame(wave = w,
             n_counties = length(unique(pv$county_fips)),
             person_rate_mean = round(mean(pv$violent_rate), 1),
             person_rate_sd = round(sd(pv$violent_rate), 1),
             person_rate_median = round(median(pv$violent_rate), 1),
             person_crime_z_mean = round(mean(pv$crime_z), 3))
}))
cfg$assert_disclosure_safe(exp_desc)
write.csv(exp_desc, file.path(cfg$output_dir, "table_S2_exposure_by_wave.csv"), row.names = FALSE)

# --- Attrition: exposure-wave characteristics of pair-retained vs lost persons
attr_rows <- list()
for (nm in names(cfg$lag_pairs)) {
  p <- cfg$lag_pairs[[nm]]
  base <- pw[pw$wave == p["exposure"] & !is.na(pw$crime_z), ]
  base$retained <- base$aid %in% pair_data[[nm]]$aid
  for (v in c("cesd_z", "crime_z", "log_hh_income_w1")) {
    m1 <- mean(base[[v]][base$retained], na.rm = TRUE)
    m0 <- mean(base[[v]][!base$retained], na.rm = TRUE)
    attr_rows[[paste(nm, v)]] <- data.frame(
      estimand = nm, variable = v,
      retained_mean = round(m1, 3), lost_mean = round(m0, 3),
      std_diff = round((m1 - m0) / sd(base[[v]], na.rm = TRUE), 3),
      n_retained = sum(base$retained), n_lost = sum(!base$retained))
  }
}
attrition <- do.call(rbind, attr_rows)
cfg$assert_disclosure_safe(attrition)
write.csv(attrition, file.path(cfg$output_dir, "table_S3_attrition.csv"), row.names = FALSE)

cat("Descriptives written: table_S1_analytic_samples.csv, table_S2_exposure_by_wave.csv, table_S3_attrition.csv\n")
