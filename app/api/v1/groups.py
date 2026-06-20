"""
Group API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from app.services.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["Groups"])


def get_group_service(db: AsyncSession = Depends(get_db)) -> GroupService:
    return GroupService(db)


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi guruh yaratish",
    description="Faqat Teacher roliga ega foydalanuvchilar guruh yarata oladi.",
)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    return await service.create_group(data, current_user)


@router.get(
    "",
    response_model=list[GroupResponse],
    summary="O'qituvchining barcha guruhlarini olish",
    description="Teacher faqat o'zi yaratgan guruhlarni ko'ra oladi.",
)
async def get_groups(
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
) -> list[GroupResponse]:
    return await service.get_groups(current_user)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Guruhni ID orqali olish",
    description="Faqat o'qituvchiga tegishli guruhni olish mumkin.",
)
async def get_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    return await service.get_group_by_id(group_id, current_user)


@router.patch(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Guruh ma'lumotlarini o'zgartirish",
    description="Guruh nomi yoki fanini tahrirlash (faqat teacher).",
)
async def update_group(
    group_id: UUID,
    data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    return await service.update_group(group_id, data, current_user)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Guruhni o'chirish",
    description="Guruhni butunlay o'chirish (faqat teacher).",
)
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
) -> None:
    await service.delete_group(group_id, current_user)
