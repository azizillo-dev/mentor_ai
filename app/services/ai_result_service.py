"""
Service layer for AI Result module.
"""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_result import AIResult
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.gemini_service import GeminiService
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)


class AIResultService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_submission(self, submission_id: UUID) -> Submission:
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await self.db.execute(stmt)
        sub = result.scalars().first()
        if not sub:
            raise HTTPException(status_code=404, detail="Submission topilmadi.")
        return sub

    async def analyze_submission(self, submission_id: UUID, current_user: User) -> AIResult:
        """
        Tahlilni boshlash jarayoni:
        1. AI Result oldin yo'qligini tekshirish.
        2. Status = PROCESSING.
        3. Gemini chaqiruvi.
        4. Muvaffaqiyatli: Status = COMPLETED, bazaga yozish.
        5. Xatolik: Status = FAILED, log qilish.
        """
        # Faqat o'qituvchilar uchun umumiy tekshiruv
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faqat o'qituvchilar AI tahlilini boshlay oladi."
            )
            
        # Egalik huquqini tekshirish
        await PermissionService.check_teacher_owns_submission(self.db, current_user.id, submission_id)

        submission = await self.get_submission(submission_id)

        # 1. Oldin tahlil qilinmaganligini tekshirish
        stmt = select(AIResult).where(AIResult.submission_id == submission_id)
        existing = (await self.db.execute(stmt)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu submission allaqachon tahlil qilingan."
            )

        # 2. Status PROCESSING
        submission.status = SubmissionStatus.PROCESSING
        await self.db.commit()

        # O'quvchi jo'natgan homework haqida ma'lumot olishimiz kerak
        await self.db.refresh(submission, ["homework"])
        homework_title = submission.homework.title
        homework_desc = submission.homework.description or ""

        # 3. Gemini chaqiruvi
        try:
            ai_data = await GeminiService.analyze_homework_submission(
                file_path=submission.file_path,
                homework_title=homework_title,
                homework_desc=homework_desc,
            )

            # 4. Muvaffaqiyatli
            ai_result = AIResult(
                submission_id=submission_id,
                score_percent=ai_data.get("score_percent", 0.0),
                confidence_score=ai_data.get("confidence_score", 0.0),
                summary=ai_data.get("summary", ""),
                strengths=ai_data.get("strengths", []),
                weaknesses=ai_data.get("weaknesses", []),
                suggestions=ai_data.get("suggestions", []),
                raw_response={"raw": ai_data.get("raw_response", "")},
            )
            self.db.add(ai_result)
            
            submission.status = SubmissionStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(ai_result)
            return ai_result

        except Exception as e:
            # 5. Xato yuz bersa FAILED
            logger.error(f"Tahlil xatosi (Submission ID: {submission_id}): {str(e)}")
            submission.status = SubmissionStatus.FAILED
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI tahlilida xatolik yuz berdi: {str(e)}"
            )

    async def get_ai_result(self, submission_id: UUID, current_user: User) -> AIResult:
        """
        Ma'lum bir submissionning AI natijasini olish.
        """
        # Egalik huquqini tekshirish
        await PermissionService.check_user_can_view_submission(self.db, current_user, submission_id)
        
        stmt = select(AIResult).where(AIResult.submission_id == submission_id)
        result = await self.db.execute(stmt)
        ai_result = result.scalars().first()

        if not ai_result:
            raise HTTPException(status_code=404, detail="AI natijasi topilmadi.")
            
        return ai_result
