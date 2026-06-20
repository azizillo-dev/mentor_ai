"""
API endpoints for Group Membership.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.group_member import GroupMemberCreate, GroupMemberResponse
from app.services.group_member_service import GroupMemberService

router = APIRouter(prefix="/groups", tags=["Group Members"])


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Guruhga o'quvchi qo'shish (Teacher)",
    description="Teacher tomonidan o'z guruhiga o'quvchini qo'shish.",
)
async def add_student(
    group_id: UUID,
    payload: GroupMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    service = GroupMemberService(db)
    member = await service.add_student(group_id, payload.student_id, current_user)
    return member  # type: ignore


@router.post(
    "/{group_id}/enroll",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Guruhga a'zo bo'lish (Student)",
    description="Student o'zi guruhga a'zo bo'lishi.",
)
async def enroll_student(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    service = GroupMemberService(db)
    member = await service.enroll_student(group_id, current_user)
    return member  # type: ignore


@router.get(
    "/{group_id}/members",
    response_model=List[GroupMemberResponse],
    summary="Guruh a'zolarini ko'rish",
    description="Teacher o'z guruhini yoki Student o'zi qatnashgan guruh a'zolarini ko'rishi.",
)
async def get_members(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GroupMemberResponse]:
    service = GroupMemberService(db)
    members = await service.get_members(group_id, current_user)
    return members  # type: ignore


@router.delete(
    "/{group_id}/members/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Guruhdan o'quvchini chetlatish (Teacher)",
)
async def remove_student(
    group_id: UUID,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = GroupMemberService(db)
    await service.remove_student(group_id, student_id, current_user)
