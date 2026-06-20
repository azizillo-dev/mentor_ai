import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.group import Group
from app.models.homework import Homework
from app.core.security import hash_password
from datetime import datetime, timedelta, timezone

async def get_token_for_user(user: User) -> str:
    from app.core.security import create_access_token
    return create_access_token(subject=user.id)

@pytest.fixture
async def users(db_session: AsyncSession):
    t = User(email="t@test.com", full_name="T", hashed_password=hash_password("123"), role=UserRole.TEACHER)
    s1 = User(email="s1@test.com", full_name="S1", hashed_password=hash_password("123"), role=UserRole.STUDENT)
    s2 = User(email="s2@test.com", full_name="S2", hashed_password=hash_password("123"), role=UserRole.STUDENT)
    db_session.add_all([t, s1, s2])
    await db_session.commit()
    return t, s1, s2

@pytest.fixture
async def group(db_session: AsyncSession, users):
    t, s1, s2 = users
    g = Group(name="Test Group", teacher_id=t.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)
    return g

@pytest.fixture
async def homework(db_session: AsyncSession, group):
    hw = Homework(group_id=group.id, title="HW", description="Desc", deadline=datetime.now(timezone.utc) + timedelta(days=1))
    db_session.add(hw)
    await db_session.commit()
    await db_session.refresh(hw)
    return hw

@pytest.mark.asyncio
async def test_teacher_add_student(client: AsyncClient, users, group):
    t, s1, s2 = users
    token = await get_token_for_user(t)
    response = await client.post(f"/api/v1/groups/{group.id}/members", headers={"Authorization": f"Bearer {token}"}, json={"student_id": s1.id})
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_student_enroll(client: AsyncClient, users, group):
    t, s1, s2 = users
    token = await get_token_for_user(s2)
    response = await client.post(f"/api/v1/groups/{group.id}/enroll", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_unauthorized_submission(client: AsyncClient, users, homework):
    t, s1, s2 = users
    token = await get_token_for_user(s1)
    
    with open("tests/test_file.pdf", "wb") as f:
        f.write(b"dummy pdf content")

    with open("tests/test_file.pdf", "rb") as f:
        response = await client.post(
            f"/api/v1/submissions/{homework.id}",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test_file.pdf", f, "application/pdf")},
        )
    assert response.status_code == 403
    assert "a'zosi emassiz" in response.json()["detail"]
