# Build the analysis panel: harmonized CES-D, standardized crime exposure,
# covariates, and one analytic dataset per lag-pair estimand.
#
# Inputs (see README for schemas): persons.csv, person_waves.csv, county_crime.csv
# Output: output/panel.rds  (list: person_waves, pair_data, standards)

# Run from the analysis root: Rscript R/01_build_panel.R
source("R/00_config.R")

persons <- read.csv(cfg$persons_file, stringsAsFactors = FALSE)
pw <- read.csv(cfg$person_waves_file, stringsAsFactors = FALSE)
crime <- read.csv(cfg$county_crime_file, stringsAsFactors = FALSE)

stopifnot(
  all(c("aid", "psu", "stratum", cfg$person_covariates) %in% names(persons)),
  all(c("aid", "wave", "age", "cesd_full", "cesd_common", "county_fips", "weight") %in% names(pw)),
  all(c("county_fips", "wave", "violent_rate", cfg$county_covariates) %in% names(crime))
)
stopifnot(!anyDuplicated(persons$aid), !anyDuplicated(pw[, c("aid", "wave")]),
          !anyDuplicated(crime[, c("county_fips", "wave")]))

# --- Exposure: ln(violent rate + 1), z-standardized against the pooled W1-W3
# person-wave distribution (one fixed scale so 1 unit = 1 SD of adolescent
# exposure in every model).
crime$ln_violent <- log(crime$violent_rate + 1)
pw <- merge(pw, crime, by = c("county_fips", "wave"), all.x = TRUE)

exp_rows <- pw$wave %in% cfg$exposure_waves & !is.na(pw$ln_violent)
crime_mean <- mean(pw$ln_violent[exp_rows])
crime_sd <- sd(pw$ln_violent[exp_rows])
pw$crime_z <- (pw$ln_violent - crime_mean) / crime_sd

# --- Outcome: CES-D z-standardized within wave (analytic person-waves with a
# valid score). cesd_full / cesd_common arrive as mean item scores computed in
# data prep under the >=80% answered rule (see README).
zscore_by_wave <- function(x, wave) {
  out <- rep(NA_real_, length(x))
  for (w in sort(unique(wave))) {
    i <- wave == w & !is.na(x)
    out[i] <- (x[i] - mean(x[i])) / sd(x[i])
  }
  out
}
pw$cesd_z <- zscore_by_wave(pw$cesd_full, pw$wave)
pw$cesd_common_z <- zscore_by_wave(pw$cesd_common, pw$wave)

pw <- merge(pw, persons, by = "aid")

# --- Cumulative adolescent exposure (secondary estimand L5): person mean of
# available W1-W3 crime_z, requiring >= 2 exposure waves observed.
adol <- pw[pw$wave %in% cfg$exposure_waves & !is.na(pw$crime_z), c("aid", "crime_z")]
cum <- aggregate(crime_z ~ aid, data = adol, FUN = mean)
names(cum)[2] <- "crime_cum_z"
n_exp <- aggregate(crime_z ~ aid, data = adol, FUN = length)
cum$n_exposure_waves <- n_exp$crime_z
cum <- cum[cum$n_exposure_waves >= 2, c("aid", "crime_cum_z")]

# --- Build one dataset per lag pair: exposure-wave row variables suffixed _exp,
# outcome-wave suffixed _out. Same-county indicator supports sensitivity S4.
build_pair <- function(exposure_wave, outcome_wave) {
  e <- pw[pw$wave == exposure_wave,
          c("aid", "crime_z", "cesd_z", "cesd_common_z", "county_fips",
            "county_poverty", "urbanicity", "log_pop_density", "age",
            if ("coverage_pct" %in% names(pw)) "coverage_pct")]
  names(e) <- c("aid", "crime_z", "cesd_z_exp", "cesd_common_z_exp", "county_fips_exp",
                "county_poverty", "urbanicity", "log_pop_density", "age_exp",
                if ("coverage_pct" %in% names(pw)) "coverage_pct")
  o <- pw[pw$wave == outcome_wave,
          c("aid", "cesd_z", "cesd_common_z", "county_fips", "age", "weight",
            "psu", "stratum", cfg$person_covariates)]
  names(o)[2:6] <- c("cesd_z_out", "cesd_common_z_out", "county_fips_out", "age_out", "weight_out")
  d <- merge(e, o, by = "aid")
  # Eligibility: interviewed at both waves with a valid outcome-wave weight and
  # observed exposure. Item-missing covariates/outcome are handled by MI.
  d <- d[!is.na(d$weight_out) & !is.na(d$crime_z), ]
  d$same_county <- as.integer(d$county_fips_exp == d$county_fips_out)
  d
}

pair_data <- lapply(cfg$lag_pairs, function(p) build_pair(p["exposure"], p["outcome"]))

# --- Cumulative-exposure datasets (L5a: W4 outcome, L5b: W5 outcome), baseline
# adjustment = W1 CES-D.
build_cum <- function(outcome_wave) {
  base <- pw[pw$wave == 1, c("aid", "cesd_z", "county_poverty", "urbanicity",
                             "log_pop_density")]
  names(base)[2] <- "cesd_z_w1"
  o <- pw[pw$wave == outcome_wave,
          c("aid", "cesd_z", "age", "weight", "psu", "stratum", cfg$person_covariates)]
  names(o)[2:4] <- c("cesd_z_out", "age_out", "weight_out")
  d <- merge(merge(cum, base, by = "aid"), o, by = "aid")
  d[!is.na(d$weight_out), ]
}
pair_data$L5a <- build_cum(4)
pair_data$L5b <- build_cum(5)

standards <- list(crime_mean = crime_mean, crime_sd = crime_sd)
saveRDS(list(person_waves = pw, pair_data = pair_data, standards = standards),
        file.path(cfg$output_dir, "panel.rds"))

cat("Panel built.\n")
cat(sprintf("Person-waves: %d | Persons: %d\n", nrow(pw), length(unique(pw$aid))))
for (nm in names(pair_data)) cat(sprintf("  %s: n = %d\n", nm, nrow(pair_data[[nm]])))
