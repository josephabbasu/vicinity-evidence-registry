from app.eligibility.classifier import RuleBasedStudyClassifier
from app.ingestion.models import NormalizedCandidate


def test_classifier_marks_strict_causal_match_eligible() -> None:
    candidate = NormalizedCandidate(
        source="fixture",
        source_id="eligible-1",
        title=(
            "Difference-in-differences study of neighborhood gun violence "
            "and adolescent mental health"
        ),
        abstract=(
            "This natural experiment examined adolescents exposed to community "
            "shootings. Outcomes included depression and anxiety."
        ),
    )
    result = RuleBasedStudyClassifier().classify(candidate)
    assert result.decision == "eligible"
    assert result.population_score >= 0.60
    assert result.exposure_score >= 0.55
    assert result.outcome_score >= 0.60
    assert result.design_score >= 0.60
    assert result.rule_trace["inferred"]["registry_stream"] == "exposure"


def test_classifier_routes_uncertain_record_to_review() -> None:
    candidate = NormalizedCandidate(
        source="fixture",
        source_id="review-1",
        title="Longitudinal study of urban youth wellbeing",
        abstract=(
            "The study followed adolescents in urban communities and measured "
            "wellbeing after exposure to crime."
        ),
    )
    result = RuleBasedStudyClassifier().classify(candidate)
    assert result.decision == "review"


def test_classifier_retains_clear_mismatch_as_ineligible() -> None:
    candidate = NormalizedCandidate(
        source="fixture",
        source_id="ineligible-1",
        title="Laboratory analysis of crop irrigation",
        abstract="The experiment measured soil moisture and plant growth.",
    )
    result = RuleBasedStudyClassifier().classify(candidate)
    assert result.decision == "ineligible"
    assert result.relevance_score < 0.25

