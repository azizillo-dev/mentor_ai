"""
AI Results API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_result import AIResultResponse
from app.services.ai_result_service import AIResultService

router = APIRouter(prefix="/ai-results", tags=["AI Results"])


def get_ai_result_service(db: AsyncSession = Depends(get_db)) -> AIResultService:
    return AIResultService(db)


@router.post(
    "/{submission_id}/analyze",
    response_model=AIResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi AI tahlilni boshlash",
    description="Faqat Teacher ushbu submissionni Gemini orqali tekshirishga yubora oladi.",
)
async def analyze_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AIResultService = Depends(get_ai_result_service),
) -> AIResultResponse:
    return await service.analyze_submission(submission_id, current_user)


@router.get(
    "/{submission_id}",
    response_model=AIResultResponse,
    summary="AI tahlil natijasini olish",
    description="Tahlil natijalarini ko'rish.",
)
async def get_ai_result(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AIResultService = Depends(get_ai_result_service),
) -> AIResultResponse:
    return await service.get_ai_result(submission_id, current_user)
