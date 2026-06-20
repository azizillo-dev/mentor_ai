"""
Integration tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import STUDENT_DATA, TEACHER_DATA


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    async def test_register_student_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json=STUDENT_DATA)
        assert response.status_code == 201

        body = response.json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == STUDENT_DATA["email"]
        assert body["data"]["user"]["role"] == "student"
        assert "access_token" in body["data"]["token"]
        assert "hashed_password" not in str(body)

    async def test_register_teacher_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json=TEACHER_DATA)
        assert response.status_code == 201

        body = response.json()
        assert body["data"]["user"]["role"] == "teacher"

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json=STUDENT_DATA)
        response = await client.post("/api/v1/auth/register", json=STUDENT_DATA)
        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        payload = {**STUDENT_DATA, "password": "nodigits"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        payload = {**STUDENT_DATA, "email": "not-an-email"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_short_name(self, client: AsyncClient):
        payload = {**STUDENT_DATA, "full_name": "A"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json=STUDENT_DATA)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": STUDENT_DATA["email"], "password": STUDENT_DATA["password"]},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert "access_token" in body["data"]["token"]
        assert body["data"]["token"]["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json=STUDENT_DATA)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": STUDENT_DATA["email"], "password": "wrongpass1"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "password1"},
        )
        assert response.status_code == 401

    async def test_login_returns_same_error_for_wrong_email_or_password(
        self, client: AsyncClient
    ):
        """Verify user enumeration prevention: same error for wrong email/pass."""
        await client.post("/api/v1/auth/register", json=STUDENT_DATA)

        resp_wrong_pass = await client.post(
            "/api/v1/auth/login",
            json={"email": STUDENT_DATA["email"], "password": "wrongpass1"},
        )
        resp_wrong_email = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": STUDENT_DATA["password"]},
        )
        assert resp_wrong_pass.status_code == resp_wrong_email.status_code == 401
        assert resp_wrong_pass.json()["detail"] == resp_wrong_email.json()["detail"]


class TestGetMe:
    """Tests for GET /api/v1/users/me"""

    async def test_get_me_success(self, client: AsyncClient):
        reg = await client.post("/api/v1/auth/register", json=STUDENT_DATA)
        token = reg.json()["data"]["token"]["access_token"]

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["email"] == STUDENT_DATA["email"]

    async def test_get_me_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401
