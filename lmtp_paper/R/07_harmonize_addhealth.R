# ------------------------------------------------------------------
# 07_harmonize_addhealth.R
# Builds the canonical wide file (data/analysis_wide.csv) from Add Health raw
# variables. Coding rules follow the dissertation manuscripts:
#   * past-year item positive  -> 1 ; 0 only if EVERY item is answered and negative ;
#     otherwise NA (refusal / don't know / legitimate skip -> NA)
#   * Waves I-II perpetration items are frequency codes (0/1/2) -> any > 0
#   * Wave III items are 0/1 "marked"; Waves IV-V are 0/1 yes/no
#   * CES-D: three items (feeling blue/depressed/sad), summed only if all three
#     answered; Wave V scored 1-4 so subtract 1 per item -> 0-9 at every wave
# EVERYTHING marked TODO must be filled from the Add Health codebooks; the
# manuscripts name the perpetration and witnessing variables but not the
# victimization, CES-D, BMI or BP variables.
# ------------------------------------------------------------------

# Add Health special codes for refusal / don't know / skip differ by variable
# and wave. Confirm in the codebook and edit here.
SPECIAL_CODES <- c(6, 7, 8, 9, 96, 97, 98, 99)   # TODO: verify per variable

as_clean <- function(x, special = SPECIAL_CODES) { x <- as.numeric(x); x[x %in% special] <- NA; x }

# any-positive indicator across items: 1 if any positive, 0 if all observed & 0, else NA
any_positive <- function(items, positive = function(z) z > 0) {
  M <- as.matrix(as.data.frame(lapply(items, as_clean)))
  pos <- apply(M, 1, function(r) any(!is.na(r) & positive(r)))
  allobs <- apply(M, 1, function(r) all(!is.na(r)))
  ifelse(pos, 1, ifelse(allobs, 0, NA_real_))
}

# 3-item CES-D sum; wave 5 rescored (1-4 -> 0-3)
cesd3 <- function(items, wave) {
  M <- as.matrix(as.data.frame(lapply(items, as_clean)))
  if (wave == 5) M <- M - 1
  s <- rowSums(M); s[apply(M, 1, function(r) any(is.na(r)))] <- NA
  s
}

# ---- raw variable map (fill TODOs) ---------------------------------
RAW <- list(
  perp = list(`1` = c("H1FV7", "H1FV8"), `2` = c("H2FV6", "H2FV7"), `3` = c("H3DS18H", "H3DS18I"),
              `4` = c("H4DS19", "H4DS20"), `5` = c("H5CJ1E", "H5CJ1F")),
  wit  = list(`1` = "H1FV1", `2` = "H2FV1", `3` = "H3DS18A", `4` = "H4DS14", `5` = "H5CJ2B"),
  vic  = list(`1` = "TODO", `2` = "TODO", `3` = "TODO", `4` = "TODO", `5` = "TODO"),
  cesd = list(`1` = "TODO", `2` = "TODO", `3` = "TODO", `4` = "TODO", `5` = "TODO"),  # 3 items each
  sbp  = list(`4` = "TODO", `5` = "TODO", `6` = "TODO"),
  bmi  = list(`3` = "TODO", `4` = "TODO", `5` = "TODO", `6` = "TODO")
)

harmonize_addhealth <- function(raw) {
  # `raw` must contain AID plus restricted-use contextual variables you merge in.
  stop("Fill RAW (TODOs) and the merge of restricted contextual files, then implement ",
       "the wave loops below. See any_positive() and cesd3() for the coding rules.")
  # Sketch of the intended loop:
  # for (w in 1:5) {
  #   out[[paste0("perp_", w)]] <- any_positive(raw[RAW$perp[[as.character(w)]]], positive = function(z) z >= 1)
  #   out[[paste0("wit_",  w)]] <- any_positive(raw[RAW$wit [[as.character(w)]]], positive = function(z) z >= 1)
  #   out[[paste0("vic_",  w)]] <- any_positive(raw[RAW$vic [[as.character(w)]]], positive = function(z) z >= 1)
  #   out[[paste0("dep_",  w)]] <- cesd3(raw[RAW$cesd[[as.character(w)]]], w)
  # }
  # plus: fam (family id), female, minority, ses, age_w, cdis_w/ccrime_w (waves 1-3),
  #       nbhd_w (waves 4-5), bmi_w, sbp_w; then write data/analysis_wide.csv
}
