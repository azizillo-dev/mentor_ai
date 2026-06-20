"""
Permission and Authorization Helper Service.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.homework import Homework
from app.models.submission import Submission
from app.models.user import User, UserRole


class PermissionService:
    @staticmethod
    async def check_teacher_owns_submission(db: AsyncSession, teacher_id: int, submission_id: UUID) -> None:
        """
        Tekshiradi: Teacher haqiqatan ham ushbu submissionga egalik qiluvchi guruh o'qituvchisimi?
        Zanjir: Group.teacher_id == teacher_id -> Homework -> Submission.id == submission_id
        """
        stmt = (
            select(Submission)
            .join(Homework, Submission.homework_id == Homework.id)
            .join(Group, Homework.group_id == Group.id)
            .where(Submission.id == submission_id, Group.teacher_id == teacher_id)
        )
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sizda ushbu javobni tahlil qilish uchun ruxsat yo'q (Bu guruh sizga tegishli emas)."
            )

    @staticmethod
    async def check_user_can_view_submission(db: AsyncSession, user: User, submission_id: UUID) -> None:
        """
        Tekshiradi: Foydalanuvchi ushbu submission (va unga bog'liq AI natija) ni ko'ra oladimi?
        - Teacher: O'z guruhiga tegishli bo'lsa.
        - Student: O'zining javobi bo'lsa.
        """
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await db.execute(stmt)
        submission = result.scalars().first()

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Javob topilmadi."
            )

        if user.role == UserRole.TEACHER:
            await PermissionService.check_teacher_owns_submission(db, user.id, submission_id)
        elif user.role == UserRole.STUDENT:
            if submission.student_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Siz faqat o'zingizning javobingiz va natijangizni ko'ra olasiz."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ruxsat etilmagan rol."
            )
