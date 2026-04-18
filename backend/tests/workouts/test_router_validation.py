from uuid import uuid4

from tests.helpers import auth_header, register_and_get_token


def test_create_workout_pool_size_too_small(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 5,
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_create_workout_pool_size_too_large(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 201,
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_create_workout_pool_size_boundary_min(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 10,
    }, headers=auth_header(user_token))
    assert resp.status_code == 201
    assert resp.json()["pool_size_meters"] == 10


def test_create_workout_pool_size_boundary_max(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 200,
    }, headers=auth_header(user_token))
    assert resp.status_code == 201
    assert resp.json()["pool_size_meters"] == 200


def test_patch_workout_pool_size_too_small(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "pool_size_meters": 9,
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_patch_workout_pool_size_too_large(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "pool_size_meters": 201,
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_get_workout_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.get("/api/workouts/not-a-uuid", headers=auth_header(token))
    assert resp.status_code == 422


def test_patch_workout_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.patch("/api/workouts/not-a-uuid", json={
        "status": "completed",
    }, headers=auth_header(token))
    assert resp.status_code == 422


def test_sync_workout_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.post("/api/workouts/not-a-uuid/sync", json={
        "status": "completed",
        "steps": [],
    }, headers=auth_header(token))
    assert resp.status_code == 422


def test_delete_workout_invalid_uuid_returns_422(client):
    token = register_and_get_token(client)
    resp = client.delete("/api/workouts/not-a-uuid", headers=auth_header(token))
    assert resp.status_code == 422


def test_patch_workout_invalid_status_value_returns_422(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "flying",
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_create_workout_missing_training_id_returns_422(client, user_token):
    resp = client.post("/api/workouts", json={
        "pool_size_meters": 25,
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_create_workout_missing_pool_size_returns_422(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
    }, headers=auth_header(user_token))
    assert resp.status_code == 422


def test_complete_then_change_status_returns_400(client, user_token, workout):
    client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "completed",
    }, headers=auth_header(user_token))
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "abandoned",
    }, headers=auth_header(user_token))
    assert resp.status_code == 400


def test_abandon_then_change_status_returns_400(client, user_token, workout):
    client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "abandoned",
    }, headers=auth_header(user_token))
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "completed",
    }, headers=auth_header(user_token))
    assert resp.status_code == 400


def test_patch_pool_size_on_completed_workout_returns_400(client, user_token, workout):
    client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "completed",
    }, headers=auth_header(user_token))
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "pool_size_meters": 50,
    }, headers=auth_header(user_token))
    assert resp.status_code == 400
