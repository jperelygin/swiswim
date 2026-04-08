from uuid import uuid4


def _unique_email() -> str:
    return f"reg_{uuid4().hex[:8]}@example.com"


def test_register_success(client):
    email = _unique_email()
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Jane Doe",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["full_name"] == "Jane Doe"
    assert "user_id" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    email = _unique_email()
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Jane Doe",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409
    assert "already registered" in resp2.json()["detail"].lower()


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "StrongPass123!",
        "full_name": "Jane Doe",
    })
    assert resp.status_code == 422
