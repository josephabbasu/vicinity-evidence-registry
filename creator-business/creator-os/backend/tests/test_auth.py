def test_register_login_me(client):
    r = client.post("/auth/register", json={
        "email": "a@b.example", "password": "longenough1", "name": "A",
    })
    assert r.status_code == 201
    token = r.json()["access_token"]

    r = client.post("/auth/register", json={"email": "a@b.example", "password": "longenough1"})
    assert r.status_code == 409

    r = client.post("/auth/login", json={"email": "a@b.example", "password": "wrong-password"})
    assert r.status_code == 401

    r = client.post("/auth/login", json={"email": "a@b.example", "password": "longenough1"})
    assert r.status_code == 200

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.example"


def test_protected_routes_require_auth(client):
    assert client.get("/ideas").status_code == 401
    assert client.get("/videos").status_code == 401
    assert client.post("/seo/score", json={"title": "x"}).status_code == 401
