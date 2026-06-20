"""
Service layer for Homework module.
Business logic and permission checks are here.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group
from app.models.homework import Homework
from app.models.user import User, UserRole
from app.schemas.homework import HomeworkCreate, HomeworkUpdate


class HomeworkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_teacher_role(self, current_user: User) -> None:
        """Faqat teacher ruxsatiga ega ekanligini tekshirish."""
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faqat o'qituvchilar (teacher) ushbu amalni bajara oladi.",
            )

    async def _get_and_check_group(self, group_id: UUID, current_user: User) -> Group:
        """Guruh mavjudligi va aynan shu o'qituvchiga tegishliligini tekshirish."""
        stmt = select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
        result = await self.db.execute(stmt)
        group = result.scalars().first()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas.",
            )
        return group

    async def create_homework(self, data: HomeworkCreate, current_user: User) -> Homework:
        """Yangi homework yaratish (faqat teacher va o'zining guruhi uchun)."""
        self._check_teacher_role(current_user)
        await self._get_and_check_group(data.group_id, current_user)

        homework = Homework(
            group_id=data.group_id,
            title=data.title,
            description=data.description,
            deadline=data.deadline,
        )
        self.db.add(homework)
        await self.db.commit()
        await self.db.refresh(homework)
        return homework

    async def get_homeworks(self, current_user: User) -> list[Homework]:
        """O'qituvchining o'z guruhlariga tegishli barcha homeworklarni qaytarish."""
        self._check_teacher_role(current_user)

        stmt = (
            select(Homework)
            .join(Group, Homework.group_id == Group.id)
            .where(Group.teacher_id == current_user.id)
            .order_by(Homework.deadline.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_homework_by_id(self, homework_id: UUID, current_user: User) -> Homework:
        """Homeworkni ID orqali olish."""
        self._check_teacher_role(current_user)

        stmt = (
            select(Homework)
            .join(Group, Homework.group_id == Group.id)
            .where(Homework.id == homework_id, Group.teacher_id == current_user.id)
        )
        result = await self.db.execute(stmt)
        homework = result.scalars().first()

        if not homework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uy vazifasi topilmadi yoki sizga tegishli emas.",
            )
        return homework

    async def update_homework(self, homework_id: UUID, data: HomeworkUpdate, current_user: User) -> Homework:
        """Homework ma'lumotlarini yangilash."""
        homework = await self.get_homework_by_id(homework_id, current_user)

        if data.title is not None:
            homework.title = data.title
        if data.description is not None:
            homework.description = data.description
        if data.deadline is not None:
            homework.deadline = data.deadline

        await self.db.commit()
        await self.db.refresh(homework)
        return homework

    async def delete_homework(self, homework_id: UUID, current_user: User) -> None:
        """Homeworkni o'chirish."""
        homework = await self.get_homework_by_id(homework_id, current_user)

        await self.db.delete(homework)
        await self.db.commit()
