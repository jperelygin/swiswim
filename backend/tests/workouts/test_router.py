from uuid import uuid4
from datetime import datetime, timezone

from tests.helpers import auth_header, register_and_get_token


# ── POST /workouts ──────────────────────────────────────────────────────────

def test_create_workout(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 25,
    }, headers=auth_header(user_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["pool_size_meters"] == 25
    assert data["total_distance_planned"] == training["total_distance"]
    assert data["total_distance_completed"] == 0


def test_create_workout_training_not_found(client, user_token):
    resp = client.post("/api/workouts", json={
        "training_id": str(uuid4()),
        "pool_size_meters": 25,
    }, headers=auth_header(user_token))
    assert resp.status_code == 404


def test_create_workout_no_auth(client, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 25,
    })
    assert resp.status_code == 401


# ── GET /workouts ───────────────────────────────────────────────────────────

def test_list_workouts(client, user_token, workout):
    resp = client.get("/api/workouts", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    ids = [w["workout_id"] for w in data["workouts"]]
    assert workout["workout_id"] in ids


def test_list_workouts_filter_status(client, user_token, workout):
    resp = client.get("/api/workouts?status=in_progress", headers=auth_header(user_token))
    assert resp.status_code == 200
    for w in resp.json()["workouts"]:
        assert w["status"] == "in_progress"


def test_list_workouts_only_own(client, user_token, training):
    other_token = register_and_get_token(client)
    client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 25,
    }, headers=auth_header(other_token))

    resp = client.get("/api/workouts", headers=auth_header(user_token))
    user_workout_ids = [w["workout_id"] for w in resp.json()["workouts"]]

    resp_other = client.get("/api/workouts", headers=auth_header(other_token))
    other_workout_ids = [w["workout_id"] for w in resp_other.json()["workouts"]]

    assert not set(user_workout_ids) & set(other_workout_ids)


def test_list_workouts_no_auth(client):
    resp = client.get("/api/workouts")
    assert resp.status_code == 401


# ── GET /workouts/{workout_id} ──────────────────────────────────────────────

def test_get_workout_detail(client, user_token, workout, training):
    resp = client.get(f"/api/workouts/{workout['workout_id']}", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout_id"] == workout["workout_id"]
    assert data["pool_size_meters"] == 25
    assert len(data["steps"]) == len(training["steps"])
    assert all(s["status"] == "pending" for s in data["steps"])


def test_get_workout_not_found(client, user_token):
    resp = client.get(f"/api/workouts/{uuid4()}", headers=auth_header(user_token))
    assert resp.status_code == 404


def test_get_workout_other_user_is_404(client, user_token, workout):
    other_token = register_and_get_token(client)
    resp = client.get(f"/api/workouts/{workout['workout_id']}", headers=auth_header(other_token))
    assert resp.status_code == 404


# ── PATCH /workouts/{workout_id} ────────────────────────────────────────────

def test_patch_workout_start_time(client, user_token, workout):
    start = "2025-06-01T09:00:00Z"
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "actual_start_time": start,
    }, headers=auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["actual_start_time"] is not None


def test_patch_workout_start_time_twice_fails(client, user_token, workout):
    start = "2025-06-01T09:00:00Z"
    client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "actual_start_time": start,
    }, headers=auth_header(user_token))
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "actual_start_time": "2025-06-01T10:00:00Z",
    }, headers=auth_header(user_token))
    assert resp.status_code == 400


def test_patch_workout_complete(client, user_token, workout):
    start = "2025-06-01T09:00:00Z"
    end = "2025-06-01T10:00:00Z"
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "completed",
        "actual_start_time": start,
        "actual_end_time": end,
    }, headers=auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_patch_workout_abandon(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "abandoned",
    }, headers=auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "abandoned"


def test_patch_workout_invalid_status_transition(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "status": "in_progress",
    }, headers=auth_header(user_token))
    assert resp.status_code == 400


def test_patch_workout_pool_size(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "pool_size_meters": 50,
    }, headers=auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["pool_size_meters"] == 50


def test_patch_workout_end_time_without_status_fails(client, user_token, workout):
    resp = client.patch(f"/api/workouts/{workout['workout_id']}", json={
        "actual_end_time": "2025-06-01T10:00:00Z",
    }, headers=auth_header(user_token))
    assert resp.status_code == 400


def test_patch_workout_not_found(client, user_token):
    resp = client.patch(f"/api/workouts/{uuid4()}", json={
        "status": "completed",
    }, headers=auth_header(user_token))
    assert resp.status_code == 404


# ── POST /workouts/{workout_id}/sync ────────────────────────────────────────

def test_sync_workout(client, user_token, workout, training):
    steps = [
        {
            "step_number": s["step_number"],
            "status": "completed",
            "started_at": "2025-06-01T09:00:00Z",
            "completed_at": "2025-06-01T09:05:00Z",
            "duration_seconds": 300,
        }
        for s in training["steps"]
    ]
    resp = client.post(f"/api/workouts/{workout['workout_id']}/sync", json={
        "status": "completed",
        "actual_start_time": "2025-06-01T09:00:00Z",
        "actual_end_time": "2025-06-01T09:30:00Z",
        "steps": steps,
    }, headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["sync_status"] == "synced"
    assert data["synced_at"] is not None


def test_sync_workout_idempotent(client, user_token, workout, training):
    payload = {
        "status": "completed",
        "actual_start_time": "2025-06-01T09:00:00Z",
        "actual_end_time": "2025-06-01T09:30:00Z",
        "steps": [
            {"step_number": s["step_number"], "status": "completed"}
            for s in training["steps"]
        ],
    }
    client.post(f"/api/workouts/{workout['workout_id']}/sync", json=payload,
                headers=auth_header(user_token))
    resp = client.post(f"/api/workouts/{workout['workout_id']}/sync", json=payload,
                       headers=auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["sync_status"] == "synced"


def test_sync_workout_not_found(client, user_token):
    resp = client.post(f"/api/workouts/{uuid4()}/sync", json={
        "status": "completed",
        "steps": [],
    }, headers=auth_header(user_token))
    assert resp.status_code == 404


# ── DELETE /workouts/{workout_id} ───────────────────────────────────────────

def test_delete_workout(client, user_token, training):
    resp = client.post("/api/workouts", json={
        "training_id": training["id"],
        "pool_size_meters": 25,
    }, headers=auth_header(user_token))
    workout_id = resp.json()["workout_id"]

    resp = client.delete(f"/api/workouts/{workout_id}", headers=auth_header(user_token))
    assert resp.status_code == 204

    resp = client.get(f"/api/workouts/{workout_id}", headers=auth_header(user_token))
    assert resp.status_code == 404


def test_delete_synced_workout_fails(client, user_token, workout, training):
    client.post(f"/api/workouts/{workout['workout_id']}/sync", json={
        "status": "completed",
        "steps": [
            {"step_number": s["step_number"], "status": "completed"}
            for s in training["steps"]
        ],
    }, headers=auth_header(user_token))

    resp = client.delete(f"/api/workouts/{workout['workout_id']}", headers=auth_header(user_token))
    assert resp.status_code == 409


def test_delete_workout_not_found(client, user_token):
    resp = client.delete(f"/api/workouts/{uuid4()}", headers=auth_header(user_token))
    assert resp.status_code == 404
