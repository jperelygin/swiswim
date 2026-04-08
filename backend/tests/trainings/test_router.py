from uuid import uuid4
from tests.helpers import register_and_get_token, auth_header


def _create_exercise(client, token, **overrides):
    payload = {
        "name": f"TrEx {uuid4().hex[:6]}",
        "short_name": f"TE{uuid4().hex[:3]}",
        "style": "freestyle",
        "distance_meters": 200,
        **overrides,
    }
    resp = client.post("/api/exercises", json=payload, headers=auth_header(token))
    return resp.json()


def _create_training(client, token, exercise_ids, **overrides):
    steps = [
        {
            "exercise_id": eid,
            "step_number": i + 1,
            "repetitions": 1,
            "section_type": "main",
        }
        for i, eid in enumerate(exercise_ids)
    ]
    payload = {
        "name": f"Training {uuid4().hex[:6]}",
        "level": "beginner",
        "steps": steps,
        **overrides,
    }
    resp = client.post("/api/trainings", json=payload, headers=auth_header(token))
    return resp


def test_create_training_admin(client, admin_token):
    ex = _create_exercise(client, admin_token)
    resp = _create_training(client, admin_token, [ex["id"]])
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["total_distance"] == 200
    assert len(data["steps"]) == 1
    assert data["steps"][0]["exercise_name"] == ex["name"]
    assert data["steps"][0]["repetitions"] == 1
    assert data["steps"][0]["section_type"] == "main"
    assert data["steps"][0]["distance_meters"] == 200


def test_create_training_with_repetitions(client, admin_token):
    ex = _create_exercise(client, admin_token, distance_meters=100)
    steps = [
        {
            "exercise_id": ex["id"],
            "step_number": 1,
            "repetitions": 4,
            "section_type": "warmup",
            "rest_seconds": 20,
        }
    ]
    resp = _create_training(
        client, admin_token, [], steps=steps,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_distance"] == 400
    assert data["steps"][0]["repetitions"] == 4
    assert data["steps"][0]["section_type"] == "warmup"
    assert data["steps"][0]["rest_seconds"] == 20
    assert data["steps"][0]["distance_meters"] == 400


def test_create_training_forbidden_for_regular_user(client, admin_token):
    ex = _create_exercise(client, admin_token)
    token = register_and_get_token(client)
    resp = _create_training(client, token, [ex["id"]])
    assert resp.status_code == 403


def test_list_trainings(client, admin_token):
    token = register_and_get_token(client)
    ex = _create_exercise(client, admin_token)
    _create_training(client, admin_token, [ex["id"]])

    resp = client.get("/api/trainings", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["trainings"]) >= 1


def test_list_trainings_filter_level(client, admin_token):
    token = register_and_get_token(client)
    ex = _create_exercise(client, admin_token)
    _create_training(client, admin_token, [ex["id"]], level="advanced")

    resp = client.get("/api/trainings?level=advanced", headers=auth_header(token))
    assert resp.status_code == 200
    for t in resp.json()["trainings"]:
        assert t["level"] == "advanced"


def test_get_training_detail_with_steps(client, admin_token):
    token = register_and_get_token(client)
    ex1 = _create_exercise(client, admin_token)
    ex2 = _create_exercise(client, admin_token, style="backstroke")
    create_resp = _create_training(client, admin_token, [ex1["id"], ex2["id"]])
    training_id = create_resp.json()["id"]

    resp = client.get(f"/api/trainings/{training_id}", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["steps"]) == 2
    assert data["steps"][0]["step_number"] == 1
    assert data["steps"][1]["step_number"] == 2
    assert data["steps"][0]["repetitions"] == 1
    assert data["steps"][0]["section_type"] == "main"


def test_get_training_not_found(client):
    token = register_and_get_token(client)
    resp = client.get(f"/api/trainings/{uuid4()}", headers=auth_header(token))
    assert resp.status_code == 404


def test_list_trainings_no_auth(client):
    resp = client.get("/api/trainings")
    assert resp.status_code == 401
