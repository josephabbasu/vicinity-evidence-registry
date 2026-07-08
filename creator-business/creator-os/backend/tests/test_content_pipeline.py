def make_video(client, auth, title="Compound interest, explained"):
    r = client.post("/videos", json={"title": title, "pillar": "Money Foundations"}, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_pipeline_enforces_fact_check_gate(client, auth):
    vid = make_video(client, auth)

    # idea -> researched (AI fallback populates the brief)
    r = client.post(f"/videos/{vid}/research", headers=auth)
    assert r.status_code == 200
    assert r.json()["mode"] == "fallback"
    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.json()["status"] == "researched"

    # researched -> scripted
    r = client.post(f"/videos/{vid}/script", headers=auth)
    assert r.status_code == 200
    assert "[CLAIM]" in r.json()["script"]
    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.json()["status"] == "scripted"

    # Cannot reach fact_checked with zero claims
    # (fallback script contains [CLAIM] markers; extract them first via factcheck)
    r = client.post(f"/videos/{vid}/factcheck", headers=auth)
    assert r.status_code == 200
    assert r.json()["claims_extracted"] >= 1

    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.json()["status"] == "fact_checked"

    # Blocked: unverified claims must stop the move to voiced
    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.status_code == 409
    assert "verification gate" in r.json()["detail"]

    # Verify all claims (requires a source URL)
    video = client.get(f"/videos/{vid}", headers=auth).json()
    for claim in video["claims"]:
        r = client.patch(
            f"/videos/{vid}/claims/{claim['id']}",
            json={"status": "verified"},
            headers=auth,
        )
        assert r.status_code == 409  # no source URL yet
        r = client.patch(
            f"/videos/{vid}/claims/{claim['id']}",
            json={"status": "verified", "source_url": "https://example.org/source"},
            headers=auth,
        )
        assert r.status_code == 200

    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.status_code == 200
    assert r.json()["status"] == "voiced"


def test_scheduling_requires_timestamp(client, auth):
    vid = make_video(client, auth)
    client.post(f"/videos/{vid}/research", headers=auth)
    client.post(f"/videos/{vid}/advance", headers=auth)
    client.post(f"/videos/{vid}/script", headers=auth)
    client.post(f"/videos/{vid}/advance", headers=auth)
    client.post(f"/videos/{vid}/factcheck", headers=auth)
    client.post(f"/videos/{vid}/advance", headers=auth)  # fact_checked
    video = client.get(f"/videos/{vid}", headers=auth).json()
    for claim in video["claims"]:
        client.patch(
            f"/videos/{vid}/claims/{claim['id']}",
            json={"status": "verified", "source_url": "https://example.org"},
            headers=auth,
        )
    for expected in ("voiced", "edited", "thumbnail"):
        r = client.post(f"/videos/{vid}/advance", headers=auth)
        assert r.json()["status"] == expected

    # thumbnail -> scheduled requires scheduled_at
    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.status_code == 409

    client.patch(f"/videos/{vid}", json={"scheduled_at": "2026-08-01T14:00:00Z"}, headers=auth)
    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.json()["status"] == "scheduled"

    r = client.post(f"/videos/{vid}/advance", headers=auth)
    assert r.json()["status"] == "published"
    assert r.json()["published_at"] is not None


def test_workflow_produce_from_idea(client, auth):
    r = client.post("/ideas", json={"title": "What is inflation?", "pillar": "The Economy Explained"}, headers=auth)
    idea_id = r.json()["id"]
    r = client.post(f"/workflows/produce/{idea_id}", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "scripted"
    assert body["claims_extracted"] >= 1
    assert body["tasks_created"] == 7

    tasks = client.get("/tasks", headers=auth).json()
    assert len(tasks) == 7
