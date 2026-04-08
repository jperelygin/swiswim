from uuid import uuid4


def _register_and_get_tokens(client) -> dict:
    resp = client.post("/api/auth/register", json={
        "email": f"refresh_{uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "John Doe",
    })
    return resp.json()


def test_refresh_success(client):
    tokens = _register_and_get_tokens(client)
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != tokens["refresh_token"]


def test_refresh_invalid_token(client):
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": "completely-bogus-token",
    })
    assert resp.status_code == 401


def test_refresh_reuse_revoked_token(client):
    tokens = _register_and_get_tokens(client)
    old_refresh = tokens["refresh_token"]

    # First refresh — succeeds, old token gets revoked
    resp1 = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp1.status_code == 200

    # Second refresh with same (now revoked) token — fails
    resp2 = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401
