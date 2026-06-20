"""
Unit tests for Group endpoints and authorization logic.
"""

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


async def get_token_for_user(client: AsyncClient, user: User) -> str:
    """Helper for getting JWT token."""
    from app.core.security import create_access_token
    return create_access_token(subject=user.id)


@pytest.mark.asyncio
async def test_create_group_as_teacher(client: AsyncClient, db_session: AsyncSession):
    """Teacher can create a group."""
    teacher = await create_test_user(db_session, "teacher1@example.com", UserRole.TEACHER)
    token = await get_token_for_user(client, teacher)

    response = await client.post(
        "/api/v1/groups",
        json={"name": "Math Group", "subject": "Mathematics"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Math Group"
    assert data["subject"] == "Mathematics"
    assert "id" in data
    assert data["teacher_id"] == teacher.id


@pytest.mark.asyncio
async def test_create_group_as_student(client: AsyncClient, db_session: AsyncSession):
    """Student cannot create a group."""
    student = await create_test_user(db_session, "student1@example.com", UserRole.STUDENT)
    token = await get_token_for_user(client, student)

    response = await client.post(
        "/api/v1/groups",
        json={"name": "Physics Group", "subject": "Physics"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_groups(client: AsyncClient, db_session: AsyncSession):
    """Teacher can view only their own groups."""
    teacher1 = await create_test_user(db_session, "teacher2@example.com", UserRole.TEACHER)
    teacher2 = await create_test_user(db_session, "teacher3@example.com", UserRole.TEACHER)
    
    token1 = await get_token_for_user(client, teacher1)
    token2 = await get_token_for_user(client, teacher2)

    # Teacher 1 creates 2 groups
    await client.post("/api/v1/groups", json={"name": "T1 Group 1"}, headers={"Authorization": f"Bearer {token1}"})
    await client.post("/api/v1/groups", json={"name": "T1 Group 2"}, headers={"Authorization": f"Bearer {token1}"})

    # Teacher 2 creates 1 group
    await client.post("/api/v1/groups", json={"name": "T2 Group 1"}, headers={"Authorization": f"Bearer {token2}"})

    # Fetch Teacher 1 groups
    response = await client.get("/api/v1/groups", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(g["teacher_id"] == teacher1.id for g in data)


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient, db_session: AsyncSession):
    """Teacher can update their own group."""
    teacher = await create_test_user(db_session, "teacher4@example.com", UserRole.TEACHER)
    token = await get_token_for_user(client, teacher)

    # Create
    create_resp = await client.post(
        "/api/v1/groups",
        json={"name": "Old Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = create_resp.json()["id"]

    # Update
    update_resp = await client.patch(
        f"/api/v1/groups/{group_id}",
        json={"name": "New Name", "subject": "Biology"},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "New Name"
    assert data["subject"] == "Biology"


@pytest.mark.asyncio
async def test_update_others_group_forbidden(client: AsyncClient, db_session: AsyncSession):
    """Teacher cannot update another teacher's group."""
    teacher1 = await create_test_user(db_session, "teacher5@example.com", UserRole.TEACHER)
    teacher2 = await create_test_user(db_session, "teacher6@example.com", UserRole.TEACHER)
    
    token1 = await get_token_for_user(client, teacher1)
    token2 = await get_token_for_user(client, teacher2)

    # Teacher 1 creates group
    create_resp = await client.post(
        "/api/v1/groups",
        json={"name": "T1 Group"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    group_id = create_resp.json()["id"]

    # Teacher 2 tries to update Teacher 1's group
    update_resp = await client.patch(
        f"/api/v1/groups/{group_id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    
    assert update_resp.status_code == 404  # Not found for teacher2


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient, db_session: AsyncSession):
    """Teacher can delete their own group."""
    teacher = await create_test_user(db_session, "teacher7@example.com", UserRole.TEACHER)
    token = await get_token_for_user(client, teacher)

    # Create
    create_resp = await client.post(
        "/api/v1/groups",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = create_resp.json()["id"]

    # Delete
    delete_resp = await client.delete(
        f"/api/v1/groups/{group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    # Verify deleted
    get_resp = await client.get(
        f"/api/v1/groups/{group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404
