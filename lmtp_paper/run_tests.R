# Fast unit tests (no lmtp needed).  Run:  Rscript run_tests.R   (from lmtp_paper/)
source("R/00_config.R"); source("R/utils.R")
source("R/01_simulate_cohort.R"); source("R/02_build_design_data.R")
source("R/05_fe_benchmark.R"); source("R/06_diagnostics.R")
ok <- function(cond, msg) { if (!isTRUE(cond)) stop("FAILED: ", msg, call. = FALSE); cat("  ok -", msg, "\n") }

cat("1. simulator\n")
w <- simulate_cohort(4000, seed = 1)
ok(nrow(w) == 4000 && all(c("vic_1", "dep_5", "sbp_6", "obs_5") %in% names(w)), "expected columns present")
ok(all(w$dep_1 %in% 0:9), "depressive score within 0-9")
ok(mean(w$obs_5, na.rm = TRUE) < mean(w$obs_4, na.rm = TRUE) + 1e-9, "participation is monotone")
ok(all(is.na(w$dep_4[w$obs_4 == 0])), "masked after dropout")
cat(sprintf("     mean dep by wave: %s\n", paste(round(colMeans(w[, paste0("dep_", 1:5), with = FALSE], na.rm = TRUE), 2), collapse = " ")))
cat(sprintf("     any involvement by wave: %s\n", paste(round(sapply(1:5, function(t) mean(pmax(w[[paste0("vic_", t)]], w[[paste0("perp_", t)]]), na.rm = TRUE)), 3), collapse = " ")))
cat(sprintf("     SBP mean/sd (wave 4): %.1f / %.1f\n", mean(w$sbp_4, na.rm = TRUE), sd(w$sbp_4, na.rm = TRUE)))

cat("2. truth responds to the policy in the expected direction\n")
tr <- sim_truth(cfg$designs$dep_III_IV, c(3, 4), N = 60000)
ok(tr["diff"] < 0, sprintf("preventing involvement lowers symptoms (diff = %.3f)", tr["diff"]))
trb <- sim_truth(cfg$designs$sbp_IV, 4, N = 60000)
ok(trb["diff"] < 0, sprintf("preventing involvement lowers SBP (diff = %.2f mmHg)", trb["diff"]))

cat("3. time-ordering guard\n")
bd <- build_design(w, cfg$designs$dep_III_IV, "any", "post", verbose = FALSE)
ok(isTRUE(check_time_ordering(bd$spec, c(3, 4), "post")), "clean design passes")
bad <- bd$spec; bad$time_vary[[1]] <- c(bad$time_vary[[1]], "dep_4")
ok(inherits(try(check_time_ordering(bad, c(3, 4), "post"), silent = TRUE), "try-error"), "future covariate (dep_4 before A_3) is caught")
bad2 <- bd$spec; bad2$time_vary[[1]] <- c(bad2$time_vary[[1]], "dep_3")
ok(inherits(try(check_time_ordering(bad2, c(3, 4), "post"), silent = TRUE), "try-error"), "same-wave symptom is caught in 'post' mode")
ok(isTRUE(check_time_ordering(bad2, c(3, 4), "pre")), "same-wave symptom allowed in 'pre' mode")
bad3 <- bd$spec; bad3$outcome <- "dep_4"
ok(inherits(try(check_time_ordering(bad3, c(3, 4), "post"), silent = TRUE), "try-error"), "outcome must follow last exposure")

cat("4. design builder\n")
for (nm in names(cfg$designs)) for (tm in cfg$timings) {
  b <- build_design(w, cfg$designs[[nm]], "any", tm, verbose = FALSE)
  K <- length(b$spec$trt)
  C <- as.matrix(b$data[b$spec$cens])
  ok(all(apply(C, 1, function(r) all(diff(r) <= 0))), sprintf("%s/%s: censoring monotone", nm, tm))
  ok(!anyNA(b$data[c(b$spec$baseline, b$spec$time_vary[[1]], b$spec$trt[1])]), sprintf("%s/%s: first block complete", nm, tm))
  y <- b$data[[b$spec$outcome]]
  ok(all(is.na(y) == (C[, K] == 0)), sprintf("%s/%s: outcome observed iff C_K = 1", nm, tm))
}
ok(max(sapply(build_design(w, cfg$designs$dep_III_IV, "any", "post", FALSE)$spec$time_vary, length)) > 0, "time-varying sets non-empty")

cat("5. positivity table\n")
pt <- positivity_table(bd); print(pt)

cat("6. fixed-effects benchmark runs and has the expected sign pattern\n")
fb <- fe_benchmark(w)
print(cbind(term = fb$main$term, round(fb$main[, c("est", "se")], 3)))
ok(fb$main$est[fb$main$term == "vic"] > 0, "past-year victimization coefficient > 0")
ok(fb$main$est[fb$main$term == "vic"] > fb$main$est[fb$main$term == "earlier_vic"], "past-year > earlier-report coefficient")
cat("7. Add Health coding rules\n")
source("R/07_harmonize_addhealth.R")
a <- any_positive(list(c(0, 1, 0, NA, 9), c(0, 0, NA, NA, 0)))
ok(identical(a, c(0, 1, NA, NA, NA)), "any_positive: 1 if any positive, 0 only if all observed and 0, else NA")
cs <- cesd3(list(c(0, 1, 2, NA), c(1, 1, 3, 0), c(0, 2, 3, 0)), wave = 3)
ok(identical(cs, c(1, 4, 8, NA)), "cesd3 sums three items, NA if any missing")
cs5 <- cesd3(list(c(1, 2), c(1, 2), c(1, 4)), wave = 5)
ok(identical(cs5, c(0, 5)), "cesd3 rescales Wave V (1-4 -> 0-3)")
cat("8. adapter: objects shaped like your session (long panel, biomarker panel, sib_prof)\n")
source("R/07a_adapter_from_panel.R")
ws <- simulate_cohort(1500, seed = 3)
long <- rbindlist(lapply(1:5, function(t) {
  keep <- !is.na(ws[[paste0("dep_", t)]])
  data.table(aid = ws$id[keep], wave = t,
    weapon_victimization = ws[[paste0("vic_", t)]][keep] * (if (t <= 2) 2 else 1),  # Waves I-II frequency codes
    weapon_violence = ws[[paste0("perp_", t)]][keep], weapon_witnessing = ws[[paste0("wit_", t)]][keep],
    depression = ws[[paste0("dep_", t)]][keep], age = ws[[paste0("age_", t)]][keep],
    gender = ifelse(ws$female[keep] == 1, "Female", "Male"), race = ifelse(ws$minority[keep] == 1, "Black", "White"),
    neigh_conc_disadv_raw = if (t <= 3) ws[[paste0("cdis_", t)]][keep] else ws[[paste0("nbhd_", t)]][keep],
    cty_violent_rate_log = if (t <= 3) ws[[paste0("ccrime_", t)]][keep] else NA_real_,
    poverty_z = rnorm(sum(keep)), family_connection_baseline = ws$ses[keep])
}))
bio <- rbindlist(lapply(4:6, function(t) {
  keep <- !is.na(ws[[paste0("sbp_", t)]])
  data.table(aid = ws$id[keep], wave = t, sbp = ws[[paste0("sbp_", t)]][keep],
             bmi = ws[[paste0("bmi_", t)]][keep], med_bp = 0)
}))
sibp <- data.table(AID = ws$id, FAMID = ws$fam)
Wd <- build_wide_from_panel(long, bio, sibp, verbose = FALSE)
m <- match(Wd$id, as.character(ws$id))
ok(all(Wd$vic_1 == as.integer(ws$vic_1[m]), na.rm = TRUE), "victimization recoded >0 (frequency codes -> 0/1)")
ok(isTRUE(all.equal(Wd$dep_5, ws$dep_5[m])), "depression carried through unchanged")
ok(isTRUE(all.equal(Wd$sbp_5, ws$sbp_5[m])), "biomarker panel merged by aid x wave")
ok(all(Wd$fam == as.character(ws$fam[m])), "FAMID -> fam")
ok(all(Wd$female == ws$female[m]) && all(Wd$minority == ws$minority[m]), "sex and race recoded")
ok(isTRUE(all.equal(Wd$cumv_3, ws$vic_1[m] + ws$vic_2[m] + ws$vic_3[m])), "earlier-report count matches your make_history() definition")
ok(!"ccrime_4" %in% names(Wd), "county crime restricted to waves 1-3")
for (nm in names(cfg$designs)) for (tm in cfg$timings) {
  b <- build_design(Wd, cfg$designs[[nm]], "any", tm, verbose = FALSE)
  ok(nrow(b$data) > 100, sprintf("adapter output builds design %s/%s (n=%d)", nm, tm, nrow(b$data)))
}
bb <- build_design(Wd, cfg$designs$dep_III_IV, "any", "post", verbose = FALSE)
cat("     covariates in block 1:", paste(bb$spec$time_vary[[1]], collapse = ", "), "\n")
cat("     baseline:", paste(bb$spec$baseline, collapse = ", "), "\n")
cat("\nALL TESTS PASSED\n")
