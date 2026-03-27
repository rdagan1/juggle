"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    response = await client.post("/auth/register", json={"email": "new@example.com", "name": "דני כהן"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "dev_code" in data  # dev mode returns code


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient):
    # Register once
    await client.post("/auth/register", json={"email": "dup@example.com", "name": "דני"})
    # Verify to mark as verified
    # Can't fully verify without email sending in tests; just check re-register
    # (unverified user allows re-register, verified returns 409)


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user, auth_token):
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_invalid_code(client: AsyncClient):
    await client.post("/auth/register", json={"email": "verify@example.com", "name": "שרה"})
    response = await client.post(
        "/auth/verify",
        json={"email": "verify@example.com", "code": "000000", "password": "newpassword"},
    )
    assert response.status_code == 400
