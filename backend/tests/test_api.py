import os
import shutil
from pathlib import Path


TEST_DB = Path(__file__).resolve().parent / "test_vicinity.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["REVIEWER_TOKEN"] = "test-reviewer-token"
os.environ["SURVEILLANCE_TOKEN"] = "test-surveillance-token"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select

from app.database import SessionLocal
from app.db_models import LiteratureCandidate, Study
from app.ingestion.models import FetchBatch, NormalizedCandidate
from app.ingestion.pipeline import IngestionPipeline
from app.migrations import run_additive_migrations
from app import main as main_module
from app.main import app


AUTH = {"Authorization": "Bearer test-reviewer-token"}


def test_registry_endpoints() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "version": "2.0"}

        stats = client.get("/api/stats")
        assert stats.status_code == 200
        data = stats.json()
        assert data["study_count"] == 58
        assert data["exposure_count"] == 32
        assert data["intervention_count"] == 26
        assert data["structural_intervention_count"] == 19
        assert data["psychosocial_intervention_count"] == 7
        assert data["direct_mental_health_count"] >= 17
        assert data["last_search_date"] == "2025-07-31"

        exposure = client.get("/api/studies", params={"stream": "exposure"})
        assert exposure.status_code == 200
        assert exposure.json()["total"] == 32

        interventions = client.get("/api/studies", params={"stream": "intervention"})
        assert interventions.status_code == 200
        assert interventions.json()["total"] == 26
        first_intervention = interventions.json()["studies"][0]
        assert first_intervention["intervention_class"] in {"Structural", "Psychosocial"}
        assert first_intervention["outcome_directness"]
        assert first_intervention["decision_relevance"]

        first_slug = exposure.json()["studies"][0]["slug"]
        detail = client.get(f"/api/studies/{first_slug}")
        assert detail.status_code == 200
        assert detail.json()["source_review"]
        assert detail.json()["search_coverage_end"] == "2025-07-31"


def test_seed_contains_no_synthetic_candidates_or_effects() -> None:
    with TestClient(app):
        with SessionLocal() as session:
            candidates = list(session.scalars(select(LiteratureCandidate)).all())
            assert candidates == []
            effects = [
                effect
                for study in session.scalars(select(Study)).all()
                for effect in study.effect_estimates
            ]
            assert all(effect.p_value is None for effect in effects)


def test_practitioner_query() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/ask",
            json={
                "age_group": "adolescent",
                "exposure_type": "shooting",
                "outcome_type": "depression",
            },
        )
        assert response.status_code == 200
        brief = response.json()
        assert brief["causal_certainty"] in {
            "Convergent credible evidence",
            "Credible evidence with important limitations",
            "Associational evidence only",
            "No directly matched evidence",
        }
        assert isinstance(brief["evidence_gaps"], list)
        for intervention in brief["available_interventions"]:
            assert intervention["outcome_directness"]
            assert intervention["decision_relevance"]


def test_gap_radar() -> None:
    with TestClient(app) as client:
        response = client.get("/api/gaps")
        assert response.status_code == 200
        data = response.json()
        assert data["total_studies"] == 58
        assert data["stream_breakdown"] == {"exposure": 32, "intervention": 26}
        assert data["intervention_breakdown"] == {
            "Structural": 19,
            "Psychosocial": 7,
        }
        assert data["directness_breakdown"]
        assert data["gaps"]


def test_surveillance_uses_source_records_and_deduplicates(monkeypatch) -> None:
    source_record = {
        "title": "Randomized youth community violence mental health intervention",
        "authors": "Source Author",
        "year": 2026,
        "journal": "Source Journal",
        "doi": "10.0000/source-derived",
        "abstract": (
            "A randomized intervention for adolescents exposed to community "
            "violence measured depression and anxiety."
        ),
        "source_database": "PubMed",
        "source_id": "12345678",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    }
    duplicate_record = {
        **source_record,
        "source_database": "Crossref",
        "source_id": "10.0000/source-derived",
        "source_url": "https://doi.org/10.0000/source-derived",
    }
    monkeypatch.setattr(
        main_module,
        "_fetch_pubmed_candidates",
        lambda start_date, end_date: [source_record],
    )
    monkeypatch.setattr(
        main_module,
        "_fetch_crossref_candidates",
        lambda start_date, end_date: [duplicate_record],
    )

    with TestClient(app):
        with SessionLocal() as session:
            result = main_module.run_surveillance(session, "test")
            assert result["status"] == "completed"
            assert result["coverage_start"] == "2025-08-01"
            assert result["candidates_found"] == 2
            assert result["duplicates_removed"] == 1
            assert result["new_candidates"] == 1
            candidate = session.scalar(
                select(LiteratureCandidate).where(
                    LiteratureCandidate.doi == "10.0000/source-derived"
                )
            )
            assert candidate is not None
            assert candidate.source_database in {"PubMed", "Crossref"}
            assert candidate.source_url


def test_reviewer_auth_and_dual_review() -> None:
    with TestClient(app) as client:
        assert client.post(
            "/api/reviewer/auth",
            json={"token": "test-reviewer-token"},
        ).status_code == 200
        assert client.post(
            "/api/reviewer/auth",
            json={"token": "wrong"},
        ).status_code == 401
        assert client.get("/api/reviewer/dashboard").status_code == 401
        assert client.get("/api/reviewer/dashboard", headers=AUTH).status_code == 200

        with SessionLocal() as session:
            candidate = LiteratureCandidate(
                title="A real candidate used for workflow testing",
                authors="Test Author",
                year=2026,
                journal="Test Journal",
                doi="10.0000/workflow-test",
                abstract="Youth community violence and mental health.",
                source_database="PubMed",
                source_id="99999999",
                source_url="https://pubmed.ncbi.nlm.nih.gov/99999999/",
                relevance_score=0.9,
                status="discovered",
            )
            session.add(candidate)
            session.commit()
            candidate_id = candidate.id

        first = client.post(
            f"/api/reviewer/candidates/{candidate_id}/decisions",
            headers=AUTH,
            json={
                "stage": "screen",
                "decision": "include",
                "reason": "Population, exposure, and outcome match.",
                "reviewer_name": "Reviewer One",
            },
        )
        assert first.status_code == 200
        assert first.json()["status"] == "awaiting_second_screen"

        second = client.post(
            f"/api/reviewer/candidates/{candidate_id}/decisions",
            headers=AUTH,
            json={
                "stage": "screen",
                "decision": "include",
                "reason": "The abstract meets screening criteria.",
                "reviewer_name": "Reviewer Two",
            },
        )
        assert second.status_code == 200
        assert second.json()["status"] == "screened"

        fulltext_one = client.post(
            f"/api/reviewer/candidates/{candidate_id}/decisions",
            headers=AUTH,
            json={
                "stage": "fulltext",
                "decision": "include",
                "reason": "The full text meets all eligibility criteria.",
                "reviewer_name": "Reviewer One",
            },
        )
        assert fulltext_one.json()["status"] == "awaiting_second_fulltext"

        conflict = client.post(
            f"/api/reviewer/candidates/{candidate_id}/decisions",
            headers=AUTH,
            json={
                "stage": "fulltext",
                "decision": "exclude",
                "reason": "The exposure does not meet the place-based definition.",
                "reviewer_name": "Reviewer Two",
            },
        )
        assert conflict.json()["status"] == "conflict"


def test_exports_and_release() -> None:
    with TestClient(app) as client:
        csv_response = client.get("/api/export/studies.csv")
        assert csv_response.status_code == 200
        assert "outcome_directness" in csv_response.text

        json_response = client.get("/api/export/studies.json")
        assert json_response.status_code == 200
        data = json_response.json()
        assert len(data) == 58
        assert all("source_review" in record for record in data)

        release = client.get("/api/releases/2.0/download")
        assert release.status_code == 200
        assert len(release.json()) == 58


def test_submission_enters_review_queue() -> None:
    payload = {
        "citation": "Example et al. (2026)",
        "doi": "10.0000/example",
        "design_type": "Difference-in-differences",
        "population": "Adolescents ages 14-17",
        "exposure": "Neighborhood violent crime",
        "outcome": "Depressive symptoms",
        "effect_size": "Not yet standardized",
        "submitter_email": "reviewer@example.org",
    }
    with TestClient(app) as client:
        response = client.post("/api/submissions", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "pending"


def test_living_evidence_registration_synthesis_and_deactivation() -> None:
    class FixtureClient:
        configured = True

        def fetch_new_items(self, cursor):
            return FetchBatch(
                items=[
                    NormalizedCandidate(
                        source="fixture",
                        source_id="living-1",
                        title=(
                            "Difference-in-differences study of neighborhood gun "
                            "violence and adolescent mental health"
                        ),
                        authors="Researcher One",
                        year=2026,
                        journal="Living Evidence Journal",
                        doi="10.0000/living-evidence-test",
                        abstract=(
                            "This natural experiment studied adolescents exposed "
                            "to community shootings. Outcomes included depression "
                            "and anxiety."
                        ),
                        source_url="https://example.org/living-1",
                    )
                ],
                next_cursor="2026-06-13",
            )

    with TestClient(app) as client:
        with SessionLocal() as session:
            run = IngestionPipeline(
                session,
                clients={"fixture": FixtureClient()},
                auto_register=True,
            ).run("test", ["fixture"])
            assert run.status == "completed"
            assert run.eligible_count == 1
            assert run.registered_count == 1

        status_response = client.get("/admin/status/ingestion", headers=AUTH)
        assert status_response.status_code == 200
        assert status_response.json()["latest_run"]["id"] == run.id

        candidates = client.get("/admin/ingestion/candidates", headers=AUTH)
        assert candidates.status_code == 200
        candidate = next(
            item
            for item in candidates.json()["candidates"]
            if item["source_id"] == "living-1"
        )
        assert candidate["eligibility"]["decision"] == "eligible"
        assert candidate["registered_study_id"]

        filtered = client.get(
            "/admin/ingestion/candidates",
            headers=AUTH,
            params={
                "decision": "eligible",
                "source": "fixture",
                "date_from": "2020-01-01T00:00:00Z",
            },
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1

        runs = client.get("/admin/ingestion/runs", headers=AUTH)
        assert runs.status_code == 200
        assert runs.json()[0]["id"] == run.id
        events = client.get(
            f"/admin/ingestion/runs/{run.id}/events",
            headers=AUTH,
        )
        assert events.status_code == 200
        assert any(event["source"] == "fixture" for event in events.json())

        detail = client.get(
            f"/admin/ingestion/candidates/{candidate['id']}",
            headers=AUTH,
        )
        assert detail.status_code == 200
        assert detail.json()["history"][0]["model_version"] == "1.0"

        rerun = client.post(
            f"/admin/ingestion/candidates/{candidate['id']}/rerun",
            headers=AUTH,
        )
        assert rerun.status_code == 200
        assert len(rerun.json()["history"]) == 2

        brief = client.post(
            "/api/ask",
            json={"age_group": "adolescent", "outcome_type": "depression"},
        )
        assert brief.status_code == 200
        assert any(
            "Difference-in-differences study" in citation
            for citation in brief.json()["studies_included"]
        )

        study_id = candidate["registered_study_id"]
        deactivated = client.post(
            f"/admin/registry/studies/{study_id}/deactivate",
            headers=AUTH,
            json={
                "reviewer": "Integration Test",
                "reason": "Verify that inactive studies leave public synthesis.",
            },
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["is_active"] is False

        override = client.post(
            f"/admin/ingestion/candidates/{candidate['id']}/decision",
            headers=AUTH,
            json={
                "decision": "ineligible",
                "reviewer": "Integration Test",
                "reason": "The test records a human override without deleting history.",
            },
        )
        assert override.status_code == 200
        assert override.json()["eligibility"]["decision"] == "ineligible"
        assert override.json()["eligibility"]["overridden_by"] == "Integration Test"
        assert len(override.json()["history"]) == 3

        after = client.post(
            "/api/ask",
            json={"age_group": "adolescent", "outcome_type": "depression"},
        )
        assert all(
            "Difference-in-differences study" not in citation
            for citation in after.json()["studies_included"]
        )


def test_additive_migration_upgrades_existing_registry_copy(tmp_path) -> None:
    source = Path(__file__).resolve().parents[1] / "app" / "data" / "vicinity.db"
    target = tmp_path / "existing-registry.db"
    shutil.copyfile(source, target)
    migration_engine = create_engine(f"sqlite:///{target.as_posix()}")
    run_additive_migrations(migration_engine)
    study_columns = {
        column["name"] for column in inspect(migration_engine).get_columns("studies")
    }
    assert {
        "is_active",
        "automation_status",
        "ingestion_candidate_id",
        "created_at",
        "updated_at",
    }.issubset(study_columns)


def test_background_ingestion_endpoint_queues_work() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/admin/ingestion/run",
            headers=AUTH,
            json={
                "sources": ["unknown-test-source"],
                "triggered_by": "background-test",
                "background": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        with SessionLocal() as session:
            run = session.get(
                main_module.IngestionRun,
                response.json()["id"],
            )
            assert run.status == "completed"
