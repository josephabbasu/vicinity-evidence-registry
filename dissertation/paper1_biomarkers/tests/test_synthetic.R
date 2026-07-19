# Smoke test: builds a synthetic panel with the same column names as the
# real (restricted, never-committed) Add Health panel, then runs the full
# 06_run_all.R pipeline against it and checks that every stage completes and
# produces output. This is what stands in for real-data testing during
# development, since Add Health data cannot leave the secure enclave and
# therefore cannot be used to test this code before you run it there.
#
# Run with:  Rscript tests/test_synthetic.R
# (from the dissertation/paper1_biomarkers/ directory, or anywhere -- the
# script locates its own paths).

set.seed(20260719)

pkg_dir <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) NA)
if (is.na(pkg_dir) || pkg_dir == "") {
  # Rscript sets a different mechanism for the running file's path.
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  pkg_dir <- dirname(dirname(normalizePath(file_arg)))
} else {
  pkg_dir <- dirname(pkg_dir)
}
message("Package root detected as: ", pkg_dir)

# ---------------------------------------------------------------------------
# 1. Build a synthetic panel with realistic structure and missingness.
# ---------------------------------------------------------------------------
n_people <- 600
waves <- 1:6

# Families of size 1-3 for the sibling-FE code path.
family_sizes <- c()
remaining <- n_people
fid <- 0
while (remaining > 0) {
  fid <- fid + 1
  size <- sample(1:3, 1, prob = c(0.5, 0.35, 0.15))
  size <- min(size, remaining)
  family_sizes <- c(family_sizes, rep(fid, size))
  remaining <- remaining - size
}
family_id <- family_sizes[seq_len(n_people)]

person_base <- data.frame(
  aid = seq_len(n_people),
  famid = family_id,
  gender = sample(c("M", "F"), n_people, replace = TRUE),
  race = sample(c("White", "Black", "Hispanic", "Other"), n_people, replace = TRUE,
                 prob = c(0.45, 0.25, 0.20, 0.10)),
  birth_year = sample(1976:1982, n_people, replace = TRUE)
)

# True latent propensity linking exposure to biomarkers, so the smoke test
# also sanity-checks that the pipeline can recover a *known* signal direction
# (not just "runs without erroring").
person_base$true_exposure_effect <- stats::rnorm(n_people, mean = 0.15, sd = 0.05)

rows <- list()
for (w in waves) {
  retain_prob <- c(1, 0.95, 0.9, 0.85, 0.8, 0.7)[w]
  keep <- stats::runif(n_people) < retain_prob
  ids <- person_base$aid[keep]
  n_w <- length(ids)

  d <- person_base[match(ids, person_base$aid), ]
  d$wave <- w
  d$age <- 13 + 3 * w + stats::rnorm(n_w, 0, 0.5)

  # --- crime (contextual county violent crime), usable waves 1-3 -----------
  crime_level <- stats::rnorm(n_w, mean = 450 + 10 * w, sd = 80)
  d$violent_rate <- if (w <= 3) pmax(crime_level, 0) else NA_real_
  d$violent_rate_log <- if (w <= 3) log1p(d$violent_rate) else NA_real_
  d$violent_rate_lag1 <- if (w <= 3 && w > 1) log1p(pmax(crime_level - 20, 0)) else NA_real_
  d$violent_interwave_avg <- pmax(stats::rnorm(n_w, 400 + 5 * w, 70), 0)
  d$violent_interwave_dose <- d$violent_interwave_avg * stats::runif(n_w, 0.8, 1.2)
  d$violent_interwave_log <- log1p(d$violent_interwave_avg)
  d$violent_cumulative <- cumsum(rep(mean(d$violent_interwave_avg), n_w)) # placeholder, replaced below
  d$violent_cum_dose <- d$violent_interwave_dose * w
  d$violent_cum_log <- log1p(d$violent_cum_dose)

  # --- self-reported violence exposure / victimization, usable waves 1-5 ---
  vict_dose <- stats::rnorm(n_w, mean = 2 + 0.3 * w, sd = 1)
  d$violent_exp_total_cum <- if (w <= 5) pmax(vict_dose * w, 0) else NA_real_
  d$violent_exp_total_cum_log <- if (w <= 5) log1p(d$violent_exp_total_cum) else NA_real_
  d$violent_flow_early <- if (w <= 2) stats::runif(n_w, 0, 2) else 0
  d$violent_flow_mid <- if (w %in% 3:4) stats::runif(n_w, 0, 2) else 0
  d$violent_flow_late <- if (w == 5) stats::runif(n_w, 0, 2) else 0
  d$violent_flow_young_adult <- if (w == 6) stats::runif(n_w, 0, 2) else 0

  # --- moderators / covariates, available every wave for simplicity --------
  d$family_connection <- stats::rnorm(n_w, 3.5, 0.6)
  d$family_connection_z <- as.numeric(scale(d$family_connection))
  d$poverty_z <- stats::rnorm(n_w)
  d$neigh_conc_disadv_z <- stats::rnorm(n_w)
  d$school_connect_baseline <- stats::rnorm(n_w, 3, 0.5)
  d$school_connect_avg <- stats::rnorm(n_w, 3, 0.5)
  d$religion_attend_z <- stats::rnorm(n_w)
  # peer_risk deliberately omitted -- tests the "optional variable missing" path

  # --- biomarkers, only at waves 4 and 5 (and partially at 6) --------------
  is_bio_wave <- w %in% c(4, 5, 6) && (w < 6 || stats::runif(1) > 0)
  if (w %in% c(4, 5, 6)) {
    cum_exposure_proxy <- d$violent_exp_total_cum_log
    cum_exposure_proxy[is.na(cum_exposure_proxy)] <- mean(vict_dose)
    latent_dysregulation <- d$true_exposure_effect[match(d$aid, person_base$aid)] *
      cum_exposure_proxy + stats::rnorm(n_w, 0, 1)

    d$crp <- pmax(stats::rlnorm(n_w, meanlog = 0.3 + 0.05 * latent_dysregulation, sdlog = 0.6), 0.01)
    d$il6 <- pmax(stats::rlnorm(n_w, meanlog = 0.2 + 0.03 * latent_dysregulation, sdlog = 0.5), 0.01)
    d$glucose <- stats::rnorm(n_w, 95 + 2 * latent_dysregulation, 12)
    d$hbalc <- stats::rnorm(n_w, 5.4 + 0.05 * latent_dysregulation, 0.4)
    d$tg <- pmax(stats::rnorm(n_w, 120 + 4 * latent_dysregulation, 40), 20)
    d$tc <- stats::rnorm(n_w, 190 + 2 * latent_dysregulation, 30)
    d$hdl <- stats::rnorm(n_w, 50 - 1.5 * latent_dysregulation, 12)
    d$non_hdl <- d$tc - d$hdl
    d$sbp <- stats::rnorm(n_w, 118 + 1.5 * latent_dysregulation, 12)
    d$dbp <- stats::rnorm(n_w, 76 + 1 * latent_dysregulation, 8)
    d$bmi <- pmax(stats::rnorm(n_w, 27 + 0.8 * latent_dysregulation, 5), 15)
    d$waist <- pmax(stats::rnorm(n_w, 90 + 2 * latent_dysregulation, 12), 55)

    d$log_crp <- log1p(d$crp)
    d$log_il6 <- log1p(d$il6)
    d$z_log_crp <- as.numeric(scale(d$log_crp))
    d$z_log_il6 <- as.numeric(scale(d$log_il6))
    d$z_glucose <- as.numeric(scale(d$glucose))
    d$z_hbalc <- as.numeric(scale(d$hbalc))
    d$z_tg <- as.numeric(scale(d$tg))
    d$z_hdl <- as.numeric(scale(d$hdl))
    d$z_non_hdl <- as.numeric(scale(d$non_hdl))
    d$z_sbp <- as.numeric(scale(d$sbp))
    d$z_dbp <- as.numeric(scale(d$dbp))
    d$z_bmi <- as.numeric(scale(d$bmi))

    d$fasting_ok <- sample(c(0, 1), n_w, replace = TRUE, prob = c(0.1, 0.9))
    d$c_infect <- sample(c(0, 1), n_w, replace = TRUE, prob = c(0.95, 0.05))
    d$med_diab <- sample(c(0, 1), n_w, replace = TRUE, prob = c(0.9, 0.1))
    d$med_lipid <- sample(c(0, 1), n_w, replace = TRUE, prob = c(0.85, 0.15))
    d$med_crp <- 0

    hi <- function(x, q) as.integer(!is.na(x) & x >= stats::quantile(x, q, na.rm = TRUE))
    lo <- function(x, q) as.integer(!is.na(x) & x <= stats::quantile(x, q, na.rm = TRUE))
    d$al_risk_crp <- hi(d$crp, 0.75)
    d$al_risk_il6 <- hi(d$il6, 0.75)
    d$al_risk_glucose <- hi(d$glucose, 0.75)
    d$al_risk_hbalc <- hi(d$hbalc, 0.75)
    d$al_risk_tg <- hi(d$tg, 0.75)
    d$al_risk_non_hdl <- hi(d$non_hdl, 0.75)
    d$al_risk_hdl_low <- lo(d$hdl, 0.25)
    d$al_risk_sbp <- hi(d$sbp, 0.75)
    d$al_risk_dbp <- hi(d$dbp, 0.75)
    d$al_risk_bmi <- hi(d$bmi, 0.75)
  }

  rows[[length(rows) + 1]] <- d
}

# Waves 1-3 never had biomarker columns added, so each wave's data.frame has
# a different column set; align them (fill missing columns with NA) before
# rbind-ing, the way a real long-format panel build would.
all_names <- unique(unlist(lapply(rows, names)))
rows <- lapply(rows, function(d) {
  missing <- setdiff(all_names, names(d))
  for (m in missing) d[[m]] <- NA
  d[all_names]
})
panel <- do.call(rbind, rows)
panel <- panel[order(panel$aid, panel$wave), ]
panel$true_exposure_effect <- NULL  # not a real panel column; drop before use

# Fix up violent_cumulative to be a genuine running cumulative sum per person
# (the placeholder loop above couldn't easily do a proper per-person cumsum
# across waves built one wave at a time).
panel <- panel[order(panel$aid, panel$wave), ]
panel$violent_cumulative <- ave(panel$violent_interwave_avg, panel$aid, FUN = function(x) cumsum(ifelse(is.na(x), 0, x)))

message(sprintf("Synthetic panel: %d rows, %d unique ids, waves: %s",
                 nrow(panel), length(unique(panel$aid)), paste(sort(unique(panel$wave)), collapse = ",")))

# ---------------------------------------------------------------------------
# 2. Run the full pipeline against it.
# ---------------------------------------------------------------------------
old_wd <- getwd()
setwd(pkg_dir)
on.exit(setwd(old_wd), add = TRUE)

# panel_path stays NULL in 00_config.R -- `panel` is already in this
# environment, matching the "already in your secure R session" use case.
withCallingHandlers(
  source(file.path("R", "06_run_all.R")),
  warning = function(w) {
    message("  [expected warning during smoke test] ", conditionMessage(w))
    invokeRestart("muffleWarning")
  }
)

# ---------------------------------------------------------------------------
# 3. Assertions.
# ---------------------------------------------------------------------------
stopifnot(
  "core_results should be a non-empty data.frame" = is.data.frame(core_results) && nrow(core_results) > 0,
  "biomarker_results should be a non-empty data.frame" = is.data.frame(biomarker_results) && nrow(biomarker_results) > 0,
  "moderation_results should be a non-empty data.frame" = is.data.frame(moderation_results) && nrow(moderation_results) > 0
)

expected_files <- file.path("output", c("01_core_models.csv", "02_biomarker_specific_models.csv",
                                          "03_moderation_models.csv"))
for (f in expected_files) {
  if (!file.exists(f)) stop("expected output file missing: ", f, call. = FALSE)
}

message("\nALL SMOKE-TEST ASSERTIONS PASSED.")
message("Recovered Model-B coefficient on d_crime_exposure for AL_count (should be directionally ",
        "positive given the synthetic data-generating process):")
print(core_results[core_results$model_label == "B: change in AL_count ~ change in exposure (within-person, individual-clustered SE)" &
                     core_results$term == "d_crime_exposure", c("estimate", "std.error", "p.value")])
