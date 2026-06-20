"""
Unit tests for Homework endpoints and authorization logic.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def create_test_user(db_session: AsyncSession, email: str, role: UserRole) -> User:
    """Helper for creating test users."""
    user = User(
        email=email,
        full_name=f"Test {role.value}",
        hashed_password="hashedpassword123",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def get_token_for_user(user: User) -> str:
    """Helper for getting JWT token."""
    from app.core.security import create_access_token
    return create_access_token(subject=user.id)


@pytest.mark.asyncio
async def test_create_homework_as_teacher(client: AsyncClient, db_session: AsyncSession):
    """Teacher can create homework for their own group."""
    teacher = await create_test_user(db_session, "hw_teacher1@example.com", UserRole.TEACHER)
    token = await get_token_for_user(teacher)

    # First create a group
    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "HW Group"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = group_resp.json()["id"]

    # Now create homework
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={
            "group_id": group_id,
            "title": "Math Assignment",
            "description": "Do exercises 1-10",
            "deadline": deadline,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert hw_resp.status_code == 201
    data = hw_resp.json()
    assert data["title"] == "Math Assignment"
    assert data["group_id"] == group_id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_homework_for_others_group(client: AsyncClient, db_session: AsyncSession):
    """Teacher cannot create homework for another teacher's group."""
    teacher1 = await create_test_user(db_session, "hw_teacher2@example.com", UserRole.TEACHER)
    teacher2 = await create_test_user(db_session, "hw_teacher3@example.com", UserRole.TEACHER)
    
    token1 = await get_token_for_user(teacher1)
    token2 = await get_token_for_user(teacher2)

    # Teacher 1 creates a group
    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "T1 Group"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    group_id = group_resp.json()["id"]

    # Teacher 2 tries to create homework for Teacher 1's group
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={
            "group_id": group_id,
            "title": "Hacked Assignment",
            "deadline": deadline,
        },
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert hw_resp.status_code == 404  # Group not found for teacher 2


@pytest.mark.asyncio
async def test_student_cannot_create_homework(client: AsyncClient, db_session: AsyncSession):
    """Student cannot create homework."""
    teacher = await create_test_user(db_session, "hw_teacher4@example.com", UserRole.TEACHER)
    student = await create_test_user(db_session, "hw_student1@example.com", UserRole.STUDENT)
    
    teacher_token = await get_token_for_user(teacher)
    student_token = await get_token_for_user(student)

    # Teacher creates group
    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "Student HW Group"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    group_id = group_resp.json()["id"]

    # Student tries to create homework
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={
            "group_id": group_id,
            "title": "Student Assignment",
            "deadline": deadline,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert hw_resp.status_code == 403


@pytest.mark.asyncio
async def test_get_homeworks(client: AsyncClient, db_session: AsyncSession):
    """Teacher can view only their own homeworks."""
    teacher = await create_test_user(db_session, "hw_teacher5@example.com", UserRole.TEACHER)
    token = await get_token_for_user(teacher)

    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "List HW Group"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "HW 1", "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "HW 2", "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get("/api/v1/homeworks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_homework(client: AsyncClient, db_session: AsyncSession):
    """Teacher can update their own homework."""
    teacher = await create_test_user(db_session, "hw_teacher6@example.com", UserRole.TEACHER)
    token = await get_token_for_user(teacher)

    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "Update HW Group"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "Old Title", "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )
    hw_id = hw_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/homeworks/{hw_id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_homework(client: AsyncClient, db_session: AsyncSession):
    """Teacher can delete their own homework."""
    teacher = await create_test_user(db_session, "hw_teacher7@example.com", UserRole.TEACHER)
    token = await get_token_for_user(teacher)

    group_resp = await client.post(
        "/api/v1/groups",
        json={"name": "Delete HW Group"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "To Delete", "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )
    hw_id = hw_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/homeworks/{hw_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/homeworks/{hw_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404
