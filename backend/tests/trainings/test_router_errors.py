from uuid import uuid4

from tests.helpers import auth_header, register_and_get_token


def test_get_training_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/trainings/not-a-uuid", headers=auth_header(token))
    assert resp.status_code == 422


def test_create_training_invalid_level_returns_422(client, admin_token):
    resp = client.post("/api/trainings", json={
        "name": "Wrong Level",
        "level": "expert",
        "steps": [],
    }, headers=auth_header(admin_token))
    assert resp.status_code == 422


def test_create_training_missing_name_returns_422(client, admin_token):
    resp = client.post("/api/trainings", json={
        "level": "beginner",
        "steps": [],
    }, headers=auth_header(admin_token))
    assert resp.status_code == 422


def test_create_training_invalid_section_type_returns_422(client, admin_token):
    resp = client.post("/api/trainings", json={
        "name": "Wrong Section",
        "level": "beginner",
        "steps": [{
            "exercise_id": str(uuid4()),
            "step_number": 1,
            "section_type": "invalid_section",
        }],
    }, headers=auth_header(admin_token))
    assert resp.status_code == 422


def test_list_trainings_invalid_page_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/trainings?page=0", headers=auth_header(token))
    assert resp.status_code == 422


def test_list_trainings_limit_too_large_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/trainings?limit=200", headers=auth_header(token))
    assert resp.status_code == 422


def test_create_training_no_auth_returns_401(client):
    resp = client.post("/api/trainings", json={
        "name": "No Auth",
        "level": "beginner",
        "steps": [],
    })
    assert resp.status_code == 401
