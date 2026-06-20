"""
Service layer for Submission module.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.homework import Homework
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole


class SubmissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_student_role(self, current_user: User) -> None:
        """Faqat student ruxsatiga ega ekanligini tekshirish."""
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faqat o'quvchilar (student) ushbu amalni bajara oladi.",
            )

    async def _get_homework(self, homework_id: UUID) -> Homework:
        """Homework mavjudligini tekshirish."""
        stmt = select(Homework).where(Homework.id == homework_id)
        result = await self.db.execute(stmt)
        homework = result.scalars().first()

        if not homework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uy vazifasi topilmadi.",
            )
        return homework

    async def create_submission(
        self,
        homework_id: UUID,
        file_path: str,
        file_type: str,
        current_user: User,
    ) -> Submission:
        """Yangi submission yaratish."""
        self._check_student_role(current_user)

        # 1. Homework mavjudligini tekshirish
        homework = await self._get_homework(homework_id)

        # TODO: Kelajakda Group Membership tizimi orqali 
        # student ushbu guruh a'zosi ekanligi va homework aynan unga 
        # tegishli ekanligini tekshiradigan qism shu yerda yozilishi kerak.
        # Masalan: self._check_student_membership(homework.group_id, current_user.id)

        # 2. Student allaqachon bu homeworkka javob yuborganligini tekshirish
        stmt_check = select(Submission).where(
            Submission.homework_id == homework_id,
            Submission.student_id == current_user.id,
        )
        existing_result = await self.db.execute(stmt_check)
        existing_sub = existing_result.scalars().first()

        if existing_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Siz ushbu uy vazifasi uchun allaqachon javob yuborgansiz.",
            )

        # 3. Submission obyektini bazaga yozish (Status = PENDING)
        submission = Submission(
            homework_id=homework_id,
            student_id=current_user.id,
            file_path=file_path,
            file_type=file_type,
            status=SubmissionStatus.PENDING,
        )

        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def get_submissions(self, current_user: User) -> list[Submission]:
        """
        Submissions ro'yxatini qaytarish:
        - Teacher faqat o'z guruhlari bo'yicha submissionlarni ko'ra oladi.
        - Student faqat o'ziga tegishli submissionlarni ko'ra oladi.
        """
        if current_user.role == UserRole.TEACHER:
            stmt = (
                select(Submission)
                .join(Homework, Submission.homework_id == Homework.id)
                .join(Group, Homework.group_id == Group.id)
                .where(Group.teacher_id == current_user.id)
                .order_by(Submission.submitted_at.desc())
            )
        elif current_user.role == UserRole.STUDENT:
            stmt = (
                select(Submission)
                .where(Submission.student_id == current_user.id)
                .order_by(Submission.submitted_at.desc())
            )
        else:
            return []

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_submission_by_id(self, submission_id: UUID, current_user: User) -> Submission:
        """Bitta submissionni olish va huquqlarni tekshirish."""
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await self.db.execute(stmt)
        submission = result.scalars().first()

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Javob topilmadi.",
            )

        # Huquqlarni tekshirish
        if current_user.role == UserRole.STUDENT:
            if submission.student_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Siz faqat o'zingizning javobingizni ko'ra olasiz.",
                )
        elif current_user.role == UserRole.TEACHER:
            # Teacher faqat o'zining homeworkiga tegishli ekanini tekshiramiz
            hw_stmt = select(Homework).join(Group).where(
                Homework.id == submission.homework_id,
                Group.teacher_id == current_user.id
            )
            hw_result = await self.db.execute(hw_stmt)
            hw = hw_result.scalars().first()
            if not hw:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu javob sizning guruhingizga tegishli emas.",
                )

        return submission
