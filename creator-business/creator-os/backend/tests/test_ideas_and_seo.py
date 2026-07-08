def test_idea_crud_and_scoring(client, auth):
    r = client.post("/ideas", json={
        "title": "Index funds explained", "pillar": "Investing From Zero",
        "demand": 9, "evergreen": 9, "competition_gap": 5, "monetization": 10, "production_ease": 8,
    }, headers=auth)
    assert r.status_code == 201
    idea = r.json()
    # 0.25*9 + 0.25*9 + 0.15*5 + 0.20*10 + 0.15*8 = 8.45
    assert idea["score"] == 8.45

    client.post("/ideas", json={"title": "Low idea", "demand": 2, "evergreen": 2,
                                "competition_gap": 2, "monetization": 2, "production_ease": 2}, headers=auth)
    ideas = client.get("/ideas", headers=auth).json()
    assert ideas[0]["title"] == "Index funds explained"  # sorted by score desc

    r = client.post("/ideas/generate", json={"pillar": "Scams & Traps", "count": 4}, headers=auth)
    assert r.status_code == 200
    assert r.json()["mode"] == "fallback"
    assert len(r.json()["created"]) == 4


def test_seo_scoring_heuristics(client, auth):
    bad = client.post("/seo/score", json={"title": "VIDEO!!", "description": "", "tags": ""}, headers=auth).json()
    good = client.post("/seo/score", json={
        "title": "How does compound interest actually work?",
        "description": "How does compound interest work? In this video you'll learn the principle, "
        "see the one chart that matters, and get a country-by-country guide to using it. "
        "Sources: listed below with links to every statistic we cite.",
        "tags": "money, compound interest, investing, saving, finance basics, interest rates, "
        "personal finance, wealth, index funds, financial literacy",
    }, headers=auth).json()
    assert good["score"] > bad["score"]
    assert good["score"] >= 80
    assert any("Sources" in s or "source" in s.lower() for s in bad["suggestions"])


def test_trends_growth_analysis(client, auth):
    r = client.post("/trends", json={"keyword": "how to budget", "category": "Saving"}, headers=auth)
    kid = r.json()["id"]
    for i, interest in enumerate([20, 22, 25, 40, 55, 60]):
        client.post(f"/trends/{kid}/points", json={"interest": interest,
                    "date": f"2026-0{i+1}-01T00:00:00Z"}, headers=auth)
    trends = client.get("/trends", headers=auth).json()
    t = next(x for x in trends if x["id"] == kid)
    assert t["growth_pct"] > 25
    assert t["momentum"] == "rising fast"
