from uuid import uuid4


def _register_user(client) -> dict:
    resp = client.post("/api/auth/register", json={
        "email": f"login_{uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "John Doe",
    })
    return resp.json()


def test_login_success(client):
    user = _register_user(client)
    resp = client.post("/api/auth/login", json={
        "email": user["email"],
        "password": "StrongPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    user = _register_user(client)
    resp = client.post("/api/auth/login", json={
        "email": user["email"],
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


def test_login_nonexistent_email(client):
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "StrongPass123!",
    })
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"
