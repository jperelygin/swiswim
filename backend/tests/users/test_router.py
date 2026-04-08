from tests.helpers import auth_header, register_and_get_token


# ── GET /users/me ────────────────────────────────────────────────────────────

def test_get_me(client):
    token = register_and_get_token(client)
    resp = client.get("/api/users/me", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert "email" in data
    assert data["is_admin"] is False
    assert data["preferred_pool_size"] == 25


def test_get_me_no_auth(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401


# ── PATCH /users/me ──────────────────────────────────────────────────────────

def test_patch_me_full_name(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={"full_name": "Updated Name"},
                        headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


def test_patch_me_pool_size(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={"preferred_pool_size": 50},
                        headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["preferred_pool_size"] == 50


def test_patch_me_both_fields(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "full_name": "John Smith",
        "preferred_pool_size": 50,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "John Smith"
    assert data["preferred_pool_size"] == 50


def test_patch_me_persists(client):
    token = register_and_get_token(client)
    client.patch("/api/users/me", json={"full_name": "Persisted Name"},
                 headers=auth_header(token))
    resp = client.get("/api/users/me", headers=auth_header(token))
    assert resp.json()["full_name"] == "Persisted Name"


def test_patch_me_no_auth(client):
    resp = client.patch("/api/users/me", json={"full_name": "X"})
    assert resp.status_code == 401
