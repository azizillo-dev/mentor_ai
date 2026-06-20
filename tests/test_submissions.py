"""
Unit tests for Submission endpoints.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def create_test_user(db_session: AsyncSession, email: str, role: UserRole) -> User:
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
    from app.core.security import create_access_token
    return create_access_token(subject=user.id)


@pytest.mark.asyncio
async def test_student_can_submit_homework(client: AsyncClient, db_session: AsyncSession):
    """Student homeworkga fayl yuklay olishi va faqat bitta marta yuklay olishi kerak."""
    teacher = await create_test_user(db_session, "sub_teacher1@example.com", UserRole.TEACHER)
    student = await create_test_user(db_session, "sub_student1@example.com", UserRole.STUDENT)
    
    teacher_token = await get_token_for_user(teacher)
    student_token = await get_token_for_user(student)

    # Teacher creates group and homework
    group_resp = await client.post(
        "/api/v1/groups", json={"name": "Sub Group"}, headers={"Authorization": f"Bearer {teacher_token}"}
    )
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "Sub HW", "deadline": deadline},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    hw_id = hw_resp.json()["id"]

    # Student submits file
    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"homework_id": hw_id}

    sub_resp = await client.post(
        "/api/v1/submissions",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert sub_resp.status_code == 201
    resp_data = sub_resp.json()
    assert resp_data["homework_id"] == hw_id
    assert resp_data["student_id"] == student.id
    assert resp_data["status"] == "PENDING"
    assert "file_path" not in resp_data  # Should not be exposed

    # Try to submit again
    files2 = {"file": ("test2.pdf", file_content, "application/pdf")}
    sub_resp2 = await client.post(
        "/api/v1/submissions",
        data=data,
        files=files2,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert sub_resp2.status_code == 400
    assert "allaqachon javob yuborgansiz" in sub_resp2.json()["detail"]


@pytest.mark.asyncio
async def test_teacher_cannot_submit(client: AsyncClient, db_session: AsyncSession):
    """Teacher submission yarata olmaydi."""
    teacher = await create_test_user(db_session, "sub_teacher2@example.com", UserRole.TEACHER)
    token = await get_token_for_user(teacher)

    group_resp = await client.post(
        "/api/v1/groups", json={"name": "Sub Group 2"}, headers={"Authorization": f"Bearer {token}"}
    )
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": group_id, "title": "Sub HW 2", "deadline": deadline},
        headers={"Authorization": f"Bearer {token}"},
    )
    hw_id = hw_resp.json()["id"]

    files = {"file": ("test.png", b"fake", "image/png")}
    data = {"homework_id": hw_id}

    sub_resp = await client.post(
        "/api/v1/submissions",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sub_resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_file_extension(client: AsyncClient, db_session: AsyncSession):
    student = await create_test_user(db_session, "sub_student2@example.com", UserRole.STUDENT)
    token = await get_token_for_user(student)

    # Use a fake homework id, validation of extension happens before homework existence check or after?
    # Actually, file validation happens first in the service layer, but it will raise 400.
    files = {"file": ("test.txt", b"text", "text/plain")}
    import uuid
    data = {"homework_id": str(uuid.uuid4())}

    sub_resp = await client.post(
        "/api/v1/submissions",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sub_resp.status_code == 400
    assert "Fayl formati noto'g'ri" in sub_resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_submissions(client: AsyncClient, db_session: AsyncSession):
    teacher = await create_test_user(db_session, "sub_teacher3@example.com", UserRole.TEACHER)
    student = await create_test_user(db_session, "sub_student3@example.com", UserRole.STUDENT)
    
    teacher_token = await get_token_for_user(teacher)
    student_token = await get_token_for_user(student)

    # create homework
    group_resp = await client.post("/api/v1/groups", json={"name": "SG"}, headers={"Authorization": f"Bearer {teacher_token}"})
    group_id = group_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks", json={"group_id": group_id, "title": "HW", "deadline": deadline}, headers={"Authorization": f"Bearer {teacher_token}"}
    )
    hw_id = hw_resp.json()["id"]

    # Student submits
    sub_resp = await client.post(
        "/api/v1/submissions",
        data={"homework_id": hw_id},
        files={"file": ("test.pdf", b"data", "application/pdf")},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    sub_id = sub_resp.json()["id"]

    # Student requests list
    resp = await client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {student_token}"})
    assert len(resp.json()) == 1

    # Teacher requests list
    resp_t = await client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {teacher_token}"})
    assert len(resp_t.json()) == 1
    assert resp_t.json()[0]["id"] == sub_id

    # Get by ID
    resp_by_id = await client.get(f"/api/v1/submissions/{sub_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert resp_by_id.status_code == 200
    assert resp_by_id.json()["id"] == sub_id
