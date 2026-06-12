"""
Generate intervention studies seed JSON from the actual Paper 2 extraction workbook.

Source: Joseph_ Intervention Systematic Review_Supplementary Extraction_Paper 2.xlsx
Output: backend/app/data/intervention_studies.json

Run from the project root:
  python scripts/generate_intervention_seed.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd


WORKBOOK = (
    r"C:\Users\josep\OneDrive\Desktop\Supplimentary list of included studies"
    r"\Systematic Review_Violence_vicinity_included_studies"
    r"\Joseph_ Intervention Systematic Review_Supplementary Extraction_Paper 2.xlsx"
)

OUTPUT = Path(__file__).resolve().parent.parent / "backend" / "app" / "data" / "intervention_studies.json"


CAUSAL_TIER_KEYWORDS = {
    "Credible": [
        "rct", "randomized", "randomised", "cluster rct", "cRCT",
        "difference-in-differences", "did", "natural experiment",
        "instrumental variable", "fixed effect", "within-person", "within-family",
        "2sls", "iv ", "quasi-experimental", "itc", "interrupted time",
    ],
    "Associational": ["regression", "logistic", "ols", "descriptive", "cross-section"],
}


def infer_causal_tier(design: str, strategy: str) -> tuple[str, str]:
    text = (design + " " + strategy).casefold()
    for tier, keywords in CAUSAL_TIER_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return tier, f"Design mentions: {design[:120]}"
    return "Associational", "No credible causal design identified in extracted fields"


QUALITY_MAP = {
    "low risk": "Low",
    "low": "Low",
    "moderate risk": "Moderate",
    "moderate": "Moderate",
    "high risk": "High",
    "high": "High",
}


def infer_quality_tier(rob: str) -> str:
    if not rob:
        return "Needs verification"
    t = rob.casefold()
    for k, v in QUALITY_MAP.items():
        if k in t:
            return v
    return "Moderate"


EFFECT_MAP = {
    "protective": "Protective",
    "beneficial": "Protective",
    "positive": "Protective",
    "improve": "Protective",
    "reduc": "Protective",
    "decrease": "Protective",
    "harmful": "Harmful",
    "deteriorat": "Harmful",
    "adverse": "Harmful",
    "worsen": "Harmful",
    "increas": "Harmful",
    "null": "Null",
    "no significant": "Null",
    "not significant": "Null",
    "mixed": "Mixed",
}


def infer_effect_direction(raw: str, findings: str) -> tuple[str, str]:
    text = (raw + " " + findings).casefold()
    for k, v in EFFECT_MAP.items():
        if k in text:
            return v, raw or findings[:200]
    return "Needs verification", raw or findings[:200]


AGE_GROUPS_MAP = [
    ((0, 9), "Children 0-9"),
    ((10, 17), "Adolescents 10-17"),
    ((18, 29), "Young adults 18-29"),
    ((30, 120), "Adults 30+"),
]


def parse_age_groups(age_str: str) -> list[str]:
    if not age_str:
        return ["Age not classifiable"]
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", age_str)]
    if not nums:
        return ["Age not classifiable"]
    lo, hi = min(nums), max(nums)
    groups = []
    for (glo, ghi), label in AGE_GROUPS_MAP:
        if lo <= ghi and hi >= glo:
            groups.append(label)
    return groups or ["Age not classifiable"]


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.casefold())
    text = re.sub(r"[\s_]+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text[:80]


OUTCOME_TYPE_MAP = {
    "ptsd": "PTSD",
    "post-traumatic": "PTSD",
    "anxiety": "Anxiety",
    "depress": "Depression",
    "mental health": "Mental health",
    "stress": "Stress",
    "behavioral": "Behavioral problems",
    "behaviour": "Behavioral problems",
    "crime": "Violence reduction",
    "violent crime": "Violence reduction",
    "shooting": "Violence reduction",
    "fear": "Fear and safety perceptions",
    "safety": "Fear and safety perceptions",
    "academic": "Academic outcomes",
    "cognitive": "Cognitive outcomes",
    "gpa": "Academic outcomes",
    "inflammation": "Physiological / biomarker",
    "cortisol": "Physiological / biomarker",
    "substance": "Substance use",
}


def infer_outcome_type(outcomes: str) -> str:
    t = outcomes.casefold()
    for k, v in OUTCOME_TYPE_MAP.items():
        if k in t:
            return v
    return "Mental health"


INTERVENTION_MAP = {
    "structural": "Structural",
    "place-based": "Structural — place-based",
    "housing": "Structural — housing",
    "demolition": "Structural — built environment",
    "greening": "Structural — built environment",
    "lighting": "Structural — built environment",
    "voucher": "Structural — housing mobility",
    "move": "Structural — housing mobility",
    "school": "Structural — school environment",
    "psychosocial": "Psychosocial",
    "cbt": "Psychosocial — trauma-focused CBT",
    "cbits": "Psychosocial — trauma-focused CBT",
    "bounce back": "Psychosocial — school-based trauma",
    "trauma": "Psychosocial — trauma-focused",
    "internet": "Psychosocial — digital/internet",
    "ipt": "Psychosocial — interpersonal therapy",
}


def infer_intervention_type(raw: str, description: str, title: str) -> str:
    text = (raw + " " + description + " " + title).casefold()
    for k, v in INTERVENTION_MAP.items():
        if k in text:
            return v
    return "Structural"


def safe(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def run():
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=0, header=0, dtype=str)
    except FileNotFoundError:
        print(f"ERROR: Workbook not found at:\n  {WORKBOOK}", file=sys.stderr)
        sys.exit(1)

    col = list(df.columns)
    print(f"Columns ({len(col)}): {col[:6]}...")

    records = []
    seen_slugs: set[str] = set()

    for i, row in df.iterrows():
        study_id = safe(row.get("Study ID", ""))
        if not study_id or study_id.startswith("Place-based") or study_id.startswith("Psychosocial"):
            continue

        title = safe(row.get("Study Title", ""))
        country = safe(row.get("Country", "")) or "United States"
        sample_size = safe(row.get("Sample Size", ""))
        age_range = safe(row.get("Age Range", ""))
        gender_race = safe(row.get("Gender/Race/Ethnicity", ""))
        design_raw = safe(row.get("Design Type (RCT, Natural Experiment, IV, DiD, FE)", ""))
        data_source = safe(row.get("Data Source", ""))
        exposure_measure = safe(row.get("Exposure Measure (Objective or Perceived)", ""))
        outcomes_raw = safe(row.get("Mental Health Outcome(s) (Primary vs Mechanistic)", ""))
        mediators = safe(row.get("Mediators/Mechanisms", ""))
        moderators = safe(row.get("Moderators (e.g., Family, Peers, Age)", ""))
        intervention_type_raw = safe(row.get("Intervention Type (structural, relational, psychosocial)", ""))
        intervention_desc = safe(row.get("Intervention Description", ""))
        findings = safe(row.get("Main Findings", ""))
        strategy = safe(row.get("Causal Identification Strategy", ""))
        rob = safe(row.get("Risk of Bias / Quality Appraisal", ""))
        strengths = safe(row.get("Strengths & Limitations", ""))
        policy = safe(row.get("Policy/Practice Implications", ""))
        reviewer_notes = safe(row.get("Reviewer Notes", ""))
        effect_dir_raw = safe(row.get("Effect Direction (Primary Outcome)", ""))
        sig_raw = safe(row.get("Statistically Significant (Primary Outcome)", ""))
        estimand = safe(row.get("Estimand: ATE / ATT / ITT / LATE", ""))
        survey_weights = safe(row.get("Survey Weights Used: Y / N", ""))
        did_trends = safe(row.get("DiD Parallel Trends Evidence", ""))
        iv_f = safe(row.get("IV First-Stage F", ""))
        outcome_instrument = safe(row.get("Outcome Instrument", ""))
        outcome_unit = safe(row.get("Outcome Unit / Scale Range", ""))
        exposure_window = safe(row.get("Exposure Window (Spatial, Temporal)", ""))
        outcome_timepoint = safe(row.get("Outcome Timepoint (relative to exposure)", ""))
        estimator = safe(row.get("Estimator", ""))
        se_clustering = safe(row.get("SE / Clustering Level", ""))
        missing_data = safe(row.get("Missing Data Method: listwise", ""))
        multiple_testing = safe(row.get("Multiple-Testing Adjustment", ""))

        base_slug = slugify(f"{study_id}")
        slug = base_slug
        counter = 2
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)

        causal_tier, causal_reason = infer_causal_tier(design_raw, strategy)
        quality_tier = infer_quality_tier(rob)
        effect_dir, effect_dir_text = infer_effect_direction(effect_dir_raw, findings)
        outcome_type = infer_outcome_type(outcomes_raw)
        intervention_type = infer_intervention_type(intervention_type_raw, intervention_desc, title)
        age_groups = parse_age_groups(age_range)

        sig = None
        if sig_raw:
            t = sig_raw.casefold()
            if t.startswith("y"):
                sig = True
            elif t.startswith("n"):
                sig = False

        # Exposure window classification
        exp_window_lower = (exposure_window + " " + intervention_desc).casefold()
        if any(w in exp_window_lower for w in ["acute", "day", "week", "month"]):
            exp_window_cat = "Acute"
        elif any(w in exp_window_lower for w in ["chronic", "longitudinal", "long", "year"]):
            exp_window_cat = "Chronic"
        else:
            exp_window_cat = "Chronic"

        finding_full = findings
        if intervention_desc and intervention_desc.casefold() not in findings.casefold():
            finding_full = f"{intervention_desc}\n\n{findings}"

        flags = []
        if not safe(row.get("IV First-Stage F", "")):
            pass
        if not outcome_instrument:
            flags.append("Outcome instrument not reported")
        if not estimand:
            flags.append("Estimand not specified")
        if not se_clustering:
            flags.append("SE clustering not reported")

        record = {
            "slug": f"iv-{slug}",
            "study_id": study_id,
            "title": title or study_id,
            "citation": study_id,
            "publication_year": None,
            "country": country,
            "age_range": age_range,
            "age_min": None,
            "age_max": None,
            "age_groups": age_groups,
            "design_type": design_raw[:120] if design_raw else "Not specified",
            "design_raw": design_raw,
            "causal_tier": causal_tier,
            "causal_tier_reason": causal_reason,
            "quality_tier": quality_tier,
            "risk_of_bias_raw": rob,
            "exposure_type": "Objective" if "objective" in exposure_measure.casefold() else "Perceived" if "perceived" in exposure_measure.casefold() else "Not specified",
            "exposure_window": exp_window_cat,
            "exposure_window_raw": exposure_window,
            "geographic_scale": "Neighborhood" if any(w in (exposure_window + design_raw).casefold() for w in ["neighborhood", "block", "community", "city", "lot"]) else "School" if "school" in (exposure_window + design_raw).casefold() else "Not specified",
            "outcome_type": outcome_type,
            "outcomes": outcomes_raw,
            "outcome_measure": outcome_instrument,
            "outcome_unit_scale": outcome_unit,
            "effect_direction": effect_dir,
            "effect_direction_raw": effect_dir_text,
            "statistically_significant": sig,
            "statistically_significant_raw": sig_raw,
            "standardized_effect_size": None,
            "ci_lower": None,
            "ci_upper": None,
            "effect_size_note": "[NEEDS VERIFICATION] Structured effect-size and CI fields not available in source extraction.",
            "sample_size": sample_size,
            "population_details": gender_race,
            "data_source": data_source,
            "exposure_measure": exposure_measure,
            "mediators_mechanisms": mediators,
            "moderators": moderators,
            "finding_summary": finding_full,
            "methodology": strategy,
            "estimand": estimand,
            "estimator": estimator,
            "se_clustering": se_clustering,
            "outcome_timepoint": outcome_timepoint,
            "missing_data_method": missing_data,
            "multiple_testing_adjustment": multiple_testing,
            "strengths_limitations": strengths,
            "policy_practice_implications": policy,
            "reviewer_notes": reviewer_notes,
            "intervention_type": intervention_type,
            "is_intervention": True,
            "doi": None,
            "source_url": None,
            "featured": False,
            "verification_flags": flags,
            "raw_fields": {
                "study_id": study_id,
                "design_type_raw": design_raw,
                "intervention_type_raw": intervention_type_raw,
                "intervention_description": intervention_desc,
                "exposure_measure": exposure_measure,
                "mental_health_outcomes": outcomes_raw,
                "effect_direction_raw": effect_dir_raw,
                "statistically_significant_raw": sig_raw,
                "estimand": estimand,
                "survey_weights": survey_weights,
                "did_parallel_trends": did_trends,
                "iv_first_stage_f": iv_f,
                "outcome_instrument": outcome_instrument,
                "outcome_unit_scale": outcome_unit,
                "exposure_window_raw": exposure_window,
                "outcome_timepoint": outcome_timepoint,
                "estimator": estimator,
                "se_clustering": se_clustering,
                "missing_data_method": missing_data,
                "multiple_testing_adjustment": multiple_testing,
            },
            "registry_stream": "intervention",
            "approval_status": "approved",
            "registry_version": 1,
            "added_in_version": "2.0",
        }
        records.append(record)

    OUTPUT.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(records)} intervention studies to:\n  {OUTPUT}")
    for r in records:
        flag = "RCT" if "Credible" in r["causal_tier"] else "Assoc."
        print(f"  [{flag}] {r['study_id'][:60]:60s} → {r['effect_direction']}")


if __name__ == "__main__":
    run()
