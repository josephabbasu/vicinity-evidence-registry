from fastapi.testclient import TestClient

from app.main import app


def test_registry_endpoints() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        stats = client.get("/api/stats")
        assert stats.status_code == 200
        # V2: 32 exposure + 26 intervention = 58 total
        assert stats.json()["study_count"] == 58
        assert stats.json()["exposure_count"] == 32
        assert stats.json()["intervention_count"] == 26
        assert stats.json()["credible_count"] >= 26

        # Exposure stream
        exposure = client.get("/api/studies", params={"stream": "exposure"})
        assert exposure.status_code == 200
        assert exposure.json()["total"] == 32

        # Intervention stream
        interventions = client.get("/api/studies", params={"stream": "intervention"})
        assert interventions.status_code == 200
        assert interventions.json()["total"] == 26

        first_slug = exposure.json()["studies"][0]["slug"]
        detail = client.get(f"/api/studies/{first_slug}")
        assert detail.status_code == 200
        assert "effect_estimates" in detail.json()


def test_practitioner_query() -> None:
    with TestClient(app) as client:
        r = client.post("/api/ask", json={"age_group": "adolescent", "outcome_type": "depression"})
        assert r.status_code == 200
        brief = r.json()
        assert "study_count" in brief
        assert "causal_certainty" in brief
        assert "available_interventions" in brief
        assert isinstance(brief["evidence_gaps"], list)


def test_gap_radar() -> None:
    with TestClient(app) as client:
        r = client.get("/api/gaps")
        assert r.status_code == 200
        data = r.json()
        assert data["total_studies"] == 58
        assert len(data["gaps"]) > 0
        assert "geographic_breakdown" in data


def test_changelog() -> None:
    with TestClient(app) as client:
        r = client.get("/api/changelog")
        assert r.status_code == 200
        entries = r.json()
        assert len(entries) == 2
        assert entries[0]["version"] == "2.0"


def test_reviewer_auth() -> None:
    with TestClient(app) as client:
        r = client.post("/api/reviewer/auth", json={"token": "vicinity-reviewer-2026"})
        assert r.status_code == 200
        assert r.json()["authenticated"] is True

        bad = client.post("/api/reviewer/auth", json={"token": "wrong"})
        assert bad.status_code == 401


def test_reviewer_dashboard_requires_auth() -> None:
    with TestClient(app) as client:
        r = client.get("/api/reviewer/dashboard")
        assert r.status_code == 401

        r = client.get("/api/reviewer/dashboard", headers={"Authorization": "Bearer vicinity-reviewer-2026"})
        assert r.status_code == 200
        dash = r.json()
        assert dash["total_studies"] == 58
        assert dash["pending_candidates"] >= 0


def test_exports() -> None:
    with TestClient(app) as client:
        csv_r = client.get("/api/export/studies.csv")
        assert csv_r.status_code == 200
        assert "study_id" in csv_r.text

        json_r = client.get("/api/export/studies.json")
        assert json_r.status_code == 200
        data = json_r.json()
        assert len(data) == 58


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
