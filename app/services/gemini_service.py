"""
Gemini integration service for analyzing homework submissions.
"""

import asyncio
import json
import logging

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    @staticmethod
    def _init_gemini():
        genai.configure(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def _sync_analyze(file_path: str, homework_title: str, homework_desc: str) -> dict:
        """Sinxron tahlil jarayoni (Thread ichida ishlashi uchun)"""
        GeminiService._init_gemini()

        # Faylni Gemini-ga yuklash
        gemini_file = genai.upload_file(file_path)

        prompt = f"""
Siz tajribali o'qituvchisiz. O'quvchi uy vazifasini topshirdi.
Vazifa sarlavhasi: {homework_title}
Vazifa ta'rifi: {homework_desc}

Iltimos, fayldagi o'quvchi javobini tahlil qiling.
Javobni FAQAT VA FAQAT JSON formatida qaytaring, boshqa hech qanday so'z yozmang.
Markdown blocklarni (masalan, ```json) umuman ishlatmasdan toza JSON qaytaring.

Kutilayotgan JSON formati qat'iy quyidagicha bo'lishi shart:
{{
    "score_percent": 0.0,
    "confidence_score": 0.0,
    "summary": "qisqacha xulosa matni",
    "strengths": ["Yutuq 1", "Yutuq 2"],
    "weaknesses": ["Kamchilik 1"],
    "suggestions": ["Tavsiya 1"]
}}
"""
        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
            response = model.generate_content([gemini_file, prompt])
            raw_text = response.text
        finally:
            # Faylni tahlil tugagach o'chirish
            genai.delete_file(gemini_file.name)

        parsed_json = GeminiService.parse_gemini_response(raw_text)
        # Asl xom matnni ham qo'shib qo'yamiz
        parsed_json["raw_response"] = raw_text
        return parsed_json

    @staticmethod
    async def analyze_homework_submission(file_path: str, homework_title: str, homework_desc: str) -> dict:
        """
        Gemini orqali analiz qiluvchi asosiy asinxron metod.
        Asosiy event loop ni band qilmaslik uchun to_thread da yurgizamiz.
        """
        return await asyncio.to_thread(GeminiService._sync_analyze, file_path, homework_title, homework_desc)

    @staticmethod
    def parse_gemini_response(text: str) -> dict:
        """
        Gemini javobini JSON qilib qaytaradi.
        Format xatolariga chidamli bo'lishi uchun markdown belgilarini tozalaydi.
        """
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing xatosi: {e}\nRaw Response: {text}")
            raise ValueError("Gemini noto'g'ri JSON qaytardi") from e
