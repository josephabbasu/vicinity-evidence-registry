from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..ingestion.models import NormalizedCandidate


@dataclass(slots=True)
class ClassificationResult:
    decision: str
    relevance_score: float
    population_score: float
    exposure_score: float
    outcome_score: float
    design_score: float
    notes: str
    rule_trace: dict
    model_name: str = "VICINITY rule-based eligibility classifier"
    model_version: str = "1.0"


class StudyClassifier(Protocol):
    def classify(self, candidate: NormalizedCandidate) -> ClassificationResult:
        ...


POPULATION_TERMS = {
    "adolescent": 0.35,
    "adolescents": 0.35,
    "youth": 0.35,
    "young people": 0.35,
    "young adult": 0.30,
    "child": 0.25,
    "children": 0.25,
    "student": 0.20,
    "school-aged": 0.25,
    "teen": 0.30,
    "ages 10": 0.20,
    "ages 18": 0.15,
}

VIOLENCE_TERMS = {
    "community violence": 0.40,
    "neighborhood violence": 0.45,
    "gun violence": 0.40,
    "shooting": 0.30,
    "firearm": 0.25,
    "homicide": 0.30,
    "violent crime": 0.35,
    "assault": 0.25,
    "police violence": 0.35,
    "war violence": 0.20,
    "crime exposure": 0.30,
}

PLACE_TERMS = {
    "neighborhood": 0.30,
    "community": 0.25,
    "census tract": 0.35,
    "residential": 0.20,
    "place-based": 0.35,
    "school": 0.15,
    "urban": 0.15,
    "geospatial": 0.20,
}

OUTCOME_TERMS = {
    "mental health": 0.40,
    "depression": 0.35,
    "depressive": 0.35,
    "anxiety": 0.35,
    "posttraumatic stress": 0.40,
    "post-traumatic stress": 0.40,
    "ptsd": 0.40,
    "trauma symptom": 0.30,
    "psychological distress": 0.35,
    "internalizing": 0.30,
    "externalizing": 0.25,
    "behavioral problem": 0.25,
    "suicid": 0.35,
    "resilience": 0.25,
    "well-being": 0.20,
    "wellbeing": 0.20,
    "recovery": 0.20,
}

DESIGN_TERMS = {
    "randomized controlled trial": (0.95, "Randomized controlled trial"),
    "randomised controlled trial": (0.95, "Randomized controlled trial"),
    "randomized trial": (0.90, "Randomized controlled trial"),
    "cluster randomized": (0.90, "Cluster randomized trial"),
    "difference-in-differences": (0.90, "Difference-in-differences"),
    "difference in differences": (0.90, "Difference-in-differences"),
    "regression discontinuity": (0.90, "Regression discontinuity"),
    "instrumental variable": (0.85, "Instrumental variables"),
    "natural experiment": (0.80, "Natural experiment"),
    "synthetic control": (0.85, "Synthetic control"),
    "interrupted time series": (0.80, "Interrupted time series"),
    "fixed effects": (0.65, "Fixed-effects panel design"),
    "event study": (0.75, "Event study"),
    "quasi-experiment": (0.75, "Quasi-experimental"),
    "quasi experiment": (0.75, "Quasi-experimental"),
    "longitudinal": (0.45, "Longitudinal observational"),
    "prospective cohort": (0.45, "Prospective cohort"),
    "cross-sectional": (0.20, "Cross-sectional"),
}

INTERVENTION_TERMS = {
    "intervention",
    "program",
    "programme",
    "prevention",
    "treatment",
    "therapy",
    "housing voucher",
    "neighborhood greening",
    "community-based",
    "policy",
}


def _matched_score(text: str, terms: dict[str, float]) -> tuple[float, list[str]]:
    matched = [term for term in terms if term in text]
    score = min(1.0, sum(terms[term] for term in matched))
    return round(score, 3), matched


def _design_score(text: str) -> tuple[float, str, list[str]]:
    matches = [
        (score, label, term)
        for term, (score, label) in DESIGN_TERMS.items()
        if term in text
    ]
    if not matches:
        return 0.1, "Design not reported", []
    score, label, _ = max(matches)
    return score, label, [term for _, _, term in matches]


def _infer_age_groups(text: str) -> list[str]:
    groups = []
    if any(term in text for term in ["child", "children", "school-aged"]):
        groups.append("Children 0-9")
    if any(term in text for term in ["adolescent", "youth", "teen", "student"]):
        groups.append("Adolescents 10-17")
    if "young adult" in text:
        groups.append("Young adults 18-29")
    return groups or ["Scope requires verification"]


def _infer_exposure(text: str) -> str:
    if any(term in text for term in ["gun violence", "shooting", "firearm"]):
        return "Gun violence"
    if "homicide" in text:
        return "Homicide"
    if any(term in text for term in ["assault", "violent crime"]):
        return "Violent crime"
    if "police violence" in text:
        return "Police violence"
    return "Community violence"


def _infer_outcome(text: str) -> str:
    for terms, label in [
        (["ptsd", "posttraumatic", "post-traumatic", "trauma symptom"], "PTSD / trauma"),
        (["depression", "depressive"], "Depression"),
        (["anxiety"], "Anxiety"),
        (["suicid"], "Suicidality"),
        (["externalizing", "behavioral problem"], "Behavioral problems"),
        (["resilience", "well-being", "wellbeing", "recovery"], "Resilience / wellbeing"),
    ]:
        if any(term in text for term in terms):
            return label
    return "Mental health"


class RuleBasedStudyClassifier:
    """Transparent baseline that can later be replaced by a trained model."""

    def classify(self, candidate: NormalizedCandidate) -> ClassificationResult:
        text = " ".join(
            [
                candidate.title,
                candidate.abstract,
                " ".join(candidate.keywords),
            ]
        ).casefold()
        population_score, population_matches = _matched_score(text, POPULATION_TERMS)
        violence_score, violence_matches = _matched_score(text, VIOLENCE_TERMS)
        place_score, place_matches = _matched_score(text, PLACE_TERMS)
        exposure_score = round(min(1.0, violence_score * 0.75 + place_score * 0.25), 3)
        outcome_score, outcome_matches = _matched_score(text, OUTCOME_TERMS)
        design_score, design_label, design_matches = _design_score(text)
        relevance_score = round(
            population_score * 0.25
            + exposure_score * 0.30
            + outcome_score * 0.30
            + design_score * 0.15,
            3,
        )

        strict_match = (
            population_score >= 0.60
            and exposure_score >= 0.55
            and outcome_score >= 0.60
            and design_score >= 0.60
            and relevance_score >= 0.65
        )
        failed_core_domains = sum(
            score < 0.20
            for score in [population_score, exposure_score, outcome_score]
        )
        if strict_match:
            decision = "eligible"
            notes = "The record meets all strict automated eligibility thresholds."
        elif failed_core_domains >= 2 or relevance_score < 0.25:
            decision = "ineligible"
            notes = "The record lacks evidence in at least two core eligibility domains."
        else:
            decision = "review"
            notes = "The record requires human review because one or more domains are uncertain."

        is_intervention = any(term in text for term in INTERVENTION_TERMS)
        rule_trace = {
            "matched_terms": {
                "population": population_matches,
                "violence": violence_matches,
                "place": place_matches,
                "outcome": outcome_matches,
                "design": design_matches,
            },
            "inferred": {
                "registry_stream": "intervention" if is_intervention else "exposure",
                "design_type": design_label,
                "age_groups": _infer_age_groups(text),
                "exposure_type": _infer_exposure(text),
                "outcome_type": _infer_outcome(text),
                "intervention_class": (
                    "Psychosocial"
                    if any(term in text for term in ["therapy", "counsel", "psychosocial"])
                    else "Structural"
                    if is_intervention
                    else "Not applicable"
                ),
            },
            "thresholds": {
                "population": 0.60,
                "exposure": 0.55,
                "outcome": 0.60,
                "design": 0.60,
                "relevance": 0.65,
            },
        }
        return ClassificationResult(
            decision=decision,
            relevance_score=relevance_score,
            population_score=population_score,
            exposure_score=exposure_score,
            outcome_score=outcome_score,
            design_score=design_score,
            notes=notes,
            rule_trace=rule_trace,
        )

