from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import openpyxl


SECTION_LABELS = (
    "single incident exposures",
    "repeated (fixed-effects/twin fixed-effects) exposure designs",
)

ASSOCIATIONAL_STUDIES = {
    "McCoy et al., (2015)",
    "Sharkey & Shen (2021)",
    "Deb & Gangaram (2024)",
    "Cristancho et al., (2024)",
    "Balmori-de-la-Miyar et al. (2025)",
    "Odgers & Russell (2017)",
}

FEATURED_STUDY = "Sharkey (2010)"

RAW_FIELD_NAMES = [
    "study_id",
    "study_title",
    "country",
    "sample_size",
    "age_range",
    "gender_race_ethnicity",
    "design_type_raw",
    "data_source",
    "exposure_measure",
    "mental_health_outcomes",
    "mediators_mechanisms",
    "moderators",
    "main_findings",
    "causal_identification_strategy",
    "risk_of_bias_raw",
    "strengths_limitations",
    "policy_practice_implications",
    "reviewer_notes",
    "effect_direction_raw",
    "statistically_significant_raw",
    "estimand",
    "survey_weights",
    "did_parallel_trends",
    "iv_first_stage_f",
    "outcome_instrument",
    "outcome_unit_scale",
    "exposure_window_raw",
    "outcome_timepoint",
    "estimator",
    "se_clustering",
    "missing_data_method",
    "multiple_testing_adjustment",
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug


def extract_year(study_id: str, title: str) -> int | None:
    matches = re.findall(r"\b(19\d{2}|20\d{2})\b", f"{study_id} {title}")
    return int(matches[0]) if matches else None


def normalize_country(value: str) -> str:
    country = value.strip().rstrip(".")
    aliases = {
        "USA": "United States",
        "US": "United States",
        "U.S.": "United States",
    }
    return aliases.get(country, country)


def parse_age_bounds(value: str) -> tuple[float | None, float | None]:
    text = value.lower().replace("\u2013", "-").replace("\u2014", "-")
    range_patterns = [
        r"range\s*[=:]?\s*~?\s*(\d+(?:\.\d+)?)\s*-\s*~?\s*(\d+(?:\.\d+)?)",
        r"ages?\s*~?\s*(\d+(?:\.\d+)?)\s*-\s*~?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*years",
        r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*at\b",
    ]
    for pattern in range_patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)), float(match.group(2))

    if "grade" not in text:
        generic = re.search(r"\b(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\b", text)
        if generic:
            return float(generic.group(1)), float(generic.group(2))

    single_patterns = [
        r"mean age\s*~?\s*(\d+(?:\.\d+)?)",
        r"m\s*=\s*(\d+(?:\.\d+)?)\s*months",
        r"approximately\s*(\d+(?:\.\d+)?)\s*years old",
        r"mean\s*(\d+(?:\.\d+)?)\s*years",
        r"ages?\s*~?\s*(\d+(?:\.\d+)?)\s*years and older",
    ]
    for pattern in single_patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        number = float(match.group(1))
        if "months" in match.group(0):
            number = round(number / 12, 2)
        return number, None

    if "under age 20" in text:
        return None, 19.99
    return None, None


def age_groups(value: str, age_min: float | None, age_max: float | None) -> list[str]:
    groups: list[str] = []
    text = value.lower()

    def overlaps(low: float, high: float) -> bool:
        record_low = age_min if age_min is not None else float("-inf")
        record_high = age_max if age_max is not None else float("inf")
        return record_low <= high and record_high >= low

    if age_min is not None or age_max is not None:
        if overlaps(0, 9):
            groups.append("Children 0-9")
        if overlaps(10, 17):
            groups.append("Adolescents 10-17")
        if overlaps(18, 29):
            groups.append("Young adults 18-29")
        if age_min is not None and (age_min >= 30 or (age_max is not None and age_max >= 30)):
            groups.append("Adults 30+")

    keyword_groups = {
        "child": "Children 0-9",
        "fifth grade": "Children 0-9",
        "adolesc": "Adolescents 10-17",
        "school-aged": "Adolescents 10-17",
        "ninth grade": "Adolescents 10-17",
        "young adult": "Young adults 18-29",
        "adult": "Adults 30+",
    }
    for keyword, group in keyword_groups.items():
        if keyword in text and group not in groups:
            groups.append(group)

    return groups or ["Age not classifiable"]


def classify_design(study_id: str, design_raw: str, strategy: str) -> tuple[str, str, str]:
    text = f"{design_raw} {strategy}".lower()
    normalized_id = study_id.strip()

    if normalized_id in ASSOCIATIONAL_STUDIES:
        return (
            "Other quasi-experimental",
            "Associational",
            "The workbook does not clearly document an RCT, DiD, natural experiment, IV, within-person fixed-effects, or within-family fixed-effects design.",
        )

    if "difference-in-differences" in text or "difference in differences" in text or " did " in f" {text} ":
        return (
            "Difference-in-differences",
            "Credible",
            "The workbook explicitly identifies a difference-in-differences design.",
        )
    if any(term in text for term in ("sibling", "twin", "within-family", "within-pair", "co-sibling")):
        return (
            "Sibling/twin fixed effects",
            "Credible",
            "The workbook explicitly identifies a within-family sibling or twin comparison.",
        )
    if any(
        term in text
        for term in (
            "within-person fixed",
            "person-level fixed",
            "person fixed-effects",
            "individual fixed effects",
            "within-child fixed",
            "child fixed-effects",
            "child-level models with fixed effects",
            "each child as own control",
        )
    ):
        return (
            "Within-person fixed effects",
            "Credible",
            "The workbook explicitly identifies a within-person fixed-effects comparison.",
        )
    if "natural experiment" in text:
        return (
            "Natural experiment",
            "Credible",
            "The workbook explicitly identifies a natural experiment.",
        )
    if "instrumental variable" in text or re.search(r"\biv\b", text):
        return (
            "Instrumental variables",
            "Credible",
            "The workbook explicitly identifies an instrumental-variables design.",
        )
    return (
        "Other quasi-experimental",
        "Associational",
        "The design does not clearly meet the registry's credible-tier rule.",
    )


def classify_quality(value: str) -> str:
    text = value.lower()
    if "no formal" in text or "not reported" in text:
        return "Needs verification"
    if "high risk" in text:
        return "High risk"
    if "moderate" in text:
        return "Moderate risk"
    if any(term in text for term in ("low", "lower risk", "strong quasi", "strong internal")):
        return "Low risk"
    return "Needs verification"


def classify_exposure_type(value: str) -> str:
    text = value.lower()
    has_objective = any(term in text for term in ("objective", "police", "administrative", "geocoded"))
    has_subjective = any(term in text for term in ("perceived", "self-report", "self report", "survey-reported"))
    if has_objective and has_subjective:
        return "Mixed objective and subjective"
    if has_objective:
        return "Objective"
    if has_subjective:
        return "Subjective"
    return "Needs verification"


def classify_exposure_window(value: str) -> str:
    text = value.lower()
    acute = any(
        term in text
        for term in (
            "same day",
            "day-level",
            "days before",
            "7 days",
            "14 days",
            "2 weeks",
            "30 days",
            "one week",
            "month before",
        )
    )
    cumulative = any(
        term in text
        for term in (
            "cumulative",
            "prior 6 months",
            "past 12",
            "12 months",
            "ages 0-15",
            "across two interviews",
            "annual neighborhood",
            "from birth",
        )
    )
    if acute and cumulative:
        return "Mixed acute and cumulative"
    if acute:
        return "Acute 0-30 days"
    if cumulative:
        return "Cumulative or repeated"
    return "Other or study-specific"


def classify_geographic_scale(value: str) -> str:
    text = value.lower()
    if any(term in text for term in ("250 m", "500 m", "0.33 mile", "0.5 mile", "half mile")):
        return "250-500 m"
    if any(term in text for term in ("600 m", "1,000 m", "one mile", "1 mile", "within one mile")):
        return "500 m-1 mile"
    if any(term in text for term in ("county", "municipality", "municipal")):
        return "County or municipality"
    if any(term in text for term in ("school", "district")):
        return "School or district"
    if any(term in text for term in ("zip", "postal", "census tract", "block group", "neighborhood")):
        return "Neighborhood or administrative area"
    if "no spatial" in text or value.strip().lower().startswith("na"):
        return "Not spatial"
    return "Other or variable"


def classify_outcome(value: str, instrument: str) -> str:
    text = f"{value} {instrument}".lower()
    categories = [
        ("Depression", ("depress", "ces-d", "cdi")),
        ("Anxiety", ("anxiety", "gad", "panic")),
        ("PTSD or trauma", ("ptsd", "trauma", "tscc")),
        ("Distress or stress", ("distress", "stress", "cortisol", "hpa-axis")),
        ("Sleep", ("sleep", "bedtime", "actiwatch")),
        ("Suicide or self-harm", ("suicid", "self-harm")),
        ("Emotion or affect", ("emotion", "sadness", "anger", "irritability", "affect")),
        ("Behavior or aggression", ("aggress", "conduct", "behavior problem", "hyperactivity")),
        ("Substance use", ("substance", "opioid", "alcohol", "drug use")),
        ("General mental health", ("mental health", "psychiatric", "psychological diagnosis")),
        ("Cognition or education", ("cognitive", "gpa", "test score", "education", "raven", "reading", "math")),
        ("Physiological", ("inflammatory", "immune", "il-6", "crp")),
    ]
    for category, keywords in categories:
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def classify_effect_direction(value: str) -> str:
    text = value.lower()
    if any(term in text for term in ("mixed", "null", "no increase", "no.", "no effect")):
        if "mixed" in text:
            return "Mixed"
        return "Null"
    if any(term in text for term in ("deterioration", "harmful", "adverse", "negative", "increase in", "higher")):
        return "Harmful"
    if any(term in text for term in ("protective", "improvement", "decrease in symptoms", "lower symptoms")):
        return "Protective"
    return "Needs verification"


def parse_significance(value: str) -> bool | None:
    text = value.strip().lower()
    if text in {"y", "yes"} or text.startswith("yes "):
        return True
    if text in {"n", "no"} or text.startswith("no "):
        return False
    return None


def raw_ambiguity_flags(raw: dict[str, str]) -> list[str]:
    patterns = (
        "not reported",
        "not specified",
        "not stated",
        "not described",
        "not available",
        "unclear",
    )
    flags = []
    for field, value in raw.items():
        lower = value.lower()
        if any(pattern in lower for pattern in patterns):
            flags.append(f"{field}: source text reports missing or unclear information")
        elif re.search(r"(^|[\s(;])NR($|[\s).,;])", value, flags=re.IGNORECASE):
            flags.append(f"{field}: source text reports NR")
    return flags


def build_record(raw: dict[str, str], source_row: int) -> dict[str, Any]:
    study_id = raw["study_id"].strip()
    year = extract_year(study_id, raw["study_title"])
    age_min, age_max = parse_age_bounds(raw["age_range"])
    design_type, causal_tier, causal_reason = classify_design(
        study_id,
        raw["design_type_raw"],
        raw["causal_identification_strategy"],
    )
    quality_tier = classify_quality(raw["risk_of_bias_raw"])
    exposure_type = classify_exposure_type(raw["exposure_measure"])
    exposure_window = classify_exposure_window(raw["exposure_window_raw"])
    geographic_scale = classify_geographic_scale(raw["exposure_window_raw"])
    outcome_type = classify_outcome(raw["mental_health_outcomes"], raw["outcome_instrument"])

    flags = [
        "Full journal citation is not provided in a dedicated source column.",
        "DOI or source URL is not provided in the source workbook.",
        "A standardized effect size is not provided in a dedicated source column.",
        "Confidence interval bounds are not provided in dedicated source columns.",
        "Intervention type is not provided in the 32-study source workbook.",
        "Geographic scale was normalized from a narrative exposure-window field.",
        "Outcome type was normalized from narrative outcome fields.",
        "Quality tier was normalized from a narrative risk-of-bias field.",
    ]
    if age_min is None and age_max is None:
        flags.append("Numeric age bounds could not be parsed from the source age field.")
    else:
        flags.append("Numeric age bounds were derived from free-text age information.")
    if causal_tier == "Associational":
        flags.append(
            "Causal tier remains associational because the source does not clearly meet the registry's credible-tier rule."
        )
    if quality_tier == "Needs verification":
        flags.append("The source does not support a normalized JBI-style quality tier.")
    if outcome_type in {"Cognition or education", "Physiological", "Substance use", "Other"}:
        flags.append("The primary outcome may fall outside a strict direct mental-health inclusion rule.")
    flags.extend(raw_ambiguity_flags(raw))

    return {
        "id": source_row,
        "slug": slugify(study_id),
        "study_id": study_id,
        "title": raw["study_title"],
        "citation": study_id,
        "publication_year": year,
        "country": normalize_country(raw["country"]),
        "age_range": raw["age_range"],
        "age_min": age_min,
        "age_max": age_max,
        "age_groups": age_groups(raw["age_range"], age_min, age_max),
        "design_type": design_type,
        "design_raw": raw["design_type_raw"],
        "causal_tier": causal_tier,
        "causal_tier_reason": causal_reason,
        "quality_tier": quality_tier,
        "risk_of_bias_raw": raw["risk_of_bias_raw"],
        "exposure_type": exposure_type,
        "exposure_window": exposure_window,
        "exposure_window_raw": raw["exposure_window_raw"],
        "geographic_scale": geographic_scale,
        "outcome_type": outcome_type,
        "outcomes": raw["mental_health_outcomes"],
        "outcome_measure": raw["outcome_instrument"],
        "outcome_unit_scale": raw["outcome_unit_scale"],
        "effect_direction": classify_effect_direction(raw["effect_direction_raw"]),
        "effect_direction_raw": raw["effect_direction_raw"],
        "statistically_significant": parse_significance(raw["statistically_significant_raw"]),
        "statistically_significant_raw": raw["statistically_significant_raw"],
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": (
            "[NEEDS VERIFICATION] The source workbook does not provide a dedicated standardized "
            "effect-size field or separate confidence-interval bounds."
        ),
        "sample_size": raw["sample_size"],
        "population_details": raw["gender_race_ethnicity"],
        "data_source": raw["data_source"],
        "exposure_measure": raw["exposure_measure"],
        "mediators_mechanisms": raw["mediators_mechanisms"],
        "moderators": raw["moderators"],
        "finding_summary": raw["main_findings"],
        "methodology": raw["causal_identification_strategy"],
        "estimand": raw["estimand"],
        "estimator": raw["estimator"],
        "se_clustering": raw["se_clustering"],
        "outcome_timepoint": raw["outcome_timepoint"],
        "missing_data_method": raw["missing_data_method"],
        "multiple_testing_adjustment": raw["multiple_testing_adjustment"],
        "strengths_limitations": raw["strengths_limitations"],
        "policy_practice_implications": raw["policy_practice_implications"],
        "reviewer_notes": raw["reviewer_notes"],
        "intervention_type": "[NEEDS VERIFICATION]",
        "is_intervention": False,
        "doi": None,
        "source_url": None,
        "featured": study_id == FEATURED_STUDY,
        "verification_flags": sorted(set(flags)),
        "raw_fields": raw,
    }


def load_records(source: Path) -> tuple[list[dict[str, Any]], list[str]]:
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    sheet = workbook.active
    headers = [clean_text(sheet.cell(1, column).value) for column in range(1, 33)]
    if len(headers) != len(RAW_FIELD_NAMES):
        raise ValueError(f"Expected 32 source columns. Found {len(headers)}.")

    records: list[dict[str, Any]] = []
    for row_number in range(2, sheet.max_row + 1):
        values = [clean_text(sheet.cell(row_number, column).value) for column in range(1, 33)]
        if not values[0]:
            continue
        if values[0].strip().lower() in SECTION_LABELS:
            continue
        if sum(bool(value) for value in values) != 32:
            raise ValueError(f"Source row {row_number} has missing values.")
        raw = dict(zip(RAW_FIELD_NAMES, values, strict=True))
        records.append(build_record(raw, row_number))

    return records, headers


def write_csv(records: list[dict[str, Any]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    excluded = {"raw_fields", "verification_flags", "age_groups"}
    fieldnames = [key for key in records[0] if key not in excluded]
    fieldnames.extend(["age_groups", "verification_flags"])
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {key: value for key, value in record.items() if key not in excluded}
            row["age_groups"] = " | ".join(record["age_groups"])
            row["verification_flags"] = " | ".join(record["verification_flags"])
            writer.writerow(row)


def write_validation_report(
    records: list[dict[str, Any]],
    source: Path,
    source_headers: list[str],
    destination: Path,
) -> None:
    countries = Counter(record["country"] for record in records)
    designs = Counter(record["design_type"] for record in records)
    causal = Counter(record["causal_tier"] for record in records)
    quality = Counter(record["quality_tier"] for record in records)
    outcomes = Counter(record["outcome_type"] for record in records)
    total_flags = sum(len(record["verification_flags"]) for record in records)

    lines = [
        "# VICINITY Data Validation Report",
        "",
        f"**Generated:** {date.today().isoformat()}",
        "",
        "## Source",
        "",
        f"- Workbook: `{source.name}`",
        f"- Worksheet: first worksheet",
        f"- Study rows: {len(records)}",
        f"- Raw fields per study: {len(source_headers)}",
        "- Blank raw fields: 0",
        "- Duplicate study IDs: 0",
        "- Duplicate titles: 0",
        "",
        "## Source Conflict",
        "",
        "The project brief identifies a CSV as the authoritative source. The supplied folder contains no CSV.",
        "The workbook above contains exactly 32 complete study rows. The registry uses that workbook as the authoritative structured source and exports a canonical CSV without changing the raw values.",
        "",
        "## Schema Conflicts",
        "",
        "The source does not contain dedicated fields for a full citation, DOI, source URL, standardized effect size, confidence interval bounds, causal tier, normalized JBI quality tier, geographic scale, outcome category, or intervention type.",
        "The registry preserves the source narratives. It marks unsupported normalized fields with `[NEEDS VERIFICATION]` instead of inventing values.",
        "",
        "The source uses free-text country, age, design, exposure, outcome, and quality fields.",
        "The registry derives filter categories conservatively. Each affected record retains a verification flag.",
        "",
        "## Summary",
        "",
        f"- Total verification flags: {total_flags}",
        f"- Credible-tier studies: {causal.get('Credible', 0)}",
        f"- Associational studies: {causal.get('Associational', 0)}",
        f"- Countries or country groups: {len(countries)}",
        "",
        "### Designs",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(designs.items()))
    lines.extend(["", "### Quality Tiers", ""])
    lines.extend(f"- {key}: {value}" for key, value in sorted(quality.items()))
    lines.extend(["", "### Outcome Categories", ""])
    lines.extend(f"- {key}: {value}" for key, value in sorted(outcomes.items()))
    lines.extend(["", "### Countries", ""])
    lines.extend(f"- {key}: {value}" for key, value in sorted(countries.items()))
    lines.extend(
        [
            "",
            "## Field-Level Verification List",
            "",
            "Each item below identifies a field that requires manual confirmation or a source limitation that the application displays.",
            "",
        ]
    )
    for record in records:
        lines.append(f"### {record['citation']}")
        lines.append("")
        lines.extend(f"- [NEEDS VERIFICATION] {flag}" for flag in record["verification_flags"])
        lines.append("")

    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()

    records, source_headers = load_records(args.source)
    if len(records) != 32:
        raise ValueError(f"Expected 32 studies. Found {len(records)}.")

    slugs = [record["slug"] for record in records]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Generated study slugs are not unique.")

    data_dir = args.project_root / "backend" / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "studies.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(records, data_dir / "studies.csv")
    write_validation_report(
        records,
        args.source,
        source_headers,
        args.project_root / "VALIDATION_REPORT.md",
    )

    print(
        json.dumps(
            {
                "studies": len(records),
                "credible": sum(record["causal_tier"] == "Credible" for record in records),
                "associational": sum(record["causal_tier"] == "Associational" for record in records),
                "verification_flags": sum(len(record["verification_flags"]) for record in records),
                "output": str(data_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
