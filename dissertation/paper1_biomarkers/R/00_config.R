# Configuration for the Paper 1 biomarker-extension analysis.
# Edit this file first. Every other script reads `config` from here.

config <- list(

  # ---- Data location -------------------------------------------------------
  # Path to the constructed panel inside your secure Add Health session.
  # Leave NULL if you will assign `panel` into the environment yourself before
  # sourcing 06_run_all.R (e.g. it's already loaded from your build pipeline).
  panel_path = NULL,   # e.g. "/secure/workspace/panel.rds" or "panel.csv"

  # ---- Keys -----------------------------------------------------------------
  id_var   = "aid",
  wave_var = "wave",

  # Candidate column names for a family/sibling/twin linkage id. The first one
  # found in the data is used; sibling fixed-effects checks are skipped with a
  # warning if none of these exist.
  family_id_candidates = c("famid", "family_id", "hhid", "household_id"),

  # ---- Exposure cutoffs -------------------------------------------------
  # Contextual county violent-crime linkage is treated as usable only through
  # this wave (per your description: waves 1-3).
  crime_wave_cutoff = 3,

  # Self-reported violence exposure / victimization is treated as usable
  # through this wave (per your description: waves 1-5).
  victimization_wave_cutoff = 5,

  # ---- Exposure variables -------------------------------------------------
  # County-level violent crime (contextual, objective).
  crime_vars = list(
    level        = "violent_rate",
    level_log    = "violent_rate_log",
    level_lag1   = "violent_rate_lag1",
    interwave_avg  = "violent_interwave_avg",
    interwave_dose = "violent_interwave_dose",
    interwave_log  = "violent_interwave_log",
    cumulative     = "violent_cumulative",
    cumulative_log = "violent_cum_log",
    cumulative_dose = "violent_cum_dose"
  ),

  # Self-reported violence exposure / victimization (individual-level).
  victimization_vars = list(
    cum      = "violent_exp_total_cum",
    cum_log  = "violent_exp_total_cum_log",
    flow_early       = "violent_flow_early",
    flow_mid         = "violent_flow_mid",
    flow_late        = "violent_flow_late",
    flow_young_adult = "violent_flow_young_adult"
  ),

  # ---- Biomarkers -------------------------------------------------------
  # Raw biomarker columns. The script auto-detects which waves have non-missing
  # values for these and treats those as "biomarker waves" -- it does not
  # hardcode Wave IV/V/VI.
  biomarker_vars = c("crp", "il6", "glucose", "hbalc", "tg", "tc", "hdl",
                      "non_hdl", "sbp", "dbp", "bmi", "waist"),

  # Standardized (z) biomarker columns used for the continuous AL composite.
  # tc and waist have no z_ column in the screenshot (tc is redundant with
  # hdl + non_hdl; waist may not be z-scored in your build) -- adjust if wrong.
  biomarker_z_vars = c("z_log_crp", "z_log_il6", "z_glucose", "z_hbalc",
                        "z_tg", "z_hdl", "z_non_hdl", "z_sbp", "z_dbp", "z_bmi"),

  # Clinical-risk flag columns (1 = high-risk range) that sum to a classic
  # 10-component allostatic-load count. Detected via regex as a fallback if
  # this exact list doesn't match your build (see utils_al_index.R).
  al_risk_vars = c("al_risk_crp", "al_risk_il6", "al_risk_glucose",
                     "al_risk_hbalc", "al_risk_tg", "al_risk_non_hdl",
                     "al_risk_hdl_low", "al_risk_sbp", "al_risk_dbp",
                     "al_risk_bmi"),

  # Biomarker-adjustment / exclusion flags.
  fasting_var   = "fasting_ok",
  infection_var = "c_infect",     # e.g. CRP > 10 mg/L acute-infection flag
  med_flags     = c("med_lipid", "med_crp", "med_diab"),

  # ---- Moderators (Paper 1 / Hypothesis 3 analogues) -----------------------
  moderators = list(
    family_connection    = "family_connection",
    family_connection_z  = "family_connection_z",
    neighborhood_poverty = "poverty_z",
    neighborhood_disadv  = "neigh_conc_disadv_z",
    school_connect       = "school_connect_baseline",
    school_connect_avg   = "school_connect_avg",
    religion_attend      = "religion_attend_z",
    peer_risk            = "peer_risk"   # optional; not confirmed present
  ),

  # ---- Covariates ------------------------------------------------------
  # Time-invariant, entered as controls in Model A (no individual FE available
  # pre-biomarker); absorbed automatically by first-differencing in Model B.
  baseline_covariates = c("gender", "race", "birth_year"),

  # Time-varying covariates entered in both models where available.
  time_varying_covariates = c("age"),

  # ---- Inference ---------------------------------------------------------
  cluster_var = "aid",   # cluster SEs at the individual level by default;
                          # Model A additionally offers family-clustered SEs
                          # when a family id is available.

  alpha = 0.05,

  # ---- Output --------------------------------------------------------------
  # Relative to the working directory you `source()` from (normally
  # dissertation/paper1_biomarkers/). Git-ignored -- see .gitignore.
  output_dir = "output"
)
