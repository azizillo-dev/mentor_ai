"""
Pydantic schemas for Group Members.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GroupMemberCreate(BaseModel):
    """
    Teacher tomonidan o'quvchini qo'shish uchun faqat student_id kerak.
    Agar student o'zi qo'shilmoqchi bo'lsa (enroll), bu sxemaga ehtiyoj yo'q
    (URLdagi group_id va Tokendagi user id olinadi).
    """
    student_id: int


class GroupMemberResponse(BaseModel):
    id: UUID
    group_id: UUID
    student_id: int
    joined_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
