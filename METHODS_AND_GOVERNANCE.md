# VICINITY Methods and Governance

## Scientific Scope

VICINITY addresses two linked questions.

The exposure stream asks how neighborhood violence affects youth mental health and related outcomes.

The intervention stream asks which structural or psychosocial responses reduce exposure, improve mental health, or change plausible pathways.

The registry keeps these questions separate. This rule prevents a program that reduces violence from being described as improving mental health unless the study measured mental health directly.

## Current Evidence Base

Version 2 contains 58 unique studies.

- 32 studies come from the causal-inference review.
- 26 studies come from the place-based intervention review.
- 19 intervention studies are structural.
- 7 intervention studies are psychosocial.
- 17 intervention studies measure a direct mental-health outcome.

The imported search coverage ends July 31, 2025.

## Record Provenance

Each public record identifies its source review. It also records the workbook row and search cutoff.

The system preserves the raw extraction fields. The normalized fields support search and decision views. Reviewers can therefore trace every public classification to the source record.

## Causal Classification

The credible tier requires explicit support for a design that strengthens causal identification.

Examples include randomized trials and natural experiments. Difference-in-differences designs also qualify. Instrumental-variable designs qualify when the source documents the strategy.

Other studies remain associational. VICINITY does not infer a causal design from a favorable result.

## Outcome Directness

VICINITY assigns one outcome-directness category.

- Direct mental-health outcome
- Exposure-reduction outcome
- Pathway or proximal outcome
- Scope requires verification

This category describes the measured outcome. It does not describe the importance of the intervention.

## Surveillance

The automated search covers the interval after the latest completed search.

PubMed and Crossref serve as the default sources. OpenAlex becomes active when the deployment includes an API key.

The service stores source identifiers and source URLs. It deduplicates records by DOI. It uses normalized title and year when a DOI is absent.

The relevance score ranks candidate records. It does not include or exclude a study.

## Independent Review

Two named reviewers make screening decisions. The system applies the same rule at full text.

The first decision moves the record to an awaiting-second-review state. Agreement advances or excludes the record. Disagreement creates a conflict state.

The current shared-token system controls access to the reviewer workspace. The next governance release should add individual accounts. Individual accounts will strengthen identity assurance and auditability.

## Publication Rule

Candidate records do not appear in public synthesis.

A study can enter the public registry only after the team confirms eligibility. The team must also complete extraction and appraisal. The team must resolve review conflicts before approval.

## Versioning

Each release freezes the approved record set.

Version 1 contains the 32 exposure studies. Version 2 contains all 58 studies.

The public changelog records additions and surveillance runs. A Zenodo token can support DOI publication for future snapshots.

## Limitations

Most source records do not contain structured effect estimates and confidence intervals. VICINITY therefore does not calculate a pooled effect.

Many records lack verified DOIs. This gap limits automated citation tracking.

The evidence base relies heavily on US settings. Users should not assume that an effect transfers to another setting.

The registry is a decision-support system. It does not replace clinical judgment or a formal policy appraisal.

## Technical References

- [Cochrane Handbook, Chapter 22](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-22)
- [NCBI Entrez Programming Utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- [OpenAlex developer documentation](https://developers.openalex.org/)
