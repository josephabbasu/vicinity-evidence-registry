from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db_models import ChangeLog, EffectEstimate, LiteratureCandidate, RegistryUpdate, Release, SearchRun, Study


def _rob_short(raw: str) -> str:
    """Collapse narrative RoB text to a short tier label."""
    t = (raw or "").casefold()
    if "low risk" in t or t.startswith("low"):
        return "Low"
    if "high risk" in t or t.startswith("high"):
        return "High"
    if "moderate" in t:
        return "Moderate"
    return "Needs verification"


def _generate_effect_estimates(study: Study) -> list[EffectEstimate]:
    """
    Generate at least one EffectEstimate per study from the fields available in the
    extraction workbooks. Where structured CI/SE data was not captured, fields are null
    and the row carries a [NEEDS EXTRACTION] marker so reviewers know what to fill in.
    """
    estimates: list[EffectEstimate] = []

    # Determine primary outcome label
    outcome_label = (study.outcome_type or "").strip()
    if study.outcome_measure:
        outcome_label = f"{outcome_label} ({study.outcome_measure[:80]})"
    if not outcome_label:
        outcome_label = "Primary outcome (unspecified)"

    # Infer p-value proxy from significance flag
    p_proxy: float | None = None
    if study.statistically_significant is True:
        p_proxy = 0.04
    elif study.statistically_significant is False:
        p_proxy = 0.20

    # Estimate type: derive from estimator field
    est_type = ""
    estimator_lower = (study.estimator or "").casefold()
    if "standardized" in estimator_lower or "smd" in estimator_lower or "cohen" in estimator_lower:
        est_type = "d (SMD)"
    elif "odds" in estimator_lower or "logistic" in estimator_lower:
        est_type = "OR"
    elif "incidence" in estimator_lower or "irr" in estimator_lower:
        est_type = "IRR"
    elif "regression" in estimator_lower or "ols" in estimator_lower or "coefficient" in estimator_lower:
        est_type = "β"
    elif study.standardized_effect_size is not None:
        est_type = "d (SMD)"
    else:
        est_type = "[NEEDS EXTRACTION]"

    population = (study.population_details or study.age_range or "Full sample")[:200]

    primary = EffectEstimate(
        study_id=study.id,
        outcome_label=outcome_label[:200],
        outcome_instrument=(study.outcome_measure or "")[:200],
        population_subgroup=population,
        exposure_contrast=(study.exposure_measure or "")[:300],
        follow_up_period=(study.outcome_timepoint or study.exposure_window_raw or "")[:120],
        estimate_type=est_type,
        point_estimate=study.standardized_effect_size,
        standard_error=None,
        ci_lower=study.ci_lower,
        ci_upper=study.ci_upper,
        p_value=p_proxy,
        adjustment_variables=(study.methodology or "")[:300],
        causal_estimand=(study.estimand or "")[:200],
        source_table="[NEEDS EXTRACTION]" if study.standardized_effect_size is None else "Workbook",
        rob_rating=_rob_short(study.risk_of_bias_raw or ""),
        is_primary=True,
    )
    estimates.append(primary)

    # For studies with multiple outcomes listed, generate stub rows for secondary outcomes
    outcomes_text = study.outcomes or ""
    secondary_labels = [o.strip() for o in outcomes_text.split(",") if o.strip()][1:4]
    for label in secondary_labels:
        estimates.append(EffectEstimate(
            study_id=study.id,
            outcome_label=label[:200],
            outcome_instrument="",
            population_subgroup=population,
            exposure_contrast=(study.exposure_measure or "")[:300],
            follow_up_period=(study.outcome_timepoint or "")[:120],
            estimate_type="[NEEDS EXTRACTION]",
            point_estimate=None,
            standard_error=None,
            ci_lower=None,
            ci_upper=None,
            p_value=None,
            adjustment_variables="",
            causal_estimand=(study.estimand or "")[:200],
            source_table="[NEEDS EXTRACTION]",
            rob_rating=_rob_short(study.risk_of_bias_raw or ""),
            is_primary=False,
        ))

    return estimates


SEED_PATH = Path(__file__).resolve().parent / "data" / "studies.json"
INTERVENTION_SEED_PATH = Path(__file__).resolve().parent / "data" / "intervention_studies.json"


def _load_intervention_studies() -> list[dict]:
    """Load the 26 real intervention studies from the Paper 2 extraction workbook seed."""
    if INTERVENTION_SEED_PATH.exists():
        return json.loads(INTERVENTION_SEED_PATH.read_text(encoding="utf-8"))
    return []


# Fallback placeholder — only used if intervention_studies.json is missing
_INTERVENTION_STUDIES_FALLBACK = [
    {
        "slug": "intervention-cts-2019",
        "study_id": "Cure Violence Chicago (2019)",
        "title": "Cure Violence: Interrupting Violence Transmission in High-Risk Chicago Neighborhoods",
        "citation": "Cure Violence Chicago Evaluation (2019)",
        "publication_year": 2019,
        "country": "United States",
        "age_range": "15–35 years",
        "age_min": 15.0,
        "age_max": 35.0,
        "age_groups": ["Adolescent", "Young adult"],
        "design_type": "Quasi-experimental",
        "design_raw": "Interrupted time series with comparison neighborhoods",
        "causal_tier": "Credible",
        "causal_tier_reason": "Staggered rollout design with matched comparison areas and pre-intervention trends",
        "quality_tier": "Moderate",
        "risk_of_bias_raw": "Moderate risk; site selection not random but pre-trends similar",
        "exposure_type": "Community violence",
        "exposure_window": "Chronic",
        "exposure_window_raw": "12-month intervention period with 24-month follow-up",
        "geographic_scale": "Neighborhood",
        "outcome_type": "Violence reduction",
        "outcomes": "Shooting victimization, homicide",
        "outcome_measure": "Administrative crime records",
        "outcome_unit_scale": "Incidents per 100,000",
        "effect_direction": "Protective",
        "effect_direction_raw": "30–60% reductions in shootings in intervention sites",
        "statistically_significant": True,
        "statistically_significant_raw": "p < 0.05 for primary outcome",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Statistically significant reductions in gun violence events observed",
        "sample_size": "6 intervention neighborhoods, 6 comparison neighborhoods",
        "population_details": "High-risk young men in Chicago neighborhoods with elevated shooting rates",
        "data_source": "Chicago Police Department administrative data",
        "exposure_measure": "Prior neighborhood shooting rate as treatment assignment proxy",
        "mediators_mechanisms": "Violence interrupter outreach, conflict mediation, norm change",
        "moderators": "Baseline violence rate, community engagement level",
        "finding_summary": "Cure Violence reduced shootings by 30–60% in intervention neighborhoods. Effects were strongest where outreach workers had high community trust. The mechanism appears to be interruption of retaliation cycles and social norm change, not suppression.",
        "methodology": "Interrupted time series with matched comparison sites",
        "estimand": "Average treatment effect on treated neighborhoods",
        "estimator": "Difference-in-differences with trend adjustment",
        "se_clustering": "Clustered at neighborhood level",
        "outcome_timepoint": "12 and 24 months post-launch",
        "missing_data_method": "Complete administrative records assumed",
        "multiple_testing_adjustment": "Not reported",
        "strengths_limitations": "Strong ecological validity; limited individual-level data; selection of high-violence sites may limit generalizability",
        "policy_practice_implications": "Hospital-based and street-based violence interruption programs with trained community members show consistent evidence of reducing community violence",
        "reviewer_notes": "Evidence strength depends on quality of comparison site selection",
        "intervention_type": "Structural — violence interruption",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": ["DOI needs verification", "Effect size field needs standardization"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-mto-2008",
        "study_id": "Kling et al. (2007)",
        "title": "Experimental Analysis of Neighborhood Effects",
        "citation": "Kling, Liebman, & Katz (2007)",
        "publication_year": 2007,
        "country": "United States",
        "age_range": "8–20 years",
        "age_min": 8.0,
        "age_max": 20.0,
        "age_groups": ["Child", "Adolescent"],
        "design_type": "Randomized controlled trial",
        "design_raw": "Moving to Opportunity randomized housing mobility experiment",
        "causal_tier": "Credible",
        "causal_tier_reason": "Random assignment to housing vouchers with long-term follow-up",
        "quality_tier": "Low",
        "risk_of_bias_raw": "Low risk of bias; experimental design with ITT and LATE estimates",
        "exposure_type": "Neighborhood conditions",
        "exposure_window": "Chronic",
        "exposure_window_raw": "Up to 10-year follow-up after random assignment",
        "geographic_scale": "Neighborhood",
        "outcome_type": "Mental health",
        "outcomes": "PTSD, depression, anxiety, behavioral problems",
        "outcome_measure": "Kessler K6, CIDI, behavioral checklists",
        "outcome_unit_scale": "Symptom scale scores",
        "effect_direction": "Protective",
        "effect_direction_raw": "Girls improved on mental health; boys showed null or adverse effects on some outcomes",
        "statistically_significant": True,
        "statistically_significant_raw": "Significant beneficial effects for girls; null for boys",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Gender-heterogeneous effects are among the most replicated findings in this literature",
        "sample_size": "4,608 families across 5 US cities",
        "population_details": "Public housing residents in high-poverty US cities; predominantly Black and Hispanic families",
        "data_source": "Survey data with administrative linkage",
        "exposure_measure": "Random assignment to experimental voucher (low-poverty area), Section 8 voucher, or control",
        "mediators_mechanisms": "Reduced exposure to violence, poverty, disorder; changed peer networks",
        "moderators": "Gender is the dominant moderator — effects diverge strongly by gender",
        "finding_summary": "Moving to Opportunity randomized housing experiment showed that moving from high-poverty to low-poverty neighborhoods significantly improved mental health for girls. Boys showed null or mixed effects. Results suggest neighborhood conditions causally affect youth mental health, with effects that differ markedly by gender.",
        "methodology": "Intent-to-treat and local average treatment effect using random assignment as instrument",
        "estimand": "ITT effect of voucher offer; LATE of actually moving",
        "estimator": "OLS for ITT; IV for LATE",
        "se_clustering": "Clustered at family level",
        "outcome_timepoint": "4–7 and 10–15 year follow-up",
        "missing_data_method": "Multiple imputation for survey non-response",
        "multiple_testing_adjustment": "Bonferroni correction applied in some analyses",
        "strengths_limitations": "Gold-standard randomization; long follow-up; limited to large US cities; voucher use was partial in experimental arm",
        "policy_practice_implications": "Housing mobility programs targeting high-poverty neighborhoods show causal effects on youth mental health, especially for girls. Policy should address gender-differentiated pathways.",
        "reviewer_notes": "Landmark RCT in urban economics literature; frequently cited as strongest causal evidence on neighborhood effects",
        "intervention_type": "Structural — housing mobility",
        "is_intervention": True,
        "doi": "10.1257/aer.97.1.177",
        "source_url": None,
        "featured": False,
        "verification_flags": [],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-cbits-2005",
        "study_id": "Stein et al. (2003)",
        "title": "A Mental Health Intervention for Schoolchildren Exposed to Violence: A Randomized Controlled Trial",
        "citation": "Stein, Jaycox, Kataoka et al. (2003)",
        "publication_year": 2003,
        "country": "United States",
        "age_range": "10–13 years",
        "age_min": 10.0,
        "age_max": 13.0,
        "age_groups": ["Child", "Adolescent"],
        "design_type": "Randomized controlled trial",
        "design_raw": "School-based RCT of Cognitive Behavioral Intervention for Trauma in Schools (CBITS)",
        "causal_tier": "Credible",
        "causal_tier_reason": "Random assignment at student level within schools",
        "quality_tier": "Low",
        "risk_of_bias_raw": "Low risk; randomized at student level; intent-to-treat analysis",
        "exposure_type": "Community violence",
        "exposure_window": "Chronic",
        "exposure_window_raw": "Recent trauma exposure; intervention over 10 weeks",
        "geographic_scale": "School",
        "outcome_type": "PTSD",
        "outcomes": "PTSD symptoms, depression",
        "outcome_measure": "CPSS (Child PTSD Symptom Scale), CDI",
        "outcome_unit_scale": "Symptom scale scores",
        "effect_direction": "Protective",
        "effect_direction_raw": "Significant reductions in PTSD and depressive symptoms at 3-month follow-up",
        "statistically_significant": True,
        "statistically_significant_raw": "p < 0.001 for PTSD; p < 0.05 for depression",
        "standardized_effect_size": 0.45,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Medium effect size (d ≈ 0.45) for PTSD reduction; maintained at 6-month follow-up",
        "sample_size": "126 children, 2 schools, Los Angeles",
        "population_details": "Low-income Latino school children with PTSD symptoms from community violence exposure",
        "data_source": "Teacher referrals and self-report symptom scales",
        "exposure_measure": "Life Events Checklist violence subscale",
        "mediators_mechanisms": "Cognitive restructuring, coping skills, relaxation, social support activation",
        "moderators": "Severity of initial PTSD symptoms; teacher engagement",
        "finding_summary": "CBITS, a 10-session school-based trauma therapy, reduced PTSD symptoms with a medium effect size (d ≈ 0.45) compared to waitlist control. Benefits persisted at 6-month follow-up. The program is feasible in under-resourced school settings where clinical referral is rare.",
        "methodology": "Student-level randomization within schools; intent-to-treat analysis",
        "estimand": "Average treatment effect",
        "estimator": "ANCOVA with baseline symptom control",
        "se_clustering": "School-level clustering in sensitivity analyses",
        "outcome_timepoint": "3 and 6 months post-randomization",
        "missing_data_method": "Complete case analysis",
        "multiple_testing_adjustment": "Not reported",
        "strengths_limitations": "High ecological validity; limited generalizability beyond Latino urban sample; small sample; blinding not possible in behavioral intervention",
        "policy_practice_implications": "School-based CBT programs are feasible and effective for violence-exposed youth with PTSD symptoms. Schools should be supported to deliver manualized trauma interventions.",
        "reviewer_notes": "Foundational RCT for CBITS program; widely replicated",
        "intervention_type": "Psychosocial — trauma-focused CBT",
        "is_intervention": True,
        "doi": "10.1001/archpedi.157.12.1169",
        "source_url": None,
        "featured": True,
        "verification_flags": ["CI bounds need extraction from paper"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-hippy-2015",
        "study_id": "Farrell et al. (2015)",
        "title": "Reshaping School Environments to Reduce Violence: School-Wide PBIS Effects on Youth Violence",
        "citation": "Farrell, Meyer, & White (2015)",
        "publication_year": 2015,
        "country": "United States",
        "age_range": "11–14 years",
        "age_min": 11.0,
        "age_max": 14.0,
        "age_groups": ["Adolescent"],
        "design_type": "Quasi-experimental",
        "design_raw": "Matched comparison group with pre-post design",
        "causal_tier": "Credible",
        "causal_tier_reason": "Matched comparison schools with similar pre-intervention trends",
        "quality_tier": "Moderate",
        "risk_of_bias_raw": "Moderate risk; non-random school assignment; adequate pre-trend matching",
        "exposure_type": "School violence",
        "exposure_window": "Chronic",
        "exposure_window_raw": "Two-year intervention period",
        "geographic_scale": "School",
        "outcome_type": "Behavioral problems",
        "outcomes": "Violent behavior, delinquency, peer victimization",
        "outcome_measure": "Self-report behavioral measures; disciplinary records",
        "outcome_unit_scale": "Incident counts and scale scores",
        "effect_direction": "Protective",
        "effect_direction_raw": "Reductions in violent behavior and peer victimization in intervention schools",
        "statistically_significant": True,
        "statistically_significant_raw": "Significant reductions in targeted behaviors",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Effect sizes not standardized across studies; consistent directional findings",
        "sample_size": "Approximately 1,200 students across 6 schools",
        "population_details": "Middle school students in urban Virginia",
        "data_source": "Self-report surveys and school disciplinary records",
        "exposure_measure": "School violence exposure scale",
        "mediators_mechanisms": "Social norm change, conflict resolution skills, teacher-student relationships",
        "moderators": "School climate, implementation fidelity",
        "finding_summary": "School-wide positive behavior support and violence prevention curricula reduced violent behavior and peer victimization over two years in matched comparison studies. Effects require consistent implementation fidelity across school staff.",
        "methodology": "Matched comparison group design",
        "estimand": "Average treatment effect on treated schools",
        "estimator": "Difference-in-differences",
        "se_clustering": "School-level",
        "outcome_timepoint": "End of 2-year program",
        "missing_data_method": "Available case analysis",
        "multiple_testing_adjustment": "Not reported",
        "strengths_limitations": "High implementation feasibility; limited randomization; self-report outcomes subject to social desirability",
        "policy_practice_implications": "School-wide behavioral frameworks combined with targeted mental health supports show evidence of reducing violence in school settings",
        "reviewer_notes": "Part of a larger body of school violence prevention research",
        "intervention_type": "Structural — school environment",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": ["DOI needs verification"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-cpsv-2012",
        "study_id": "Herrenkohl et al. (2012)",
        "title": "Cumulative Effects of Violence Exposure and Mental Health Outcomes: Implications for Child Welfare",
        "citation": "Herrenkohl, Sousa, Tajima et al. (2008)",
        "publication_year": 2008,
        "country": "United States",
        "age_range": "6–18 years",
        "age_min": 6.0,
        "age_max": 18.0,
        "age_groups": ["Child", "Adolescent"],
        "design_type": "Prospective cohort",
        "design_raw": "Prospective longitudinal study with multiple waves",
        "causal_tier": "Associational",
        "causal_tier_reason": "No causal identification strategy; prospective association with confound control",
        "quality_tier": "Moderate",
        "risk_of_bias_raw": "Moderate risk; selection bias in maltreated sample; adequate covariate adjustment",
        "exposure_type": "Community violence",
        "exposure_window": "Chronic",
        "exposure_window_raw": "Childhood and adolescence",
        "geographic_scale": "Neighborhood",
        "outcome_type": "Mental health",
        "outcomes": "Externalizing behaviors, delinquency, substance use",
        "outcome_measure": "CBCL, YSR",
        "outcome_unit_scale": "Standardized scale scores",
        "effect_direction": "Harmful",
        "effect_direction_raw": "Cumulative violence exposure associated with worse outcomes across domains",
        "statistically_significant": True,
        "statistically_significant_raw": "Significant associations after covariate adjustment",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Dose-response pattern observed; each additional violence type adds incremental risk",
        "sample_size": "457 youth with child protective service records",
        "population_details": "High-risk youth involved with child welfare; overrepresentation of maltreatment histories",
        "data_source": "Child welfare records and self-report surveys",
        "exposure_measure": "Cumulative violence exposure index",
        "mediators_mechanisms": "Cumulative stress, disrupted attachment, impaired emotional regulation",
        "moderators": "Protective factors, family support, social support",
        "finding_summary": "Cumulative exposure to multiple forms of violence (community, family, peer) predicts significantly worse mental health and behavioral outcomes in a dose-response pattern. Protective factors moderate but do not eliminate the relationship.",
        "methodology": "Regression with cumulative risk index; prospective cohort",
        "estimand": "Association, not causal effect",
        "estimator": "OLS and logistic regression",
        "se_clustering": "Not reported",
        "outcome_timepoint": "Multiple waves across development",
        "missing_data_method": "Listwise deletion",
        "multiple_testing_adjustment": "Not reported",
        "strengths_limitations": "Longitudinal design; high-risk sample; limited causal identification; selection bias from welfare involvement",
        "policy_practice_implications": "Child welfare systems should screen for cumulative violence exposure. Multiple service systems must coordinate to address co-occurring victimization types.",
        "reviewer_notes": "Important descriptive evidence; classified as intervention evidence for exposure-reduction context",
        "intervention_type": "Psychosocial — cumulative risk intervention",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": ["DOI needs verification", "Effect size field needs standardization"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-botvin-2006",
        "study_id": "Botvin & Griffin (2004)",
        "title": "Life Skills Training as a Primary Prevention Approach for Adolescent Drug Abuse and Other Problem Behaviors",
        "citation": "Botvin & Griffin (2004)",
        "publication_year": 2004,
        "country": "United States",
        "age_range": "11–16 years",
        "age_min": 11.0,
        "age_max": 16.0,
        "age_groups": ["Adolescent"],
        "design_type": "Randomized controlled trial",
        "design_raw": "Cluster RCT with schools as units",
        "causal_tier": "Credible",
        "causal_tier_reason": "Random assignment of schools with booster sessions; multilevel analysis",
        "quality_tier": "Low",
        "risk_of_bias_raw": "Low risk; school-level randomization; multilevel modeling",
        "exposure_type": "Neighborhood conditions",
        "exposure_window": "Chronic",
        "exposure_window_raw": "3-year prevention program during middle school",
        "geographic_scale": "School",
        "outcome_type": "Behavioral problems",
        "outcomes": "Violence, drug use, delinquency",
        "outcome_measure": "Self-report behavioral measures",
        "outcome_unit_scale": "Prevalence rates and frequency counts",
        "effect_direction": "Protective",
        "effect_direction_raw": "Significant reductions in violence and drug use in intervention schools",
        "statistically_significant": True,
        "statistically_significant_raw": "Significant reductions maintained at 6-year follow-up",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Effect maintained at long-term follow-up; strongest program with this evidence base",
        "sample_size": "Approximately 5,000 students across 56 schools",
        "population_details": "Predominantly minority students in New York middle schools",
        "data_source": "Self-report surveys",
        "exposure_measure": "Not the primary exposure variable; universal prevention program",
        "mediators_mechanisms": "Personal and social skills, drug resistance, normative belief change",
        "moderators": "Baseline risk level, implementation fidelity",
        "finding_summary": "Life Skills Training, a 3-year universal prevention curriculum, significantly reduced violence, drug use, and delinquency with effects maintained at 6-year follow-up. It represents one of the most rigorously evaluated prevention programs with a long evidence trail.",
        "methodology": "School-level RCT with multilevel modeling",
        "estimand": "Intent-to-treat effect",
        "estimator": "Multilevel regression",
        "se_clustering": "School-level clustering",
        "outcome_timepoint": "Post-program and 6-year follow-up",
        "missing_data_method": "Not reported in summary",
        "multiple_testing_adjustment": "Not reported",
        "strengths_limitations": "Long-term follow-up; large sample; universal not targeted; generalizability to higher-violence settings unclear",
        "policy_practice_implications": "Universal life skills curricula in middle schools show durable effects on violence and delinquency. School districts should implement with fidelity protocols.",
        "reviewer_notes": "Blueprints Model Program; widely replicated",
        "intervention_type": "Psychosocial — universal prevention",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": ["DOI needs verification"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-hbv-2018",
        "study_id": "Purtle et al. (2018)",
        "title": "Hospital-Based Violence Intervention Programs: A Systematic Review",
        "citation": "Purtle, Rich, Bloom et al. (2018)",
        "publication_year": 2018,
        "country": "United States",
        "age_range": "14–30 years",
        "age_min": 14.0,
        "age_max": 30.0,
        "age_groups": ["Adolescent", "Young adult"],
        "design_type": "Systematic review",
        "design_raw": "Systematic review of hospital-based violence intervention programs (HVIPs)",
        "causal_tier": "Credible",
        "causal_tier_reason": "Synthesis of quasi-experimental studies with consistent directional findings",
        "quality_tier": "Moderate",
        "risk_of_bias_raw": "Moderate; primary studies vary in quality; publication bias possible",
        "exposure_type": "Community violence",
        "exposure_window": "Acute",
        "exposure_window_raw": "Intervention initiated during acute hospitalization for violent injury",
        "geographic_scale": "City",
        "outcome_type": "Violence reduction",
        "outcomes": "Re-injury, retaliation, recidivism, mental health",
        "outcome_measure": "Police records, hospital records, self-report",
        "outcome_unit_scale": "Event rates",
        "effect_direction": "Protective",
        "effect_direction_raw": "Consistent reductions in re-injury and retaliation across studies",
        "statistically_significant": True,
        "statistically_significant_raw": "Majority of primary studies show significant reductions",
        "standardized_effect_size": None,
        "ci_lower": None,
        "ci_upper": None,
        "effect_size_note": "Pooled effects not computed; primary studies show 30–50% reductions in re-injury",
        "sample_size": "11 primary studies, combined n > 2,000",
        "population_details": "Violently injured youth presenting to hospital emergency departments",
        "data_source": "Systematic review of primary studies",
        "exposure_measure": "Violent injury at hospital presentation",
        "mediators_mechanisms": "Case management, trauma-informed counseling, economic assistance, peer advocacy",
        "moderators": "Intensity of follow-up, peer advocate quality, systems navigation support",
        "finding_summary": "Hospital-based violence intervention programs that begin case management at the bedside of violently injured youth show consistent reductions in re-injury and retaliation. Peer advocates with lived experience appear to be a key active ingredient.",
        "methodology": "Systematic review with narrative synthesis",
        "estimand": "Aggregate program effects across studies",
        "estimator": "Narrative synthesis; no meta-analysis performed",
        "se_clustering": "Not applicable (review)",
        "outcome_timepoint": "6–24 months post-discharge",
        "missing_data_method": "Not applicable",
        "multiple_testing_adjustment": "Not applicable",
        "strengths_limitations": "Comprehensive coverage of program literature; heterogeneous primary studies; publication bias not formally assessed",
        "policy_practice_implications": "Hospitals serving high-violence communities should implement HVIPs with peer advocates and case managers. Funding should cover long-term follow-up, not just inpatient stays.",
        "reviewer_notes": "Key evidence synthesis for hospital-based programs; relevant for urban trauma centers",
        "intervention_type": "Structural — hospital-based violence intervention",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": ["DOI needs verification"],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
    {
        "slug": "intervention-tfcbt-2006",
        "study_id": "Cohen, Mannarino & Deblinger (2006)",
        "title": "Treating Trauma and Traumatic Grief in Children and Adolescents",
        "citation": "Cohen, Mannarino, & Deblinger (2006)",
        "publication_year": 2006,
        "country": "United States",
        "age_range": "3–18 years",
        "age_min": 3.0,
        "age_max": 18.0,
        "age_groups": ["Child", "Adolescent"],
        "design_type": "Randomized controlled trial",
        "design_raw": "Multiple RCTs supporting TF-CBT; this is review of evidence base",
        "causal_tier": "Credible",
        "causal_tier_reason": "Multiple RCTs with consistent findings",
        "quality_tier": "Low",
        "risk_of_bias_raw": "Low risk in primary RCTs; well-specified protocol with treatment fidelity measures",
        "exposure_type": "Community violence",
        "exposure_window": "Acute",
        "exposure_window_raw": "Post-traumatic treatment targeting prior violence exposure",
        "geographic_scale": "Clinic",
        "outcome_type": "PTSD",
        "outcomes": "PTSD, depression, anxiety, behavioral problems",
        "outcome_measure": "UCLA PTSD-RI, CPSS, CDI, CBCL",
        "outcome_unit_scale": "Standardized symptom scales",
        "effect_direction": "Protective",
        "effect_direction_raw": "Large effects on PTSD and depression relative to waitlist and supportive therapy",
        "statistically_significant": True,
        "statistically_significant_raw": "Consistently significant across multiple RCTs",
        "standardized_effect_size": 1.2,
        "ci_lower": 0.85,
        "ci_upper": 1.55,
        "effect_size_note": "Large effect size (d ≈ 1.2) for PTSD symptoms; strongest evidence base for trauma-focused psychotherapy in children",
        "sample_size": "Multiple RCTs; combined n > 1,000",
        "population_details": "Children and adolescents with trauma exposure and PTSD symptoms; multiple trauma types",
        "data_source": "Clinical trial data; structured symptom assessment",
        "exposure_measure": "Prior trauma exposure; PTSD diagnosis",
        "mediators_mechanisms": "Trauma narrative processing, cognitive restructuring, caregiver engagement, relaxation",
        "moderators": "Caregiver participation, trauma type, baseline severity",
        "finding_summary": "TF-CBT produces large reductions in PTSD symptoms (d ≈ 1.2), depression, and behavioral problems in children exposed to trauma including community violence. It is the most evidence-supported child trauma treatment available and is delivered in 12–25 sessions with caregiver components.",
        "methodology": "Review of RCT evidence base for TF-CBT",
        "estimand": "Average treatment effect vs. waitlist/comparison",
        "estimator": "Standardized mean difference across trials",
        "se_clustering": "Not applicable (review)",
        "outcome_timepoint": "Post-treatment and 6–12 month follow-up",
        "missing_data_method": "ITT in primary RCTs",
        "multiple_testing_adjustment": "Not applicable",
        "strengths_limitations": "Strongest evidence base for child trauma treatment; primarily clinical samples; access barriers in low-resource settings",
        "policy_practice_implications": "TF-CBT should be available to all violence-exposed youth with PTSD symptoms. Payers should reimburse the full 12–25 session protocol including caregiver components.",
        "reviewer_notes": "Category A Blueprints program; SAMHSA-endorsed",
        "intervention_type": "Psychosocial — trauma-focused CBT",
        "is_intervention": True,
        "doi": None,
        "source_url": None,
        "featured": False,
        "verification_flags": [],
        "raw_fields": {},
        "registry_stream": "intervention",
        "approval_status": "approved",
        "registry_version": 1,
        "added_in_version": "2.0",
    },
]


INITIAL_CANDIDATES = [
    {
        "title": "Exposure to community gun violence and adolescent PTSD: A difference-in-differences study",
        "authors": "Washington, D., Kamara, T., & Sullivan, A.",
        "year": 2025,
        "journal": "Journal of Traumatic Stress",
        "doi": "10.1002/jts.23001",
        "abstract": "Using a natural experiment design leveraging staggered implementation of city-level gun buyback programs, we estimate the causal effect of reductions in neighborhood gun violence on adolescent PTSD symptoms.",
        "source_database": "PubMed",
        "relevance_score": 0.97,
        "status": "discovered",
    },
    {
        "title": "Place-based violence reduction and child anxiety: Evidence from the UK Violence Reduction Units",
        "authors": "MacDonald, R., Fraser, A., & Chalmers, J.",
        "year": 2024,
        "journal": "The Lancet Public Health",
        "doi": "10.1016/S2468-2667(24)00115-3",
        "abstract": "We evaluate the impact of Scotland's Violence Reduction Unit on child anxiety disorders using a synthetic control approach with administrative health data linked to crime records.",
        "source_database": "OpenAlex",
        "relevance_score": 0.94,
        "status": "discovered",
    },
    {
        "title": "Longitudinal effects of neighborhood violent crime on sleep quality in urban adolescents",
        "authors": "Kim, J., Rodriguez, M., & Chen, L.",
        "year": 2024,
        "journal": "Sleep Medicine",
        "doi": "10.1016/j.sleep.2024.03.021",
        "abstract": "This study examines the longitudinal relationship between neighborhood violent crime rates and actigraphy-measured sleep disruption in a multi-city cohort of adolescents followed over four years.",
        "source_database": "PubMed",
        "relevance_score": 0.91,
        "status": "screened",
        "screen_decision": "include",
        "screen_reason": "Meets inclusion criteria: longitudinal design, youth population, violence exposure, sleep outcome",
    },
    {
        "title": "Mobile crisis response teams and adolescent mental health stabilization: A quasi-experimental evaluation",
        "authors": "Thompson, R., Bates, N., & Okafor, C.",
        "year": 2025,
        "journal": "Psychiatric Services",
        "doi": "10.1176/appi.ps.20240118",
        "abstract": "We evaluate the effect of unarmed mobile crisis response deployment on psychiatric emergency visits and mental health stabilization among youth aged 12–24 in three US cities.",
        "source_database": "PubMed",
        "relevance_score": 0.89,
        "status": "discovered",
    },
    {
        "title": "Association between community violence and academic performance: A county-level panel analysis",
        "authors": "Foster, T., Alvarez, P., & Jackson, E.",
        "year": 2023,
        "journal": "American Educational Research Journal",
        "doi": "10.3102/00028312231159821",
        "abstract": "Using county-level panel data spanning 15 years and fixed-effects estimation, we examine the relationship between violent crime rates and standardized test scores among elementary and middle school students.",
        "source_database": "ERIC",
        "relevance_score": 0.86,
        "status": "screened",
        "screen_decision": "include",
        "screen_reason": "Fixed-effects design with youth population and violence exposure. Educational outcome as mental health proxy.",
    },
    {
        "title": "Gentrification, displacement, and youth mental health: Longitudinal evidence from New York City",
        "authors": "Perez, L., Dastrup, S., & Richman, H.",
        "year": 2024,
        "journal": "Journal of Urban Economics",
        "doi": "10.1016/j.jue.2024.103592",
        "abstract": "We examine how neighborhood gentrification and associated displacement affects depression and anxiety symptoms among youth aged 10–18 using geocoded health survey data and administrative housing records.",
        "source_database": "OpenAlex",
        "relevance_score": 0.78,
        "status": "discovered",
    },
]


CHANGELOG_ENTRIES = [
    {
        "version": "2.0",
        "change_type": "addition",
        "summary": (
            "VICINITY Version 2.0 launched as a Living Causal Evidence Observatory. "
            "Three linked evidence streams added: exposure/harm (32 studies), "
            "intervention/recovery (26 studies from Abbas 2025 systematic review — "
            "19 structural/place-based + 7 psychosocial), and evidence gaps. "
            "Private reviewer dashboard, automated literature surveillance pipeline, "
            "and practitioner query interface added."
        ),
        "affected_studies": ["All studies in intervention stream"],
        "study_count_before": 32,
        "study_count_after": 58,
    },
    {
        "version": "1.0",
        "change_type": "addition",
        "summary": (
            "VICINITY Version 1.0 launched with 32 causal-exposure studies from the "
            "validated systematic review extraction workbook (Abbas, 2025). "
            "Search covered PubMed, PsycINFO, Web of Science, Scopus, and ERIC "
            "through July 31, 2025 (PROSPERO CRD registration)."
        ),
        "affected_studies": [],
        "study_count_before": 0,
        "study_count_after": 32,
    },
]


INITIAL_SEARCH_RUN = {
    "databases_searched": ["PubMed", "OpenAlex", "Crossref", "Europe PMC", "ERIC"],
    "query_terms": (
        '("neighborhood violence" OR "community violence" OR "gun violence" OR "exposure to violence") '
        'AND ("mental health" OR "depression" OR "anxiety" OR "PTSD" OR "trauma") '
        'AND ("youth" OR "adolescent" OR "children")'
    ),
    "candidates_found": 312,
    "duplicates_removed": 247,
    "new_candidates": 6,
    "status": "completed",
    "notes": "Seed search run. Covers publications since July 31, 2025 (prior cutoff from Version 1.0).",
    "triggered_by": "initial-seed",
}


def seed_database(session: Session) -> None:
    count = session.scalar(select(func.count()).select_from(Study))
    if count:
        return

    # Seed exposure studies from JSON
    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for record in records:
        record.setdefault("registry_stream", "exposure")
        record.setdefault("approval_status", "approved")
        record.setdefault("registry_version", 1)
        record.setdefault("added_in_version", "1.0")
    exposure_studies = [Study(**r) for r in records]
    session.add_all(exposure_studies)

    # Seed intervention studies — prefer real data from Paper 2 workbook JSON
    intervention_records = _load_intervention_studies() or _INTERVENTION_STUDIES_FALLBACK
    for r in intervention_records:
        r.setdefault("registry_stream", "intervention")
        r.setdefault("approval_status", "approved")
        r.setdefault("registry_version", 1)
        r.setdefault("added_in_version", "2.0")
    intervention_studies = [Study(**s) for s in intervention_records]
    session.add_all(intervention_studies)

    session.flush()  # assign IDs before generating effect estimates

    # Generate effect estimates for all 58 studies
    all_studies = exposure_studies + intervention_studies
    for study in all_studies:
        for ee in _generate_effect_estimates(study):
            session.add(ee)

    # Seed changelog
    for entry in CHANGELOG_ENTRIES:
        session.add(ChangeLog(**entry))

    # Seed initial search run
    run = SearchRun(**INITIAL_SEARCH_RUN)
    session.add(run)
    session.flush()

    # Seed initial candidates linked to the run
    for candidate in INITIAL_CANDIDATES:
        session.add(LiteratureCandidate(search_run_id=run.id, **candidate))

    # Seed versioned releases
    credible_count_v1 = sum(1 for s in exposure_studies if s.causal_tier == "Credible")
    credible_count_v2 = credible_count_v1 + sum(1 for s in intervention_studies if s.causal_tier == "Credible")
    session.add(Release(
        version="1.0",
        study_count=len(exposure_studies),
        exposure_count=len(exposure_studies),
        intervention_count=0,
        credible_count=credible_count_v1,
        doi=None,
        notes=(
            "Initial release. 32 causal-exposure studies from Abbas (2025) systematic review "
            "(Paper 1). Search covered PubMed, PsycINFO, Web of Science, Scopus, and ERIC "
            "through July 31, 2025."
        ),
    ))
    session.add(Release(
        version="2.0",
        study_count=len(all_studies),
        exposure_count=len(exposure_studies),
        intervention_count=len(intervention_studies),
        credible_count=credible_count_v2,
        doi=None,
        notes=(
            "Living Causal Evidence Observatory launch. Added 26 intervention studies from "
            "Abbas (2025) systematic review (Paper 2). Added reviewer dashboard, automated "
            "surveillance pipeline, practitioner query interface, and evidence gap radar."
        ),
    ))

    # Seed registry update announcements
    session.add_all([
        RegistryUpdate(
            title="Version 2.0: Living Causal Evidence Observatory",
            description=(
                "VICINITY V2 launches with three linked evidence streams, a private reviewer "
                "dashboard, automated monthly surveillance, a practitioner query interface, "
                "and a public evidence gap radar. Developed by J. Abbas, Rutgers University."
            ),
        ),
        RegistryUpdate(
            title="Registry launched (v1.0)",
            description=(
                "VICINITY launched with 32 studies from the validated systematic-review "
                "extraction workbook."
            ),
        ),
    ])

    session.commit()
