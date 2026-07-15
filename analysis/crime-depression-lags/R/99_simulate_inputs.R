# Generate synthetic Add Health-like input files for pipeline verification.
# NOT Add Health data. The structural model builds in a known lagged effect
# (TRUE_LAG_BETA, SD units, conditional on prior symptoms) so that
# R/98_validate_recovery.R can confirm the pipeline recovers the truth.
# Run from the analysis root: Rscript R/99_simulate_inputs.R

source("R/00_config.R")
set.seed(20260401)

TRUE_LAG_BETA <- 0.05   # structural effect of crime_z(t) on y(t+1) | y(t)
AR_Y <- 0.45            # autoregression of depressive symptoms
N_PERSONS <- 5000
N_COUNTIES <- 120
N_SCHOOLS <- 132

# --- Counties: AR(1) ln violent rate across 5 calendar waves, poverty
# correlated with crime, urbanicity from population density.
cty <- data.frame(county_fips = sprintf("%05d", sample(1000:56045, N_COUNTIES)))
base_ln <- rnorm(N_COUNTIES, log(450), 0.65)
ln_rate <- matrix(NA, N_COUNTIES, 5)
ln_rate[, 1] <- base_ln
for (w in 2:5) ln_rate[, w] <- log(450) * 0.1 + 0.9 * ln_rate[, w - 1] + rnorm(N_COUNTIES, 0, 0.18)
cty$log_pop_density <- rnorm(N_COUNTIES, 5, 1.6)
cty$urbanicity <- cut(cty$log_pop_density, c(-Inf, 4.2, 6, Inf),
                      labels = c("rural", "suburban", "urban"))
pov_base <- plogis(-1.8 + 0.55 * scale(base_ln)[, 1] - 0.15 * scale(cty$log_pop_density)[, 1] +
                     rnorm(N_COUNTIES, 0, 0.35))

county_crime <- do.call(rbind, lapply(1:3, function(w) {
  data.frame(county_fips = cty$county_fips, wave = w,
             violent_rate = round(exp(ln_rate[, w]) *
                                    runif(N_COUNTIES, 0.97, 1.03), 1),
             county_poverty = round(pmin(pmax(pov_base + rnorm(N_COUNTIES, 0, .01), .02), .55), 3),
             urbanicity = as.character(cty$urbanicity),
             log_pop_density = round(cty$log_pop_density, 2),
             coverage_pct = round(pmin(100, 100 - rexp(N_COUNTIES, 1 / 6)), 1))
}))
write.csv(county_crime, cfg$county_crime_file, row.names = FALSE)

# Crime z-scale used INSIDE the generator (close to, not identical to, the
# pipeline's analytic-sample standardization; validation allows for this).
gen_z <- function(w, idx) (ln_rate[idx, w] - mean(ln_rate[, 1:3])) / sd(ln_rate[, 1:3])

# --- Schools nested in counties; 4 region strata.
sch <- data.frame(psu = sprintf("S%03d", 1:N_SCHOOLS),
                  county_idx = sample(rep(1:N_COUNTIES, length.out = N_SCHOOLS)))
sch$stratum <- sample(c("Northeast", "Midwest", "South", "West"), N_SCHOOLS, TRUE,
                      prob = c(.18, .24, .37, .21))

# --- Persons: covariates, W1 school/county, base sampling weight.
p_school <- sample(1:N_SCHOOLS, N_PERSONS, TRUE)
persons <- data.frame(
  aid = sprintf("A%06d", 1:N_PERSONS),
  psu = sch$psu[p_school],
  stratum = sch$stratum[p_school],
  sex_female = rbinom(N_PERSONS, 1, .51),
  race_eth = sample(c("NHWhite", "NHBlack", "Hispanic", "NHAsian", "NHOther"),
                    N_PERSONS, TRUE, prob = c(.52, .21, .17, .07, .03)),
  parent_educ = sample(c("lt_hs", "hs", "some_college", "college_plus"),
                       N_PERSONS, TRUE, prob = c(.14, .3, .3, .26)),
  family_structure_w1 = sample(c("two_bio", "other"), N_PERSONS, TRUE, prob = c(.55, .45))
)
cnty1 <- sch$county_idx[p_school]
# Income depends on county poverty (observable confounding path: income and
# county poverty affect both residence and symptoms; models adjust for both).
inc <- exp(rnorm(N_PERSONS, 10.6 - 1.4 * pov_base[cnty1], 0.55)) / 1000
persons$log_hh_income_w1 <- round(log(inc), 3)
persons$log_hh_income_w1[runif(N_PERSONS) < .10] <- NA  # item nonresponse
base_wt <- exp(rnorm(N_PERSONS, 0, .35)) *
  ifelse(persons$race_eth %in% c("NHBlack", "NHAsian"), 0.8, 1.1)

age1 <- sample(12:18, N_PERSONS, TRUE)
wave_years <- c(0, 1, 6.5, 13.5, 21.5)  # years since W1 interview

# --- County trajectory: movers change county between waves.
move_prob <- c(NA, .05, .35, .55, .30)
cnty <- matrix(NA_integer_, N_PERSONS, 5); cnty[, 1] <- cnty1
for (w in 2:5) {
  mv <- runif(N_PERSONS) < move_prob[w]
  cnty[, w] <- ifelse(mv, sample(1:N_COUNTIES, N_PERSONS, TRUE), cnty[, w - 1])
}

# --- Depressive symptoms: structural model on a ~z scale.
u <- rnorm(N_PERSONS, 0, .45)
lin_cov <- 0.18 * persons$sex_female - 0.10 * scale(ifelse(is.na(persons$log_hh_income_w1),
                                                           mean(log(inc)), persons$log_hh_income_w1))[, 1] +
  0.12 * (persons$family_structure_w1 == "other") +
  0.55 * pov_base[cnty[, 1]]
y <- matrix(NA_real_, N_PERSONS, 5)
y[, 1] <- 0.05 * gen_z(1, cnty[, 1]) + lin_cov + u + rnorm(N_PERSONS, 0, .8)
for (w in 2:5) {
  lag_effect <- if (w <= 4) TRUE_LAG_BETA * gen_z(w - 1, cnty[, w - 1]) else
    TRUE_LAG_BETA * gen_z(3, cnty[, 3])  # W5: exposure carried from W3 (L4 pair)
  y[, w] <- AR_Y * y[, w - 1] + lag_effect + 0.5 * (1 - AR_Y) * lin_cov +
    (1 - AR_Y) * u + rnorm(N_PERSONS, 0, .8)
}

# --- Participation, weights, and observed CES-D per wave.
part_prob <- cbind(1, .88 - .02 * pmin(pmax(y[, 1], -2), 2),
                   .77 - .02 * pmin(pmax(y[, 2], -2), 2),
                   .80 - .015 * pmin(pmax(y[, 3], -2), 2),
                   .62 - .015 * pmin(pmax(y[, 4], -2), 2))
participates <- sapply(1:5, function(w) runif(N_PERSONS) < part_prob[, w])
participates[age1 >= 18 & seq_len(N_PERSONS) %% 7 == 0, 2] <- FALSE  # W2 excluded most W1 seniors

rows <- list()
for (w in 1:5) {
  idx <- which(participates[, w])
  cesd_full <- pmin(pmax(0.6 + 0.33 * y[idx, w] + rnorm(length(idx), 0, .05), 0), 3)
  cesd_common <- pmin(pmax(cesd_full + rnorm(length(idx), 0, .12), 0), 3)
  cesd_full[runif(length(idx)) < .03] <- NA
  wt <- base_wt[idx] / part_prob[idx, w]
  rows[[w]] <- data.frame(
    aid = persons$aid[idx], wave = w,
    age = age1[idx] + wave_years[w] + round(runif(length(idx), -.3, .3), 1),
    cesd_full = round(cesd_full, 3), cesd_common = round(cesd_common, 3),
    county_fips = cty$county_fips[cnty[idx, w]],
    weight = round(wt / mean(wt) * 1000, 2))
}
person_waves <- do.call(rbind, rows)

write.csv(persons, cfg$persons_file, row.names = FALSE)
write.csv(person_waves, cfg$person_waves_file, row.names = FALSE)
saveRDS(list(true_lag_beta = TRUE_LAG_BETA, ar_y = AR_Y,
             note = "beta on the y scale; observed CES-D is a linear map of y, so the standardized estimand differs from TRUE_LAG_BETA only through scaling/attenuation checked in 98_validate_recovery.R"),
        file.path(cfg$output_dir, "sim_truth.rds"))

cat(sprintf("Simulated inputs written: %d persons, %d person-waves, %d county-waves.\n",
            nrow(persons), nrow(person_waves), nrow(county_crime)))
cat(sprintf("True structural lag effect (y scale): %.3f\n", TRUE_LAG_BETA))
