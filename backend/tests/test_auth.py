"""
tests/test_auth.py
Tests for all authentication flows.
"""
import pytest


@pytest.mark.asyncio
async def test_register_new_user(client):
    resp = await client.post("/api/auth/register", json={
        "name": "Dr. Auth Test",
        "email": "authtest@example.com",
        "password": "SecurePass123",
        "role": "doctor",
        "hospital": "Test Hospital",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["email"] == "authtest@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "name": "Dr. Dup", "email": "dup@example.com",
        "password": "SecurePass123", "role": "doctor"
    }
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "name": "Dr. Login", "email": "login@example.com",
        "password": "Pass1234!", "role": "doctor"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com", "password": "Pass1234!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": "WrongPass"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "doctor"


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/api/auth/register", json={
        "name": "Dr. Refresh", "email": "refresh@example.com",
        "password": "Pass1234!", "role": "doctor"
    })
    login = await client.post("/api/auth/login", json={
        "email": "refresh@example.com", "password": "Pass1234!"
    })
    refresh_token = login.json()["data"]["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]
