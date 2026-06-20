"""
Unit tests for AI Results endpoints.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import SubmissionStatus
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
@patch("app.services.ai_result_service.GeminiService.analyze_homework_submission")
async def test_analyze_submission_success(mock_analyze, client: AsyncClient, db_session: AsyncSession):
    # Mock return value
    mock_analyze.return_value = {
        "score_percent": 85.5,
        "confidence_score": 0.9,
        "summary": "Yaxshi bajarilgan",
        "strengths": ["To'g'ri formula"],
        "weaknesses": ["Kichik xato"],
        "suggestions": ["Yana takrorlash"],
        "raw_response": "{\"score_percent\": 85.5}"
    }

    teacher = await create_test_user(db_session, "ai_teacher1@example.com", UserRole.TEACHER)
    student = await create_test_user(db_session, "ai_student1@example.com", UserRole.STUDENT)
    
    t_token = await get_token_for_user(teacher)
    s_token = await get_token_for_user(student)

    # 1. Create Group & Homework
    g_resp = await client.post("/api/v1/groups", json={"name": "AI Group"}, headers={"Authorization": f"Bearer {t_token}"})
    g_id = g_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": g_id, "title": "Math", "deadline": deadline},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    hw_id = hw_resp.json()["id"]

    # 2. Student Submits
    sub_resp = await client.post(
        "/api/v1/submissions",
        data={"homework_id": hw_id},
        files={"file": ("test.pdf", b"fake", "application/pdf")},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    sub_id = sub_resp.json()["id"]

    # 3. Teacher starts AI Analysis
    ai_resp = await client.post(
        f"/api/v1/ai-results/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {t_token}"},
    )

    assert ai_resp.status_code == 201
    data = ai_resp.json()
    assert data["score_percent"] == 85.5
    assert data["summary"] == "Yaxshi bajarilgan"
    
    # Check if submission status is COMPLETED
    sub_get = await client.get(f"/api/v1/submissions/{sub_id}", headers={"Authorization": f"Bearer {t_token}"})
    assert sub_get.json()["status"] == "COMPLETED"

    # Try analyzing again -> should fail
    ai_resp2 = await client.post(
        f"/api/v1/ai-results/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    assert ai_resp2.status_code == 400


@pytest.mark.asyncio
@patch("app.services.ai_result_service.GeminiService.analyze_homework_submission")
async def test_analyze_submission_fail_json(mock_analyze, client: AsyncClient, db_session: AsyncSession):
    # Mock to raise error
    mock_analyze.side_effect = ValueError("Gemini API JSON qaytarmadi")

    teacher = await create_test_user(db_session, "ai_teacher2@example.com", UserRole.TEACHER)
    student = await create_test_user(db_session, "ai_student2@example.com", UserRole.STUDENT)
    
    t_token = await get_token_for_user(teacher)
    s_token = await get_token_for_user(student)

    # 1. Create
    g_resp = await client.post("/api/v1/groups", json={"name": "AI G2"}, headers={"Authorization": f"Bearer {t_token}"})
    g_id = g_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": g_id, "title": "Math 2", "deadline": deadline},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    hw_id = hw_resp.json()["id"]

    # 2. Submits
    sub_resp = await client.post(
        "/api/v1/submissions",
        data={"homework_id": hw_id},
        files={"file": ("test.pdf", b"fake", "application/pdf")},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    sub_id = sub_resp.json()["id"]

    # 3. Analyze fails
    ai_resp = await client.post(
        f"/api/v1/ai-results/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {t_token}"},
    )

    assert ai_resp.status_code == 500

    # Submission status should be FAILED
    sub_get = await client.get(f"/api/v1/submissions/{sub_id}", headers={"Authorization": f"Bearer {t_token}"})
    assert sub_get.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_analyze_submission_other_teacher_fails(client: AsyncClient, db_session: AsyncSession):
    # Setup teacher 1 and student
    t1 = await create_test_user(db_session, "t1@example.com", UserRole.TEACHER)
    s1 = await create_test_user(db_session, "s1@example.com", UserRole.STUDENT)
    
    t1_token = await get_token_for_user(t1)
    s1_token = await get_token_for_user(s1)

    # Setup teacher 2
    t2 = await create_test_user(db_session, "t2@example.com", UserRole.TEACHER)
    t2_token = await get_token_for_user(t2)

    # t1 creates group and homework
    g_resp = await client.post("/api/v1/groups", json={"name": "G1"}, headers={"Authorization": f"Bearer {t1_token}"})
    g_id = g_resp.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    hw_resp = await client.post(
        "/api/v1/homeworks",
        json={"group_id": g_id, "title": "HW1", "deadline": deadline},
        headers={"Authorization": f"Bearer {t1_token}"},
    )
    hw_id = hw_resp.json()["id"]

    # s1 submits
    sub_resp = await client.post(
        "/api/v1/submissions",
        data={"homework_id": hw_id},
        files={"file": ("test.pdf", b"fake", "application/pdf")},
        headers={"Authorization": f"Bearer {s1_token}"},
    )
    sub_id = sub_resp.json()["id"]

    # t2 tries to analyze -> 403
    ai_resp = await client.post(
        f"/api/v1/ai-results/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {t2_token}"},
    )
    assert ai_resp.status_code == 403


@pytest.mark.asyncio
@patch("app.services.ai_result_service.GeminiService.analyze_homework_submission")
async def test_get_ai_result_authorization(mock_analyze, client: AsyncClient, db_session: AsyncSession):
    mock_analyze.return_value = {"score_percent": 100, "confidence_score": 1, "summary": "A+", "strengths": [], "weaknesses": [], "suggestions": [], "raw_response": "{}"}
    
    t1 = await create_test_user(db_session, "t_auth1@example.com", UserRole.TEACHER)
    t2 = await create_test_user(db_session, "t_auth2@example.com", UserRole.TEACHER)
    s1 = await create_test_user(db_session, "s_auth1@example.com", UserRole.STUDENT)
    s2 = await create_test_user(db_session, "s_auth2@example.com", UserRole.STUDENT)
    
    t1_token = await get_token_for_user(t1)
    t2_token = await get_token_for_user(t2)
    s1_token = await get_token_for_user(s1)
    s2_token = await get_token_for_user(s2)

    g_resp = await client.post("/api/v1/groups", json={"name": "GAuth"}, headers={"Authorization": f"Bearer {t1_token}"})
    hw_resp = await client.post("/api/v1/homeworks", json={"group_id": g_resp.json()["id"], "title": "HW", "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()}, headers={"Authorization": f"Bearer {t1_token}"})
    
    sub_resp = await client.post("/api/v1/submissions", data={"homework_id": hw_resp.json()["id"]}, files={"file": ("t.pdf", b"f", "application/pdf")}, headers={"Authorization": f"Bearer {s1_token}"})
    sub_id = sub_resp.json()["id"]

    # t1 analyzes
    await client.post(f"/api/v1/ai-results/{sub_id}/analyze", headers={"Authorization": f"Bearer {t1_token}"})

    # s1 can view
    r1 = await client.get(f"/api/v1/ai-results/{sub_id}", headers={"Authorization": f"Bearer {s1_token}"})
    assert r1.status_code == 200

    # t1 can view
    r2 = await client.get(f"/api/v1/ai-results/{sub_id}", headers={"Authorization": f"Bearer {t1_token}"})
    assert r2.status_code == 200

    # s2 cannot view
    r3 = await client.get(f"/api/v1/ai-results/{sub_id}", headers={"Authorization": f"Bearer {s2_token}"})
    assert r3.status_code == 403

    # t2 cannot view
    r4 = await client.get(f"/api/v1/ai-results/{sub_id}", headers={"Authorization": f"Bearer {t2_token}"})
    assert r4.status_code == 403

