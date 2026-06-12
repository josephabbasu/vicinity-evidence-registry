"""Generate the 26-study intervention seed from the authoritative workbook."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import openpyxl


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_ROOT / "data" / "source" / "Intervention_Systematic_Review_Extraction_Paper_2.xlsx"
OUTPUT = PROJECT_ROOT / "backend" / "app" / "data" / "intervention_studies.json"

SECTION_LABELS = (
    "place-based (structural/context changes that alter exposure)",
    "psychosocial (clinical/skills programs delivered to youth/caregivers)",
)

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
    "intervention_type_raw",
    "intervention_description",
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
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def extract_year(study_id: str, title: str) -> int | None:
    match = re.search(r"(19\d{2}|20\d{2})", f"{study_id} {title}")
    return int(match.group(1)) if match else None


def parse_age_bounds(value: str) -> tuple[float | None, float | None]:
    text = value.lower().replace("\u2013", "-").replace("\u2014", "-")
    if any(term in text for term in ("not applicable", "not reported", "not specified")):
        return None, None
    patterns = [
        r"ages?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years|year-olds?)",
        r"range[^0-9]*(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)), float(match.group(2))
    if "grade" not in text:
        generic = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\b", text)
        if generic:
            return float(generic.group(1)), float(generic.group(2))
    mean_age = re.search(r"(?:mean age|mage)\D{0,8}(\d+(?:\.\d+)?)", text)
    if mean_age:
        value = float(mean_age.group(1))
        return value, value
    numbers = [float(number) for number in re.findall(r"\b\d+(?:\.\d+)?\b", text)]
    plausible = [number for number in numbers if 0 <= number <= 100]
    if len(plausible) == 1:
        return plausible[0], plausible[0]
    return None, None


def classify_age_groups(
    value: str,
    age_min: float | None,
    age_max: float | None,
) -> list[str]:
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
        if age_max is not None and age_max >= 30:
            groups.append("Adults 30+")

    keywords = {
        "child": "Children 0-9",
        "adolesc": "Adolescents 10-17",
        "youth": "Adolescents 10-17",
        "young adult": "Young adults 18-29",
    }
    for keyword, group in keywords.items():
        if keyword in text and group not in groups:
            groups.append(group)
    return groups or ["Age not classifiable"]


def classify_design(design: str, strategy: str) -> tuple[str, str]:
    text = f"{design} {strategy}".lower()
    if "random" in text:
        return "Randomized controlled trial", "The source describes randomized assignment."
    if "difference-in-differences" in text or "difference in differences" in text:
        return "Difference-in-differences", "The source describes a difference-in-differences design."
    if "instrumental variable" in text or re.search(r"\biv\b", text):
        return "Instrumental variables", "The source describes an instrumental-variables design."
    if "natural experiment" in text:
        return "Natural experiment", "The source describes a natural experiment."
    if "interrupted time" in text:
        return "Interrupted time series", "The source describes an interrupted time-series design."
    if "fixed effect" in text or "fixed-effect" in text:
        return "Fixed effects", "The source describes a fixed-effects comparison."
    return (
        "Other quasi-experimental",
        "The intervention review included this study under its prespecified counterfactual design criteria.",
    )


def classify_quality(value: str) -> str:
    text = value.lower()
    if "high risk" in text:
        return "High risk"
    if "moderate" in text:
        return "Moderate risk"
    if "low" in text:
        return "Low risk"
    return "Needs verification"


def classify_intervention(value: str) -> str:
    text = value.lower()
    if "psychosocial" in text:
        return "Psychosocial"
    if "structural" in text or "place-based" in text:
        return "Structural"
    return "Needs verification"


def classify_outcome(value: str, instrument: str) -> str:
    text = f"{value} {instrument}".lower()
    categories = [
        ("PTSD or trauma", ("ptsd", "post-traumatic", "posttraumatic", "trauma symptom")),
        ("Depression", ("depress", "cdi", "ces-d")),
        ("Anxiety", ("anxiety", "anxious", "gad", "sared", "scared")),
        ("Distress or stress", ("distress", "stress", "perceived stress")),
        ("General mental health", ("mental health", "mental-health", "psychiatric", "psychological wellbeing")),
        ("Fear and safety", ("fear", "perceived safety", "feeling safe")),
        ("Physiological", ("cortisol", "heart rate", "physiological", "biomarker")),
        ("Violence reduction", ("crime", "gun assault", "shooting", "homicide", "violent incident")),
        ("Behavior or aggression", ("aggress", "conduct", "behavior")),
        ("Academic outcomes", ("academic", "school performance", "gpa")),
        ("Substance use", ("substance", "alcohol", "drug use")),
    ]
    for category, keywords in categories:
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def classify_outcome_directness(outcome_type: str, outcomes: str) -> str:
    text = outcomes.lower()
    if outcome_type in {
        "PTSD or trauma",
        "Depression",
        "Anxiety",
        "Distress or stress",
        "General mental health",
    }:
        return "Direct mental-health outcome"
    if outcome_type in {"Fear and safety", "Physiological", "Behavior or aggression", "Academic outcomes"}:
        return "Pathway or functional outcome"
    if outcome_type == "Violence reduction":
        return "Exposure-reduction outcome"
    if any(term in text for term in ("mental health", "depress", "anxi", "ptsd", "distress")):
        return "Direct mental-health outcome"
    return "Scope requires verification"


def classify_effect_direction(value: str) -> str:
    text = value.lower()
    if "mixed" in text:
        return "Mixed"
    protective = any(
        term in text for term in ("protective", "reduction", "reduced", "improved", "lower")
    )
    harmful = any(term in text for term in ("harm", "adverse", "worse", "increased symptoms"))
    if protective and harmful:
        return "Mixed"
    if text.strip() == "0" or any(
        term in text for term in ("null", "no significant", "not significant", "no effect")
    ):
        return "Null"
    if protective:
        return "Protective"
    if harmful:
        return "Harmful"
    return "Needs verification"


def parse_significance(value: str) -> bool | None:
    text = value.lower().strip()
    if text.startswith("yes") or text == "y":
        return True
    if text.startswith("no") or text == "n":
        return False
    return None


def classify_exposure_type(value: str) -> str:
    text = value.lower()
    objective = any(term in text for term in ("objective", "administrative", "police", "geocod"))
    perceived = any(term in text for term in ("perceived", "self-report", "self report"))
    if objective and perceived:
        return "Mixed objective and subjective"
    if objective:
        return "Objective"
    if perceived:
        return "Subjective"
    return "Needs verification"


def classify_geographic_scale(value: str) -> str:
    text = value.lower()
    if any(term in text for term in ("250 m", "500 m", "0.5 mile", "half-mile")):
        return "250-500 m"
    if any(term in text for term in ("1 mile", "one mile", "1,000 m")):
        return "500 m-1 mile"
    if "block" in text or "lot" in text:
        return "Block or parcel"
    if "school" in text:
        return "School or district"
    if any(term in text for term in ("neighborhood", "census tract", "community")):
        return "Neighborhood or administrative area"
    if any(term in text for term in ("city", "county", "municipal")):
        return "County or municipality"
    if "not applicable" in text:
        return "Not spatial"
    return "Other or variable"


def build_record(raw: dict[str, str], source_row: int) -> dict[str, Any]:
    study_id = raw["study_id"]
    year = extract_year(study_id, raw["study_title"])
    age_min, age_max = parse_age_bounds(raw["age_range"])
    design_type, causal_reason = classify_design(
        raw["design_type_raw"],
        raw["causal_identification_strategy"],
    )
    intervention_class = classify_intervention(raw["intervention_type_raw"])
    outcome_type = classify_outcome(
        raw["mental_health_outcomes"],
        raw["outcome_instrument"],
    )
    directness = classify_outcome_directness(outcome_type, raw["mental_health_outcomes"])
    effect_direction = classify_effect_direction(raw["effect_direction_raw"])
    evidence_role = (
        "Symptom recovery"
        if intervention_class == "Psychosocial"
        else "Exposure reduction"
    )
    if effect_direction in {"Mixed", "Null", "Harmful"}:
        decision_relevance = "Conditional or mixed evidence"
    elif directness == "Direct mental-health outcome":
        decision_relevance = "Supports consideration with contextual adaptation"
    elif directness == "Exposure-reduction outcome":
        decision_relevance = "Supports exposure-reduction decisions"
    else:
        decision_relevance = "Mechanistic or implementation insight"

    flags = [
        "Full journal citation is not provided in a dedicated source column.",
        "DOI or source URL is not provided in the source workbook.",
        "A standardized effect size is not provided in a dedicated source column.",
        "Confidence interval bounds are not provided in dedicated source columns.",
        "Outcome directness was classified from the extracted outcome narrative.",
    ]
    if age_min is None and age_max is None:
        flags.append("Numeric age bounds could not be parsed from the source age field.")
    if intervention_class == "Needs verification":
        flags.append("Intervention class requires manual verification.")
    if directness == "Scope requires verification":
        flags.append("The relationship between the outcome and youth mental health requires verification.")

    return {
        "slug": f"iv-{slugify(study_id)}",
        "study_id": study_id,
        "title": raw["study_title"],
        "citation": study_id,
        "publication_year": year,
        "country": raw["country"].rstrip("."),
        "age_range": raw["age_range"],
        "age_min": age_min,
        "age_max": age_max,
        "age_groups": classify_age_groups(raw["age_range"], age_min, age_max),
        "design_type": design_type,
        "design_raw": raw["design_type_raw"],
        "causal_tier": "Credible",
        "causal_tier_reason": causal_reason,
        "quality_tier": classify_quality(raw["risk_of_bias_raw"]),
        "risk_of_bias_raw": raw["risk_of_bias_raw"],
        "exposure_type": classify_exposure_type(raw["exposure_measure"]),
        "exposure_window": "Intervention follow-up",
        "exposure_window_raw": raw["exposure_window_raw"],
        "geographic_scale": classify_geographic_scale(
            f"{raw['exposure_window_raw']} {raw['intervention_description']}"
        ),
        "outcome_type": outcome_type,
        "outcomes": raw["mental_health_outcomes"],
        "outcome_measure": raw["outcome_instrument"],
        "outcome_unit_scale": raw["outcome_unit_scale"],
        "effect_direction": effect_direction,
        "effect_direction_raw": raw["effect_direction_raw"],
        "statistically_significant": parse_significance(
            raw["statistically_significant_raw"]
        ),
        "statistically_significant_raw": raw["statistically_significant_raw"],
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": (
            "[NEEDS VERIFICATION] Exact estimates and confidence intervals remain in the "
            "narrative extraction and require effect-level coding before quantitative synthesis."
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
        "intervention_type": raw["intervention_type_raw"],
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": sorted(set(flags)),
        "raw_fields": raw,
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 2,
        "added_in_version": "2.0",
        "evidence_role": evidence_role,
        "intervention_class": intervention_class,
        "outcome_directness": directness,
        "decision_relevance": decision_relevance,
        "source_review": "Intervention systematic review (Paper 2)",
        "search_coverage_end": "2025-07-31",
        "source_row": source_row,
    }


def main() -> None:
    workbook = openpyxl.load_workbook(SOURCE, read_only=True, data_only=True)
    sheet = workbook.active
    headers = [clean_text(sheet.cell(1, column).value) for column in range(1, 35)]
    if len(headers) != len(RAW_FIELD_NAMES):
        raise ValueError(f"Expected 34 source columns. Found {len(headers)}.")

    records: list[dict[str, Any]] = []
    for row_number in range(2, sheet.max_row + 1):
        values = [
            clean_text(sheet.cell(row_number, column).value)
            for column in range(1, 35)
        ]
        if not values[0]:
            continue
        if values[0].lower() in SECTION_LABELS:
            continue
        if not values[1]:
            continue
        raw = dict(zip(RAW_FIELD_NAMES, values, strict=True))
        records.append(build_record(raw, row_number))

    if len(records) != 26:
        raise ValueError(f"Expected 26 intervention studies. Found {len(records)}.")
    slugs = [record["slug"] for record in records]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Generated intervention slugs are not unique.")

    OUTPUT.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "studies": len(records),
                "structural": sum(
                    record["intervention_class"] == "Structural"
                    for record in records
                ),
                "psychosocial": sum(
                    record["intervention_class"] == "Psychosocial"
                    for record in records
                ),
                "direct_mental_health": sum(
                    record["outcome_directness"] == "Direct mental-health outcome"
                    for record in records
                ),
                "output": str(OUTPUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
