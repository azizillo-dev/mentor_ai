"""
Homework API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.homework import HomeworkCreate, HomeworkResponse, HomeworkUpdate
from app.services.homework_service import HomeworkService

router = APIRouter(prefix="/homeworks", tags=["Homeworks"])


def get_homework_service(db: AsyncSession = Depends(get_db)) -> HomeworkService:
    return HomeworkService(db)


@router.post(
    "",
    response_model=HomeworkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi uy vazifasi yaratish",
    description="Faqat Teacher roliga ega foydalanuvchilar o'z guruhlari uchun uy vazifasi yarata oladi.",
)
async def create_homework(
    data: HomeworkCreate,
    current_user: User = Depends(get_current_user),
    service: HomeworkService = Depends(get_homework_service),
) -> HomeworkResponse:
    return await service.create_homework(data, current_user)


@router.get(
    "",
    response_model=list[HomeworkResponse],
    summary="Barcha uy vazifalarini olish",
    description="Teacher o'zi rahbarlik qiladigan barcha guruhlardagi uy vazifalarini ko'rishi mumkin.",
)
async def get_homeworks(
    current_user: User = Depends(get_current_user),
    service: HomeworkService = Depends(get_homework_service),
) -> list[HomeworkResponse]:
    return await service.get_homeworks(current_user)


@router.get(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Uy vazifasini ID orqali olish",
    description="Faqat o'qituvchiga tegishli uy vazifasini olish mumkin.",
)
async def get_homework(
    homework_id: UUID,
    current_user: User = Depends(get_current_user),
    service: HomeworkService = Depends(get_homework_service),
) -> HomeworkResponse:
    return await service.get_homework_by_id(homework_id, current_user)


@router.patch(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Uy vazifasi ma'lumotlarini o'zgartirish",
    description="Uy vazifasi nomi, ta'rifi yoki muddatini tahrirlash (faqat teacher).",
)
async def update_homework(
    homework_id: UUID,
    data: HomeworkUpdate,
    current_user: User = Depends(get_current_user),
    service: HomeworkService = Depends(get_homework_service),
) -> HomeworkResponse:
    return await service.update_homework(homework_id, data, current_user)


@router.delete(
    "/{homework_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uy vazifasini o'chirish",
    description="Uy vazifasini butunlay o'chirish (faqat teacher).",
)
async def delete_homework(
    homework_id: UUID,
    current_user: User = Depends(get_current_user),
    service: HomeworkService = Depends(get_homework_service),
) -> None:
    await service.delete_homework(homework_id, current_user)
