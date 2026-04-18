from tests.helpers import auth_header, register_and_get_token


def test_patch_pool_size_too_small_returns_422(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "preferred_pool_size": 9,
    }, headers=auth_header(token))
    assert resp.status_code == 422


def test_patch_pool_size_too_large_returns_422(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "preferred_pool_size": 201,
    }, headers=auth_header(token))
    assert resp.status_code == 422


def test_patch_pool_size_boundary_min(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "preferred_pool_size": 10,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["preferred_pool_size"] == 10


def test_patch_pool_size_boundary_max(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "preferred_pool_size": 200,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["preferred_pool_size"] == 200


def test_patch_empty_body_returns_200(client):
    # Empty update should succeed (no-op)
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={}, headers=auth_header(token))
    assert resp.status_code == 200


def test_patch_unknown_field_ignored(client):
    # Extra fields should be ignored by Pydantic.
    token = register_and_get_token(client)
    resp = client.patch("/api/users/me", json={
        "email": "hacker@evil.com",
        "full_name": "Safe Name",
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Safe Name"
    # email should not have changed
    profile = client.get("/api/users/me", headers=auth_header(token)).json()
    assert profile["email"] != "hacker@evil.com"
