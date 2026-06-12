# VICINITY Data Validation Report

**Generated:** 2026-06-12

## Source

- Workbook: `Synthesis_Systematic Review Extraction_Prevention Sc_2026_fnl_ARR_JOE_Paper 1.xlsx`
- Worksheet: first worksheet
- Study rows: 32
- Raw fields per study: 32
- Blank raw fields: 0
- Duplicate study IDs: 0
- Duplicate titles: 0

## Source Conflict

The project brief identifies a CSV as the authoritative source. The supplied folder contains no CSV.
The workbook above contains exactly 32 complete study rows. The registry uses that workbook as the authoritative structured source and exports a canonical CSV without changing the raw values.

## Schema Conflicts

The source does not contain dedicated fields for a full citation, DOI, source URL, standardized effect size, confidence interval bounds, causal tier, normalized JBI quality tier, geographic scale, outcome category, or intervention type.
The registry preserves the source narratives. It marks unsupported normalized fields with `[NEEDS VERIFICATION]` instead of inventing values.

The source uses free-text country, age, design, exposure, outcome, and quality fields.
The registry derives filter categories conservatively. Each affected record retains a verification flag.

## Summary

- Total verification flags: 370
- Credible-tier studies: 26
- Associational studies: 6
- Countries or country groups: 10

### Designs

- Difference-in-differences: 8
- Natural experiment: 5
- Other quasi-experimental: 6
- Sibling/twin fixed effects: 6
- Within-person fixed effects: 7

### Quality Tiers

- Low risk: 25
- Moderate risk: 5
- Needs verification: 2

### Outcome Categories

- Anxiety: 2
- Behavior or aggression: 1
- Cognition or education: 7
- Depression: 9
- Distress or stress: 1
- Emotion or affect: 4
- General mental health: 3
- Other: 1
- Physiological: 1
- Substance use: 2
- Suicide or self-harm: 1

### Countries

- Brazil: 1
- Canada: 1
- Chile: 1
- Colombia: 3
- England and Wales: 1
- Finland: 2
- Mexico: 2
- Norway: 1
- United Kingdom: 1
- United States: 19

## Field-Level Verification List

Each item below identifies a field that requires manual confirmation or a source limitation that the application displays.

### Ang (2021)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds could not be parsed from the source age field.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information

### Rossin-Slater et al., (2020)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.

### Gujral et al., ( 2023)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds could not be parsed from the source age field.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] se_clustering: source text reports missing or unclear information

### Bharadwaj et al. (2021)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information

### McCoy et al., (2015)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.

### Levine & McKnight (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds could not be parsed from the source age field.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] mediators_mechanisms: source text reports NR

### Karandinos et al. (2026)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports NR
- [NEEDS VERIFICATION] mediators_mechanisms: source text reports NR
- [NEEDS VERIFICATION] se_clustering: source text reports NR

### Cabral et al. (2026)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] did_parallel_trends: source text reports NR
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] mediators_mechanisms: source text reports NR

### Sharkey & Shen (2021)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] mediators_mechanisms: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR
- [NEEDS VERIFICATION] se_clustering: source text reports NR
- [NEEDS VERIFICATION] survey_weights: source text reports NR

### Deb & Gangaram (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information

### Heissel et al.,( 2018)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.

### Cristancho et al., (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] estimand: source text reports missing or unclear information
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Sharkey (2010)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Abufhele & Laurito (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] The source does not support a normalized JBI-style quality tier.

### Molano et al. (2018)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] age_range: source text reports missing or unclear information
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Vogel et al. (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### McCoy et al. (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The source does not support a normalized JBI-style quality tier.
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] se_clustering: source text reports missing or unclear information

### Cuartas & Leventhal (2020)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.

### Shulman et al. (2021)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] se_clustering: source text reports NR

### Jaffee et al. (2023)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] se_clustering: source text reports NR

### Connolly et al. (2022)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR

### Singham et al. (2017)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR
- [NEEDS VERIFICATION] outcome_unit_scale: source text reports NR

### Schaefer et al., (2018)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR

### Balmori-de-la-Miyar et al. (2025)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR

### Odgers & Russell (2017)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports missing or unclear information
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information

### Finegood et al.,( 2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] estimand: source text reports missing or unclear information
- [NEEDS VERIFICATION] missing_data_method: source text reports missing or unclear information
- [NEEDS VERIFICATION] se_clustering: source text reports missing or unclear information

### Lyons et al., (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Voith, Gromoske, & Holmes (2014)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] se_clustering: source text reports missing or unclear information
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Quintana-Navarrete (2025)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] survey_weights: source text reports missing or unclear information

### Tarkiainen et al. (2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] estimand: source text reports missing or unclear information
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information

### Miller et al.,( 2024)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds were derived from free-text age information.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] The primary outcome may fall outside a strict direct mental-health inclusion rule.
- [NEEDS VERIFICATION] age_range: source text reports NR
- [NEEDS VERIFICATION] estimand: source text reports NR

### Pitkänen et al. (2026)

- [NEEDS VERIFICATION] A standardized effect size is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Confidence interval bounds are not provided in dedicated source columns.
- [NEEDS VERIFICATION] DOI or source URL is not provided in the source workbook.
- [NEEDS VERIFICATION] Full journal citation is not provided in a dedicated source column.
- [NEEDS VERIFICATION] Geographic scale was normalized from a narrative exposure-window field.
- [NEEDS VERIFICATION] Intervention type is not provided in the 32-study source workbook.
- [NEEDS VERIFICATION] Numeric age bounds could not be parsed from the source age field.
- [NEEDS VERIFICATION] Outcome type was normalized from narrative outcome fields.
- [NEEDS VERIFICATION] Quality tier was normalized from a narrative risk-of-bias field.
- [NEEDS VERIFICATION] estimand: source text reports NR
- [NEEDS VERIFICATION] gender_race_ethnicity: source text reports missing or unclear information
- [NEEDS VERIFICATION] mediators_mechanisms: source text reports NR
- [NEEDS VERIFICATION] missing_data_method: source text reports NR
- [NEEDS VERIFICATION] moderators: source text reports NR
