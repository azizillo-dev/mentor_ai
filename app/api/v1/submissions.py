"""
Submission API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.submission import SubmissionResponse
from app.services.file_service import FileService
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    return SubmissionService(db)


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi javob yuborish",
    description="Faqat Student roliga ega foydalanuvchilar bitta vazifa uchun 1 marta javob (fayl) yubora oladi.",
)
async def create_submission(
    homework_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
    # Faylni saqlaymiz va path/type olamiz
    file_path, file_type = await FileService.save_upload_file(file)

    # Submission yaratamiz
    return await service.create_submission(
        homework_id=homework_id,
        file_path=file_path,
        file_type=file_type,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=list[SubmissionResponse],
    summary="Barcha javoblarni olish",
    description="Teacher o'z guruhlarining javoblarini ko'radi, Student esa o'zining javoblarini.",
)
async def get_submissions(
    current_user: User = Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
) -> list[SubmissionResponse]:
    return await service.get_submissions(current_user)


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Javobni ID orqali olish",
    description="Faqat o'qituvchiga tegishli yoki talabaning o'ziga tegishli javobni olish mumkin.",
)
async def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
    return await service.get_submission_by_id(submission_id, current_user)
