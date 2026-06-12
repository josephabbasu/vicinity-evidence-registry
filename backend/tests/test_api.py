from fastapi.testclient import TestClient

from app.main import app


def test_registry_endpoints() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        stats = client.get("/api/stats")
        assert stats.status_code == 200
        assert stats.json()["study_count"] == 32
        assert stats.json()["credible_count"] == 26
        assert stats.json()["associational_count"] == 6

        studies = client.get("/api/studies", params={"causal_tier": "Credible"})
        assert studies.status_code == 200
        assert studies.json()["total"] == 26

        first_slug = studies.json()["studies"][0]["slug"]
        detail = client.get(f"/api/studies/{first_slug}")
        assert detail.status_code == 200
        assert detail.json()["verification_count"] > 0


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
