# Configuration for the crime -> depression lag analysis.
# All scripts source this file first. Paths are relative to the analysis root
# (analysis/crime-depression-lags/); run scripts from that directory or set
# CRIMEDEP_ROOT.

cfg <- new.env()

cfg$root <- Sys.getenv("CRIMEDEP_ROOT", unset = ".")
cfg$input_dir <- file.path(cfg$root, "input")
cfg$output_dir <- file.path(cfg$root, "output")

# Input files (prepared from restricted-use Add Health sources; see README for
# the required schemas). The pipeline never touches raw Add Health files.
cfg$persons_file <- file.path(cfg$input_dir, "persons.csv")
cfg$person_waves_file <- file.path(cfg$input_dir, "person_waves.csv")
cfg$county_crime_file <- file.path(cfg$input_dir, "county_crime.csv")

# Waves at which exposure (county violent crime) exists.
cfg$exposure_waves <- 1:3

# Lag-pair estimands: exposure wave -> outcome wave. L1-L3 primary, L4 secondary.
cfg$lag_pairs <- list(
  L1 = c(exposure = 1, outcome = 2),
  L2 = c(exposure = 2, outcome = 3),
  L3 = c(exposure = 3, outcome = 4),
  L4 = c(exposure = 3, outcome = 5)
)

# Approximate median elapsed years per pair (used only in sensitivity S1; when
# interview dates are available, compute person-specific elapsed time instead).
cfg$elapsed_years <- c(L1 = 1.0, L2 = 5.5, L3 = 6.5, L4 = 15.0)

# Minimum proportion of CES-D items answered for a valid scale score.
cfg$cesd_min_prop <- 0.8

# Multiple imputation settings. Set CRIMEDEP_MI_M=0 to skip MI (complete-case
# primary), e.g. for pipeline testing.
cfg$mi_m <- as.integer(Sys.getenv("CRIMEDEP_MI_M", unset = "20"))
cfg$mi_seed <- 20260715

# UCR agency-coverage threshold for sensitivity S5 (used only if the crime file
# has a coverage_pct column).
cfg$coverage_threshold <- 90

# Individual covariates used in all adjusted models (must exist in persons.csv).
cfg$person_covariates <- c(
  "sex_female", "race_eth", "parent_educ", "log_hh_income_w1", "family_structure_w1"
)

# County covariates (exposure wave; must exist in county_crime.csv).
cfg$county_covariates <- c("county_poverty", "urbanicity", "log_pop_density")

dir.create(cfg$output_dir, showWarnings = FALSE, recursive = TRUE)

# Disclosure rule for restricted-use output: no released table may reveal
# county identity or cells with n < 5. Table writers call this before saving.
cfg$assert_disclosure_safe <- function(df) {
  stopifnot(!any(grepl("fips", names(df), ignore.case = TRUE)))
  invisible(df)
}
