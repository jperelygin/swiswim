from uuid import uuid4

from tests.helpers import auth_header, register_and_get_token


def test_get_exercise_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/exercises/not-a-uuid", headers=auth_header(token))
    assert resp.status_code == 422

def test_create_exercise_invalid_style_returns_422(client, admin_token):
    resp = client.post("/api/exercises", json={
        "name": "Bad Style",
        "short_name": "BS",
        "style": "fruit_style",
        "distance_meters": 100,
    }, headers=auth_header(admin_token))
    assert resp.status_code == 422

def test_create_exercise_missing_required_fields_returns_422(client, admin_token):
    resp = client.post("/api/exercises", json={
        "name": "Incomplete",
    }, headers=auth_header(admin_token))
    assert resp.status_code == 422

def test_create_exercise_duplicate_returns_409(client, admin_token):
    name = f"Duplicate {uuid4().hex[:6]}"
    payload = {
        "name": name,
        "short_name": f"Dup{uuid4().hex[:3]}",
        "style": "freestyle",
        "distance_meters": 100,
    }
    resp1 = client.post("/api/exercises", json=payload, headers=auth_header(admin_token))
    assert resp1.status_code == 201
    resp2 = client.post("/api/exercises", json=payload, headers=auth_header(admin_token))
    assert resp2.status_code == 409

def test_list_exercises_invalid_page_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/exercises?page=0", headers=auth_header(token))
    assert resp.status_code == 422

def test_list_exercises_invalid_limit_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/exercises?limit=0", headers=auth_header(token))
    assert resp.status_code == 422

def test_list_exercises_limit_too_large_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/exercises?limit=101", headers=auth_header(token))
    assert resp.status_code == 422
