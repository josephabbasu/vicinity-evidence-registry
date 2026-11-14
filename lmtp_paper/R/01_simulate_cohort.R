# ------------------------------------------------------------------
# 01_simulate_cohort.R
# Synthetic Add Health-like cohort with a KNOWN causal truth.
# Purpose: verify that the data build, time ordering and estimators recover
# the right answer BEFORE touching restricted data. Not a claim about Add Health.
#
# Truth is computed by re-running the same data-generating process with
# involvement forced to 0 at chosen waves, using common random numbers.
# ------------------------------------------------------------------
suppressPackageStartupMessages(library(data.table))

# type = "calibrated": effect sizes taken from the dissertation papers
#   past-year victimization ~0.20 SD (~0.37 points on a ~1.4 mean)  -> bv ~ 0.22
#   each earlier victimization report ~0.08 SD (~0.15 points)       -> gv ~ 0.10
#   past-year perpetration ~0.17 points, no lingering                -> bp ~ 0.12, gp = 0
# type = "strong": inflated effects, ONLY for verifying that the code can
#   recover a known effect at modest n. Not a claim about Add Health.
sim_params <- function(type = c("calibrated", "strong")) {
  type <- match.arg(type)
  p <- list(bv = 0.22, bp = 0.12, gv = 0.10, gp = 0.00, rho = 0.55,
            dcur = 1.0, dlag = 1.6, wave_int = c(0, 0, 0.10, -0.10, -0.10))
  if (type == "strong") { p$bv <- .35; p$gv <- .30; p$rho <- .60; p$dcur <- 2.5; p$dlag <- 4 }
  p
}

simulate_cohort <- function(N = 6000, seed = 1, policy_waves = integer(0),
                            u_strength = 0, fam_strength = 0,
                            attrition = TRUE, mask = TRUE,
                            attr_current_dep = FALSE, par = sim_params()) {
  set.seed(seed)
  T <- 5L
  # ---- time-fixed ------------------------------------------------
  female <- rbinom(N, 1, .5); minority <- rbinom(N, 1, .35); ses <- rnorm(N)
  age1 <- runif(N, 12, 19)
  gap  <- c(0, 1, 6, 13, 22, 27)
  age  <- sapply(1:6, function(t) age1 + gap[t])
  fam  <- seq_len(N); n_pair <- floor(N * 0.15)
  sib  <- sample.int(N, 2 * n_pair)
  fam[sib[(n_pair + 1):(2 * n_pair)]] <- fam[sib[1:n_pair]]
  ufam <- rnorm(N)[fam]; uper <- rnorm(N)
  u    <- u_strength * uper + fam_strength * ufam   # UNMEASURED confounder (0 by default)

  # ---- context ----------------------------------------------------
  cdis <- matrix(NA_real_, N, 3)
  cdis[, 1] <- .5 * minority - .4 * ses + rnorm(N, 0, .8)
  for (t in 2:3) cdis[, t] <- .8 * cdis[, t - 1] + rnorm(N, 0, .5)
  ccrime <- .5 * cdis + matrix(rnorm(N * 3, 0, .9), N, 3)
  nbhd <- matrix(NA_real_, N, 5)
  nbhd[, 4] <- .6 * cdis[, 3] + rnorm(N, 0, .8)
  nbhd[, 5] <- .8 * nbhd[, 4] + rnorm(N, 0, .5)
  ctx <- cbind(cdis, nbhd[, 4:5])

  # ---- common random numbers -------------------------------------
  Uv <- matrix(runif(N * T), N, T); Up <- matrix(runif(N * T), N, T)
  Uw <- matrix(runif(N * T), N, T); Ud <- matrix(runif(N * T), N, T)
  Z  <- matrix(rnorm(N * T), N, T)
  Eb <- matrix(rnorm(N * 6), N, 6); Ebp <- matrix(rnorm(N * 6), N, 6)
  Ua <- matrix(runif(N * 6), N, 6); Ubp <- matrix(runif(N * 6), N, 6)

  # ---- waves 1..5: involvement, witnessing, symptoms --------------
  vic <- perp <- wit <- dep <- A <- matrix(0, N, T)
  int_v <- c(-2.5, -2.6, -2.9, -3.6, -4.2)
  int_p <- c(-3.0, -3.1, -3.3, -3.9, -4.5)
  for (t in 1:T) {
    pv <- if (t > 1) vic[, t - 1]  else 0
    pp <- if (t > 1) perp[, t - 1] else 0
    pw <- if (t > 1) wit[, t - 1]  else 0
    dp <- if (t > 1) (dep[, t - 1] - 1.5) / 1.8 else 0
    lpv <- int_v[t] + .5 * (1 - female) + .3 * minority + .25 * ctx[, t] +
           .35 * pv + .25 * pp + .12 * dp + .2 * pw + .6 * Z[, t] + u
    lpp <- int_p[t] + .6 * (1 - female) + .2 * minority + .20 * ctx[, t] +
           .35 * pp + .25 * pv + .10 * dp + .2 * pw + .6 * Z[, t] + u
    vic[, t]  <- as.numeric(Uv[, t] < expit(lpv))
    perp[, t] <- as.numeric(Up[, t] < expit(lpp))
    if (t %in% policy_waves) { vic[, t] <- 0; perp[, t] <- 0 }     # <- the intervention
    A[, t]   <- pmax(vic[, t], perp[, t])
    wit[, t] <- as.numeric(Uw[, t] < expit(-2.2 + .5 * A[, t] + .2 * ctx[, t] + .3 * pw))
    cumv <- if (t > 1) rowSums(vic[,  1:(t - 1), drop = FALSE]) else 0
    cump <- if (t > 1) rowSums(perp[, 1:(t - 1), drop = FALSE]) else 0
    ll <- if (t == 1) {
      log(1.1) + .12 * female + .08 * minority - .06 * ses + .08 * ctx[, t]
    } else {
      log(.75) + par$rho * log1p(dep[, t - 1]) + .10 * female + .05 * minority -
        .04 * ses + .05 * ctx[, t] + par$wave_int[t]
    }
    ll <- ll + par$bv * vic[, t] + par$bp * perp[, t] +
               par$gv * cumv + par$gp * cump + .5 * u
    dep[, t] <- pmin(9, qpois(Ud[, t], exp(ll)))
  }

  # ---- BMI (3-6) and systolic BP (4-6) ---------------------------
  bmi <- matrix(NA_real_, N, 6)
  bmi[, 3] <- 24.5 + 1.2 * minority - .4 * ses + 1.0 * (1 - female) + rnorm(N, 0, 4)
  for (t in 4:6) bmi[, t] <- bmi[, t - 1] + .7 + .12 * dep[, t - 1] + 1.2 * Eb[, t]
  base <- function(t) 112 + 6 * (1 - female) + .22 * (age[, t] - 28) + .7 * (bmi[, t] - 25)
  sbp <- matrix(NA_real_, N, 6)
  sbp[, 4] <- base(4) + par$dcur * A[, 4] + par$dlag * A[, 3] + 9 * Ebp[, 4]
  for (t in 5:6) {
    acur <- if (t <= 5) A[, t] else 0
    sbp[, t] <- .55 * sbp[, t - 1] + .45 * base(t) + par$dcur * acur +
                par$dlag * A[, t - 1] + 6 * Ebp[, t]
  }

  # ---- participation (monotone) ----------------------------------
  obs <- matrix(1, N, 6); bpo <- matrix(1, N, 6)
  if (attrition) {
    cur <- function(x) if (attr_current_dep) -.15 * (x - 1.5) else 0
    p4 <- expit(1.8 - .3 * minority - .25 * A[, 3] - .08 * (dep[, 2] - 1.5) + cur(dep[, 3]))
    obs[, 4] <- as.numeric(Ua[, 4] < p4)
    p5 <- expit(1.5 - .3 * minority - .30 * A[, 4] - .10 * (dep[, 3] - 1.5) + cur(dep[, 4]))
    obs[, 5] <- obs[, 4] * as.numeric(Ua[, 5] < p5)
    p6 <- expit(1.3 - .2 * minority - .20 * A[, 5] - .08 * (dep[, 4] - 1.5) + cur(dep[, 5]))
    obs[, 6] <- obs[, 5] * as.numeric(Ua[, 6] < p6)
    bpo[, 4:6] <- (Ubp[, 4:6] < .7) * 1
  }

  # ---- assemble ---------------------------------------------------
  dt <- data.table(id = seq_len(N), fam = fam, female, minority, ses, age1)
  for (t in 1:6) dt[[paste0("age_", t)]] <- age[, t]
  for (t in 1:3) { dt[[paste0("cdis_", t)]] <- cdis[, t]; dt[[paste0("ccrime_", t)]] <- ccrime[, t] }
  for (t in 4:5) dt[[paste0("nbhd_", t)]] <- nbhd[, t]
  for (t in 1:5) {
    dt[[paste0("vic_", t)]]  <- vic[, t];  dt[[paste0("perp_", t)]] <- perp[, t]
    dt[[paste0("wit_", t)]]  <- wit[, t];  dt[[paste0("dep_", t)]]  <- dep[, t]
  }
  for (t in 3:6) dt[[paste0("bmi_", t)]] <- bmi[, t]
  for (t in 4:6) dt[[paste0("sbp_", t)]] <- sbp[, t]
  for (t in 1:6) dt[[paste0("obs_", t)]] <- obs[, t]
  for (t in 4:6) dt[[paste0("bpo_", t)]] <- bpo[, t]

  if (mask && attrition) {
    for (t in 4:6) {
      gone <- obs[, t] == 0
      for (nm in c("vic", "perp", "wit", "dep", "bmi", "sbp", "nbhd", "age")) {
        col <- paste0(nm, "_", t)
        if (col %in% names(dt)) dt[gone, (col) := NA_real_]
      }
      nobp <- bpo[, t] == 0
      for (nm in c("sbp")) { col <- paste0(nm, "_", t); dt[nobp, (col) := NA_real_] }
    }
  }
  dt[]
}

# ------------------------------------------------------------------
# Truth: mean outcome under each policy in the ELIGIBLE population.
# Eligibility mirrors the design builder: observed at the first treatment wave.
# ------------------------------------------------------------------
sim_truth <- function(design, policy_waves, N = 200000, seed = 999, ...) {
  nat <- simulate_cohort(N, seed, integer(0), attrition = TRUE, mask = FALSE, ...)
  pol <- simulate_cohort(N, seed, policy_waves, attrition = TRUE, mask = FALSE, ...)
  w1  <- design$trt_waves[1]
  elig <- if (w1 >= 4) nat[[paste0("obs_", w1)]] == 1 else rep(TRUE, N)
  y <- design$outcome
  c(natural = mean(nat[[y]][elig]),
    policy  = mean(pol[[y]][elig]),
    diff    = mean(pol[[y]][elig]) - mean(nat[[y]][elig]))
}
