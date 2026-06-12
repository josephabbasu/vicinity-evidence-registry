# VICINITY Version 2 Validation Report

## Build Date

June 12, 2026

## Source Validation

The exposure workbook contains 32 complete study records.

The intervention workbook contains 26 complete study records.

The combined registry contains 58 unique titles. The two workbooks contain no exact cross-stream title duplicates.

## Intervention Portfolio

The intervention workbook contains 19 structural studies and 7 psychosocial studies.

The normalization identifies 17 intervention records with direct mental-health outcomes. The other records measure violence reduction, proximal pathways, or outcomes that require verification.

## Provenance

Every generated record includes the source review. Every record also includes the July 31, 2025 search cutoff. Each record retains the workbook row.

The generators preserve the original extraction values in `raw_fields`.

## Fabrication Controls

The seed process does not create publications.

The seed process does not create DOIs.

The seed process does not infer numerical effect estimates from narrative text.

The seed process does not assign proxy p-values.

The effect-estimate table receives a row only when the workbook contains a structured effect or confidence interval.

## Review Controls

The reviewer API requires a private deployment token.

The screening workflow requires two named reviewers. The full-text workflow applies the same rule.

The registry records conflicts. A conflict does not advance automatically.

## Surveillance Controls

The surveillance process uses source APIs. It stores PubMed, Crossref, or OpenAlex identifiers.

The search run records the covered interval and completed sources. A failed source does not appear as completed.

The scheduled endpoint requires a separate private token.

## Remaining Validation Work

The team should verify missing DOIs against primary publications.

The team should extract numerical estimates and confidence intervals from eligible primary reports.

The team should add individual reviewer accounts before a multi-institutional launch.

The team should obtain stakeholder feedback from practitioners and policy users. That work should test whether the decision views answer real operational questions.
