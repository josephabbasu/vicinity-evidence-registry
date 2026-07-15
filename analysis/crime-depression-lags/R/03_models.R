# Primary and secondary models (SAP sections 4.1-4.3).
#   L1-L3: lag-pair conditional-change models, survey-weighted, MI-pooled.
#   L4, L5a, L5b: secondary (long lag; cumulative adolescent exposure).
#   C1: contemporaneous within-person fixed-effects model, W1-W3.
# Run from the analysis root: Rscript R/03_models.R

source("R/00_config.R")
suppressPackageStartupMessages({
  library(survey)
  library(mitools)
  if (cfg$mi_m > 0) library(mice)
})
options(survey.lonely.psu = "adjust")

panel <- readRDS(file.path(cfg$output_dir, "panel.rds"))
pair_data <- panel$pair_data

covar_rhs <- paste(c("age_out", cfg$person_covariates,
                     "county_poverty", "urbanicity", "log_pop_density"),
                   collapse = " + ")

model_specs <- list(
  L1  = list(f = paste("cesd_z_out ~ crime_z + cesd_z_exp +", covar_rhs), tier = "primary"),
  L2  = list(f = paste("cesd_z_out ~ crime_z + cesd_z_exp +", covar_rhs), tier = "primary"),
  L3  = list(f = paste("cesd_z_out ~ crime_z + cesd_z_exp +", covar_rhs), tier = "primary"),
  L4  = list(f = paste("cesd_z_out ~ crime_z + cesd_z_exp +", covar_rhs), tier = "secondary"),
  L5a = list(f = paste("cesd_z_out ~ crime_cum_z + cesd_z_w1 +", covar_rhs), tier = "secondary"),
  L5b = list(f = paste("cesd_z_out ~ crime_cum_z + cesd_z_w1 +", covar_rhs), tier = "secondary")
)

model_vars <- function(f, d) {
  v <- intersect(all.vars(as.formula(f)), names(d))
  unique(c(v, "weight_out", "psu", "stratum"))
}

# Fit one survey-weighted model; with MI, impute -> fit per imputation -> pool
# (Rubin's rules via mitools::MIcombine). Imputed outcomes are excluded from the
# analysis model (MI-then-delete), per SAP section 5.
fit_pair <- function(name, spec, d) {
  f <- as.formula(spec$f)
  exposure_term <- if ("crime_z" %in% all.vars(f)) "crime_z" else "crime_cum_z"
  vars <- model_vars(spec$f, d)
  dd <- d[, vars]

  if (cfg$mi_m > 0 && anyNA(dd[, setdiff(vars, c("weight_out", "psu", "stratum"))])) {
    pred_vars <- setdiff(vars, c("weight_out", "psu", "stratum"))
    imp_data <- dd[, pred_vars]
    imp_data[] <- lapply(imp_data, function(x) if (is.character(x)) factor(x) else x)
    imp <- mice::mice(imp_data, m = cfg$mi_m, seed = cfg$mi_seed, printFlag = FALSE)
    fits <- lapply(seq_len(cfg$mi_m), function(i) {
      ci <- mice::complete(imp, i)
      ci$weight_out <- dd$weight_out; ci$psu <- dd$psu; ci$stratum <- dd$stratum
      ci <- ci[!is.na(dd$cesd_z_out), ]                      # MI-then-delete
      des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~weight_out,
                       data = ci, nest = TRUE)
      svyglm(f, design = des)
    })
    pooled <- mitools::MIcombine(fits)
    est <- coef(pooled)[exposure_term]
    se <- sqrt(diag(vcov(pooled)))[exposure_term]
    dfree <- pooled$df[names(coef(pooled)) == exposure_term]
    n_used <- sum(!is.na(dd$cesd_z_out))
    method <- sprintf("svyglm + MI (m=%d), Rubin's rules", cfg$mi_m)
  } else {
    cc <- dd[complete.cases(dd), ]
    des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~weight_out,
                     data = cc, nest = TRUE)
    fit <- svyglm(f, design = des)
    est <- coef(fit)[exposure_term]
    se <- sqrt(diag(vcov(fit)))[exposure_term]
    dfree <- degf(des) - length(coef(fit)) + 1
    n_used <- nrow(cc)
    method <- "svyglm, complete case"
  }

  tstat <- est / se
  p <- 2 * pt(-abs(tstat), df = max(dfree, 1))
  data.frame(estimand = name, tier = spec$tier, exposure = exposure_term,
             n = n_used, beta = est, se = se,
             ci_lo = est - qt(.975, max(dfree, 1)) * se,
             ci_hi = est + qt(.975, max(dfree, 1)) * se,
             p = p, method = method, row.names = NULL)
}

results <- do.call(rbind, lapply(names(model_specs), function(nm) {
  cat(sprintf("Fitting %s ...\n", nm))
  fit_pair(nm, model_specs[[nm]], pair_data[[nm]])
}))

# Benjamini-Hochberg q-values across the lagged estimands L1-L4 (SAP 4.4).
lag_idx <- results$estimand %in% c("L1", "L2", "L3", "L4")
results$q_bh <- NA_real_
results$q_bh[lag_idx] <- p.adjust(results$p[lag_idx], method = "BH")

# --- C1: contemporaneous within-person fixed effects, W1-W3 panel -----------
pw <- panel$person_waves
cpanel <- pw[pw$wave %in% cfg$exposure_waves &
               !is.na(pw$crime_z) & !is.na(pw$cesd_z) &
               !is.na(pw$county_poverty) & !is.na(pw$age), ]
cpanel <- cpanel[cpanel$aid %in% names(which(table(cpanel$aid) >= 2)), ]

# Within-person demeaning (within estimator), wave dummies kept in the design.
demean <- function(x, id) x - ave(x, id)
fe <- data.frame(
  aid = cpanel$aid,
  y = demean(cpanel$cesd_z, cpanel$aid),
  crime = demean(cpanel$crime_z, cpanel$aid),
  age = demean(cpanel$age, cpanel$aid),
  ctypov = demean(cpanel$county_poverty, cpanel$aid),
  w2 = demean(as.numeric(cpanel$wave == 2), cpanel$aid),
  w3 = demean(as.numeric(cpanel$wave == 3), cpanel$aid)
)
fe_fit <- lm(y ~ crime + age + ctypov + w2 + w3 - 1, data = fe)

# Cluster-robust (CR1) SEs by person, with df corrected for the absorbed
# person intercepts (N - G - k).
cluster_se <- function(fit, cluster) {
  X <- model.matrix(fit); u <- residuals(fit)
  Xu <- rowsum(X * u, group = cluster)
  meat <- crossprod(Xu)
  bread <- solve(crossprod(X))
  G <- length(unique(cluster)); N <- nrow(X); k <- ncol(X)
  adj <- (G / (G - 1)) * ((N - 1) / (N - k))
  sqrt(diag(adj * bread %*% meat %*% bread))
}
fe_se <- cluster_se(fe_fit, fe$aid)["crime"]
fe_beta <- coef(fe_fit)["crime"]
fe_df <- nrow(fe) - length(unique(fe$aid)) - length(coef(fe_fit))
fe_p <- 2 * pt(-abs(fe_beta / fe_se), df = fe_df)
results <- rbind(results, data.frame(
  estimand = "C1", tier = "contemporaneous", exposure = "crime_z",
  n = nrow(fe), beta = fe_beta, se = fe_se,
  ci_lo = fe_beta - qt(.975, fe_df) * fe_se,
  ci_hi = fe_beta + qt(.975, fe_df) * fe_se,
  p = fe_p, method = "person fixed effects (within), CR1 by person, unweighted",
  q_bh = NA_real_, row.names = NULL))

results[, c("beta", "se", "ci_lo", "ci_hi")] <-
  round(results[, c("beta", "se", "ci_lo", "ci_hi")], 4)
results$p <- signif(results$p, 3)
results$q_bh <- signif(results$q_bh, 3)

cfg$assert_disclosure_safe(results)
write.csv(results, file.path(cfg$output_dir, "table_2_main_results.csv"), row.names = FALSE)
saveRDS(results, file.path(cfg$output_dir, "main_results.rds"))
cat("\nMain results (exposure coefficients, SD units):\n")
print(results[, c("estimand", "tier", "n", "beta", "se", "ci_lo", "ci_hi", "p", "q_bh")],
      row.names = FALSE)
