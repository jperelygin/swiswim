from uuid import uuid4
from tests.helpers import register_and_get_token, auth_header


def _create_exercise(client, token, **overrides):
    payload = {
        "name": f"Ex {uuid4().hex[:6]}",
        "short_name": f"E{uuid4().hex[:4]}",
        "style": "freestyle",
        "distance_meters": 100,
        **overrides,
    }
    resp = client.post("/api/exercises", json=payload, headers=auth_header(token))
    return resp


def test_create_exercise_admin(client, admin_token):
    resp = _create_exercise(client, admin_token)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["style"] == "freestyle"
    assert data["distance_meters"] == 100


def test_create_exercise_forbidden_for_regular_user(client):
    token = register_and_get_token(client)
    resp = _create_exercise(client, token)
    assert resp.status_code == 403


def test_list_exercises(client, admin_token):
    token = register_and_get_token(client)
    # Create some exercises as admin
    _create_exercise(client, admin_token, style="backstroke", name="List Back 1", short_name="LB1")
    _create_exercise(client, admin_token, style="freestyle", name="List Free 1", short_name="LF1")

    resp = client.get("/api/exercises", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["exercises"]) >= 2


def test_list_exercises_filter_style(client, admin_token):
    token = register_and_get_token(client)
    _create_exercise(client, admin_token, style="butterfly", name="Filter Fly 1", short_name="FF1")

    resp = client.get("/api/exercises?style=butterfly", headers=auth_header(token))
    assert resp.status_code == 200
    for ex in resp.json()["exercises"]:
        assert ex["style"] == "butterfly"


def test_list_exercises_search(client, admin_token):
    token = register_and_get_token(client)
    _create_exercise(client, admin_token, name="Unique Searchable Name", short_name="USN")

    resp = client.get("/api/exercises?search=Unique Searchable", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    assert "Unique Searchable" in resp.json()["exercises"][0]["name"]


def test_get_exercise_detail(client, admin_token):
    token = register_and_get_token(client)
    create_resp = _create_exercise(
        client, admin_token,
        name="Detail Test Ex",
        short_name="DTE",
        content_markdown="# Hello",
    )
    exercise_id = create_resp.json()["id"]

    resp = client.get(f"/api/exercises/{exercise_id}", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == exercise_id
    assert data["content_markdown"] == "# Hello"


def test_get_exercise_not_found(client):
    token = register_and_get_token(client)
    fake_id = str(uuid4())
    resp = client.get(f"/api/exercises/{fake_id}", headers=auth_header(token))
    assert resp.status_code == 404


def test_list_exercises_no_auth(client):
    resp = client.get("/api/exercises")
    assert resp.status_code == 401
