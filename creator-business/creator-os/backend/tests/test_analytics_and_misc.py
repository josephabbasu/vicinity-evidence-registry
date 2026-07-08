def test_analytics_dashboard(client, auth):
    vid = client.post("/videos", json={"title": "T1"}, headers=auth).json()["id"]
    client.post("/analytics/metrics", json={
        "video_id": vid, "views": 1000, "ctr": 5.5, "avg_percentage_viewed": 52.0,
        "watch_hours": 80, "subscribers_gained": 12, "revenue": 6.4,
    }, headers=auth)
    client.post("/analytics/metrics", json={
        "video_id": vid, "views": 2000, "ctr": 6.5, "avg_percentage_viewed": 55.0,
        "watch_hours": 150, "subscribers_gained": 30, "revenue": 13.1,
    }, headers=auth)

    dash = client.get("/analytics/dashboard", headers=auth).json()
    assert dash["totals"]["views"] == 3000
    assert dash["health"]["ctr"] == "healthy"
    assert dash["health"]["retention"] == "healthy"
    assert dash["top_videos"][0]["views"] == 3000
    assert dash["pipeline"]["idea"] == 1


def test_planner_slots_and_calendar(client, auth):
    slots = client.get("/planner/next-slots", headers=auth).json()["slots"]
    assert len(slots) == 6
    assert all("T14:00:00" in s for s in slots)

    cal = client.get("/planner/calendar", headers=auth).json()
    assert cal["buffer_target_weeks"] == 3


def test_assistant_offline_fallback(client, auth):
    r = client.post("/assistant/chat", json={"message": "Suggest a title"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["model"] == "offline-fallback"


def test_prompts_knowledge_tasks(client, auth):
    r = client.post("/prompts", json={"name": "test", "purpose": "p", "body": "b"}, headers=auth)
    pid = r.json()["id"]
    assert r.json()["version"] == 1
    r = client.patch(f"/prompts/{pid}", json={"name": "test", "purpose": "p2", "body": "b2"}, headers=auth)
    assert r.json()["version"] == 2

    r = client.post("/knowledge", json={"title": "Voice", "category": "brand", "body": "..."}, headers=auth)
    assert r.status_code == 201

    r = client.post("/tasks", json={"title": "Record VO"}, headers=auth)
    tid = r.json()["id"]
    r = client.patch(f"/tasks/{tid}", json={"done": True}, headers=auth)
    assert r.json()["done"] is True


def test_competitor_tracking(client, auth):
    r = client.post("/competitors", json={"name": "Two Cents", "channel_url": "https://youtube.com/@x"}, headers=auth)
    cid = r.json()["id"]
    client.post(f"/competitors/{cid}/snapshots", json={"subscribers": 100000, "date": "2026-01-01T00:00:00Z"}, headers=auth)
    client.post(f"/competitors/{cid}/snapshots", json={"subscribers": 120000, "date": "2026-06-01T00:00:00Z"}, headers=auth)
    comps = client.get("/competitors", headers=auth).json()
    assert comps[0]["subscribers"] == 120000
    assert comps[0]["growth_pct"] == 20.0
