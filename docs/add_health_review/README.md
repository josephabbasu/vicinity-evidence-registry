# Add Health Evidence Catalogue & Dissertation Novelty Audit

Source-verified catalogue of Add Health research on neighborhood violence,
community violence, victimization, and adolescent mental health, mapped against
the dissertation's proposed contributions.

## Files

- **`Add_Health_Evidence_Catalogue_and_Novelty_Audit.docx`** — committee-ready
  Word document: executive summary, data-integrity/exclusions, the full
  catalogue (Tier A + Tier B), synthesis by domain, evidence gaps, the corrected
  novelty audit, and a recommended novelty statement.
- **`Add_Health_Evidence_Catalogue.html`** — the same content as an interactive,
  searchable/filterable web page (open in a browser).
- **`verified_studies_dataset.json`** — the underlying classified dataset (one
  record per study with status, verification level, design, data, and findings).

## Corpus summary

- **108** verified Add Health studies (target: 100).
  - **63** Tier A (author, design, data, findings).
  - **45** Tier B (citation & design level; no findings claimed).
- **5** removed — confirmed NOT Add Health (AH-001 Los Angeles County;
  AH-003 National Youth Survey; AH-079 New Orleans sample; AH-099 Fragile
  Families; AH-102 National Crime Victimization Survey).
- **7** quarantined — Add Health use unverifiable (AH-022, AH-053, AH-080,
  AH-094, AH-104, AH-118, AH-119).
- **1** mixed-sample flagged (AH-034 — Add Health + YRBS + a third sample).

## Method

Every record was checked against its actual data source rather than trusting the
original workbook's uniform "Add Health confirmed" label. Findings are sourced
from full text (4 studies) or database abstracts/metadata (Tier A). No effect
sizes, confidence intervals, or DOIs were fabricated. One DOI was corrected:
AH-056 (Anderson, Cesur & Tekin 2015) from `10.1111/ecin.12176` to
`10.1111/ecin.12145`.

## Open items before committee submission

1. Verify the quarantined CRP dissertation (AH-119) — the largest unresolved
   biomarker-precedence risk.
2. Pull full text for the 7 quarantined records to decide keep/cut.
