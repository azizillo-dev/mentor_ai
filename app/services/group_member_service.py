"""
Business logic for Group Membership.
"""

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User, UserRole


class GroupMemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_group_exists(self, group_id: UUID) -> Group:
        stmt = select(Group).where(Group.id == group_id)
        result = await self.db.execute(stmt)
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=404, detail="Guruh topilmadi.")
        return group

    async def _check_teacher_owns_group(self, teacher_id: int, group_id: UUID) -> Group:
        group = await self._check_group_exists(group_id)
        if group.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Siz faqat o'zingizning guruhingizga o'quvchi qo'sha olasiz."
            )
        return group

    async def add_student(self, group_id: UUID, student_id: int, current_user: User) -> GroupMember:
        """
        O'qituvchi tomonidan guruhga o'quvchi qo'shish.
        """
        await self._check_teacher_owns_group(current_user.id, group_id)

        # O'quvchi haqiqatan student ekanligini tekshirish
        stmt = select(User).where(User.id == student_id, User.role == UserRole.STUDENT)
        student = (await self.db.execute(stmt)).scalars().first()
        if not student:
            raise HTTPException(status_code=404, detail="Student topilmadi.")

        member = GroupMember(group_id=group_id, student_id=student_id)
        self.db.add(member)
        try:
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu o'quvchi allaqachon guruhga qo'shilgan."
            )

    async def get_members(self, group_id: UUID, current_user: User) -> List[GroupMember]:
        """
        Guruh a'zolarini ko'rish. 
        Teacher: o'z guruhinikini ko'ra oladi.
        Student: o'zi qatnashgan guruhnikini ko'ra oladi.
        """
        group = await self._check_group_exists(group_id)

        if current_user.role == UserRole.TEACHER:
            if group.teacher_id != current_user.id:
                raise HTTPException(status_code=403, detail="Ruxsat etilmagan.")
        else:
            # Student tekshiruvi
            stmt_check = select(GroupMember).where(
                GroupMember.group_id == group_id, 
                GroupMember.student_id == current_user.id
            )
            is_member = (await self.db.execute(stmt_check)).scalars().first()
            if not is_member:
                raise HTTPException(status_code=403, detail="Siz bu guruhga a'zo emassiz.")

        stmt = select(GroupMember).where(GroupMember.group_id == group_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def remove_student(self, group_id: UUID, student_id: int, current_user: User) -> None:
        """
        Teacher tomonidan guruhdan chetlatish.
        """
        await self._check_teacher_owns_group(current_user.id, group_id)

        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id, 
            GroupMember.student_id == student_id
        )
        member = (await self.db.execute(stmt)).scalars().first()
        if not member:
            raise HTTPException(status_code=404, detail="O'quvchi ushbu guruhdan topilmadi.")

        await self.db.delete(member)
        await self.db.commit()

    async def enroll_student(self, group_id: UUID, current_user: User) -> GroupMember:
        """
        Student o'zini o'zi guruhga qo'shishi (Enrollment).
        """
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Faqat o'quvchilar a'zo bo'la oladi.")
            
        await self._check_group_exists(group_id)

        member = GroupMember(group_id=group_id, student_id=current_user.id)
        self.db.add(member)
        try:
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Siz allaqachon bu guruhga a'zo bo'lgansiz."
            )
