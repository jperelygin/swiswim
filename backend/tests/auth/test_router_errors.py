from uuid import uuid4
from datetime import datetime, timedelta, UTC
from jose import jwt

import backend.config
from tests.helpers import auth_header, register_and_get_token


def test_expired_access_token_returns_401(client):
    payload = {
        "sub": str(uuid4()),
        "role": "user",
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "access",
    }
    expired_token = jwt.encode(payload, backend.config.settings.jwt_secret_key, 
                               algorithm=backend.config.settings.jwt_algorithm)
    resp = client.get("/api/users/me", headers=auth_header(expired_token))
    assert resp.status_code == 401

def test_wrong_secret_token_returns_401(client):
    payload = {
        "sub": str(uuid4()),
        "role": "user",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "type": "access",
    }
    bad_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
    resp = client.get("/api/users/me", headers=auth_header(bad_token))
    assert resp.status_code == 401

def test_token_missing_sub_returns_401(client):
    payload = {
        "role": "user",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "type": "access",
    }
    token = jwt.encode(payload, backend.config.settings.jwt_secret_key,
                        algorithm=backend.config.settings.jwt_algorithm)
    resp = client.get("/api/users/me", headers=auth_header(token))
    assert resp.status_code == 401

def test_refresh_type_token_rejected_as_access(client):
    payload = {
        "sub": str(uuid4()),
        "role": "user",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "type": "refresh",
    }
    token = jwt.encode(payload, backend.config.settings.jwt_secret_key,
                        algorithm=backend.config.settings.jwt_algorithm)
    resp = client.get("/api/users/me", headers=auth_header(token))
    assert resp.status_code == 401

def test_token_with_nonexistent_user_returns_401(client):
    payload = {
        "sub": str(uuid4()),
        "role": "user",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "type": "access",
    }
    token = jwt.encode(payload, backend.config.settings.jwt_secret_key,
                       algorithm=backend.config.settings.jwt_algorithm)
    resp = client.get("/api/users/me", headers=auth_header(token))
    assert resp.status_code == 401

def test_wrong_bearer_token_returns_401(client):
    resp = client.get("/api/users/me", headers={"Authorization": "Bearer bu.bu.bu"})
    assert resp.status_code == 401

def test_register_missing_full_name_returns_422(client):
    resp = client.post("/api/auth/register", json={
        "email": "x@example.com",
        "password": "StrongPass123!",
    })
    assert resp.status_code == 422

def test_register_missing_password_returns_422(client):
    resp = client.post("/api/auth/register", json={
        "email": "x@example.com",
        "full_name": "Test Testovich",
    })
    assert resp.status_code == 422

def test_register_empty_body_returns_422(client):
    resp = client.post("/api/auth/register", json={})
    assert resp.status_code == 422

def test_login_missing_email_returns_422(client):
    resp = client.post("/api/auth/login", json={"password": "x"})
    assert resp.status_code == 422

def test_login_missing_password_returns_422(client):
    resp = client.post("/api/auth/login", json={"email": "x@example.com"})
    assert resp.status_code == 422

def test_refresh_empty_body_returns_422(client):
    resp = client.post("/api/auth/refresh", json={})
    assert resp.status_code == 422

def test_refresh_invalid_token_returns_401(client):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "invalid_refresh_token"})
    assert resp.status_code == 401

def test_logout_missing_body_returns_422(client):
    token = register_and_get_token(client)
    resp = client.post("/api/auth/logout", json={}, headers=auth_header(token))
    assert resp.status_code == 422
