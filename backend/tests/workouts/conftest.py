import pytest
from uuid import uuid4
from tests.helpers import auth_header, register_and_get_token


@pytest.fixture
def user_token(client):
    return register_and_get_token(client)


@pytest.fixture
def training(client, admin_token):
    """Create a minimal exercise + training, return training dict."""
    ex_resp = client.post("/api/exercises", json={
        "name": f"WO Ex {uuid4().hex[:6]}",
        "short_name": f"WE{uuid4().hex[:3]}",
        "style": "freestyle",
        "distance_meters": 100,
    }, headers=auth_header(admin_token))
    exercise_id = ex_resp.json()["id"]

    tr_resp = client.post("/api/trainings", json={
        "name": f"WO Training {uuid4().hex[:6]}",
        "level": "beginner",
        "steps": [
            {"exercise_id": exercise_id, "step_number": 1, "repetitions": 2, "section_type": "main"},
            {"exercise_id": exercise_id, "step_number": 2, "repetitions": 1, "section_type": "cooldown"},
        ],
    }, headers=auth_header(admin_token))
    return tr_resp.json()


@pytest.fixture
def workout(client, user_token, training):
    """Create a workout for user_token, return response dict."""
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 25,
    }, headers=auth_header(user_token))
    return resp.json()
