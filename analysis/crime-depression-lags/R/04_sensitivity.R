# Pre-specified sensitivity analyses S1-S7 (SAP section 6). All are
# complete-case survey-weighted fits unless noted; the MI-vs-CC contrast itself
# is sensitivity S3.
# Run from the analysis root: Rscript R/04_sensitivity.R

source("R/00_config.R")
suppressPackageStartupMessages({ library(survey); library(lme4) })
options(survey.lonely.psu = "adjust")

panel <- readRDS(file.path(cfg$output_dir, "panel.rds"))
pair_data <- panel$pair_data

covar_rhs <- paste(c("age_out", cfg$person_covariates,
                     "county_poverty", "urbanicity", "log_pop_density"),
                   collapse = " + ")
base_f <- paste("cesd_z_out ~ crime_z + cesd_z_exp +", covar_rhs)

fit_cc <- function(f, d, term = "crime_z", label, estimand) {
  f <- as.formula(f)
  vars <- unique(c(intersect(all.vars(f), names(d)), "weight_out", "psu", "stratum"))
  cc <- d[complete.cases(d[, vars]), vars]
  if (nrow(cc) < 50 || length(unique(cc$psu)) < 3) {
    return(data.frame(analysis = label, estimand = estimand, n = nrow(cc),
                      beta = NA, se = NA, ci_lo = NA, ci_hi = NA, p = NA,
                      note = "insufficient sample"))
  }
  des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~weight_out,
                   data = cc, nest = TRUE)
  fit <- svyglm(f, design = des)
  est <- coef(fit)[term]; se <- sqrt(diag(vcov(fit)))[term]
  dfree <- max(degf(des) - length(coef(fit)) + 1, 1)
  data.frame(analysis = label, estimand = estimand, n = nrow(cc),
             beta = est, se = se,
             ci_lo = est - qt(.975, dfree) * se, ci_hi = est + qt(.975, dfree) * se,
             p = 2 * pt(-abs(est / se), dfree), note = "", row.names = NULL)
}

res <- list()
lag_names <- c("L1", "L2", "L3", "L4")

# S1: pooled lagged person-pairs with elapsed-time interaction (formal decay
# test, H3). Person-pairs stack across L1-L4; SEs clustered by person via
# svydesign ids = ~aid (persons cross pairs), weights = outcome-wave weight.
stacked <- do.call(rbind, lapply(lag_names, function(nm) {
  d <- pair_data[[nm]]
  vars <- unique(c(all.vars(as.formula(base_f)), "aid", "weight_out"))
  d <- d[, intersect(vars, names(d))]
  d$years <- cfg$elapsed_years[[nm]]
  d
}))
stacked <- stacked[complete.cases(stacked), ]
stacked$years_c <- stacked$years - mean(stacked$years)
des_s1 <- svydesign(ids = ~aid, weights = ~weight_out, data = stacked)
f_s1 <- as.formula(paste("cesd_z_out ~ crime_z * years_c + cesd_z_exp +", covar_rhs))
fit_s1 <- svyglm(f_s1, design = des_s1)
for (term in c("crime_z", "crime_z:years_c")) {
  est <- coef(fit_s1)[term]; se <- sqrt(diag(vcov(fit_s1)))[term]
  dfree <- max(degf(des_s1) - length(coef(fit_s1)) + 1, 1)
  res[[paste0("S1_", term)]] <- data.frame(
    analysis = "S1 pooled lag x elapsed years (clustered by person)",
    estimand = term, n = nrow(stacked), beta = est, se = se,
    ci_lo = est - qt(.975, dfree) * se, ci_hi = est + qt(.975, dfree) * se,
    p = 2 * pt(-abs(est / se), dfree), note = "", row.names = NULL)
}

# S2: common-item CES-D outcome and baseline (measurement non-invariance).
f_s2 <- paste("cesd_common_z_out ~ crime_z + cesd_common_z_exp +", covar_rhs)
for (nm in lag_names)
  res[[paste0("S2_", nm)]] <- fit_cc(f_s2, pair_data[[nm]],
                                     label = "S2 common-item CES-D", estimand = nm)

# S3: complete-case main models (contrast with MI results in table_2).
for (nm in lag_names)
  res[[paste0("S3_", nm)]] <- fit_cc(base_f, pair_data[[nm]],
                                     label = "S3 complete case", estimand = nm)

# S4: same-county restriction and mover-adjusted model.
for (nm in c("L1", "L2", "L3")) {
  d <- pair_data[[nm]]
  res[[paste0("S4a_", nm)]] <- fit_cc(base_f, d[d$same_county == 1, ],
                                      label = "S4a same-county only", estimand = nm)
  res[[paste0("S4b_", nm)]] <- fit_cc(paste(base_f, "+ same_county"), d,
                                      label = "S4b mover-adjusted", estimand = nm)
}

# S5: UCR agency-coverage restriction (only if coverage data provided).
if ("coverage_pct" %in% names(pair_data$L1)) {
  for (nm in c("L1", "L2", "L3")) {
    d <- pair_data[[nm]]
    res[[paste0("S5_", nm)]] <- fit_cc(
      base_f, d[!is.na(d$coverage_pct) & d$coverage_pct >= cfg$coverage_threshold, ],
      label = sprintf("S5 UCR coverage >= %d%%", cfg$coverage_threshold), estimand = nm)
  }
}

# S6: county random-intercept mixed model (unweighted), exposure-level
# clustering beyond the school PSU.
for (nm in c("L1", "L2", "L3")) {
  d <- pair_data[[nm]]
  vars <- unique(c(all.vars(as.formula(base_f)), "county_fips_exp"))
  cc <- d[complete.cases(d[, intersect(vars, names(d))]), ]
  f_s6 <- as.formula(paste(base_f, "+ (1 | county_fips_exp)"))
  fit <- lmer(f_s6, data = cc, REML = TRUE)
  est <- fixef(fit)["crime_z"]; se <- sqrt(diag(as.matrix(vcov(fit))))["crime_z"]
  dfree <- length(unique(cc$county_fips_exp)) - 1
  res[[paste0("S6_", nm)]] <- data.frame(
    analysis = "S6 county random intercept (unweighted)", estimand = nm,
    n = nrow(cc), beta = est, se = se,
    ci_lo = est - qt(.975, dfree) * se, ci_hi = est + qt(.975, dfree) * se,
    p = 2 * pt(-abs(est / se), dfree), note = "df = counties - 1", row.names = NULL)
}

# S7: drop county poverty (bounding the deprivation-adjustment effect).
f_s7 <- paste("cesd_z_out ~ crime_z + cesd_z_exp +",
              paste(c("age_out", cfg$person_covariates, "urbanicity", "log_pop_density"),
                    collapse = " + "))
for (nm in c("L1", "L2", "L3"))
  res[[paste0("S7_", nm)]] <- fit_cc(f_s7, pair_data[[nm]],
                                     label = "S7 no deprivation adjustment", estimand = nm)

sens <- do.call(rbind, res)
sens[, c("beta", "se", "ci_lo", "ci_hi")] <- round(sens[, c("beta", "se", "ci_lo", "ci_hi")], 4)
sens$p <- signif(sens$p, 3)
cfg$assert_disclosure_safe(sens)
write.csv(sens, file.path(cfg$output_dir, "table_3_sensitivity.csv"), row.names = FALSE)
saveRDS(sens, file.path(cfg$output_dir, "sensitivity_results.rds"))
cat("Sensitivity analyses written to table_3_sensitivity.csv\n")
print(sens[, c("analysis", "estimand", "n", "beta", "ci_lo", "ci_hi", "p")], row.names = FALSE)
