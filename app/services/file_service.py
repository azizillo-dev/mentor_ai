"""
Service layer for file uploads.
"""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Uploads directory
UPLOAD_DIR = Path("uploads")


class FileService:
    @staticmethod
    def _ensure_upload_dir():
        if not UPLOAD_DIR.exists():
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> tuple[str, str]:
        """
        Validates the uploaded file and saves it locally.
        Returns a tuple of (file_path, file_extension).
        """
        if not upload_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fayl nomi kiritilmagan.",
            )

        _, ext = os.path.splitext(upload_file.filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fayl formati noto'g'ri. Faqat quyidagilar ruxsat etilgan: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        FileService._ensure_upload_dir()

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file to disk
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Faylni saqlashda xatolik yuz berdi: {str(e)}",
            )
        finally:
            upload_file.file.close()

        return str(file_path), ext
