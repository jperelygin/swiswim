from uuid import uuid4
from fastapi.testclient import TestClient


PASSWORD = "StrongPass123!"


def register_and_get_token(client: TestClient) -> str:
    """Register a user and return the access token."""
    resp = client.post("/api/auth/register", json={
        "email": f"user_{uuid4().hex[:8]}@example.com",
        "password": PASSWORD,
        "full_name": "Test User",
    })
    return resp.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
