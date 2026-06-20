"""
Service layer for Group module.
Business logic and permission checks are here.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User, UserRole
from app.schemas.group import GroupCreate, GroupUpdate


class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_teacher_role(self, current_user: User) -> None:
        """Faqat teacher ruxsatiga ega ekanligini tekshirish."""
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faqat o'qituvchilar (teacher) ushbu amalni bajara oladi.",
            )

    async def create_group(self, data: GroupCreate, current_user: User) -> Group:
        """Yangi guruh yaratish (faqat teacher)."""
        self._check_teacher_role(current_user)

        group = Group(
            name=data.name,
            subject=data.subject,
            teacher_id=current_user.id,
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_groups(self, current_user: User) -> list[Group]:
        """O'qituvchining barcha guruhlarini qaytarish."""
        self._check_teacher_role(current_user)

        stmt = select(Group).where(Group.teacher_id == current_user.id).order_by(Group.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_group_by_id(self, group_id: UUID, current_user: User) -> Group:
        """Guruhni ID orqali olish."""
        self._check_teacher_role(current_user)

        stmt = select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
        result = await self.db.execute(stmt)
        group = result.scalars().first()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guruh topilmadi yoki sizga tegishli emas.",
            )
        return group

    async def update_group(self, group_id: UUID, data: GroupUpdate, current_user: User) -> Group:
        """Guruh ma'lumotlarini yangilash."""
        group = await self.get_group_by_id(group_id, current_user)

        if data.name is not None:
            group.name = data.name
        if data.subject is not None:
            group.subject = data.subject

        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete_group(self, group_id: UUID, current_user: User) -> None:
        """Guruhni o'chirish."""
        group = await self.get_group_by_id(group_id, current_user)

        await self.db.delete(group)
        await self.db.commit()
