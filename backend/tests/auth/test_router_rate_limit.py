from uuid import uuid4


def test_login_rate_limit(client):
    email = f"rl_login_{uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email, "password": "StrongPass123!", "full_name": "RL User",
    })

    for _ in range(5):
        resp = client.post("/api/auth/login", json={
            "email": email, "password": "WrongPass!",
        })
        assert resp.status_code == 401

    resp = client.post("/api/auth/login", json={
        "email": email, "password": "WrongPass!",
    })
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_register_rate_limit(client):
    for _ in range(5):
        resp = client.post("/api/auth/register", json={
            "email": f"rl_reg_{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123!",
            "full_name": "RL User",
        })
        assert resp.status_code == 201

    resp = client.post("/api/auth/register", json={
        "email": f"rl_reg_{uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "RL User",
    })
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_refresh_rate_limit(client):
    for _ in range(5):
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid.token.value",
        })
        assert resp.status_code == 401

    resp = client.post("/api/auth/refresh", json={
        "refresh_token": "invalid.token.value",
    })
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]
