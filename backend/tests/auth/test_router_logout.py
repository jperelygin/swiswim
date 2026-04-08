from uuid import uuid4


def _register_and_get_tokens(client) -> dict:
    resp = client.post("/api/auth/register", json={
        "email": f"logout_{uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "John Doe",
    })
    return resp.json()


def test_logout_success(client):
    tokens = _register_and_get_tokens(client)
    resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 204


def test_logout_no_auth_header(client):
    tokens = _register_and_get_tokens(client)
    resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 401


def test_logout_then_refresh_fails(client):
    tokens = _register_and_get_tokens(client)

    # Logout revokes the refresh token
    resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 204

    # Trying to refresh with revoked token fails
    resp2 = client.post("/api/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp2.status_code == 401
