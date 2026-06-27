import io
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class STTService:
    """Speech-to-text using OpenAI Whisper (Large-v3 via API)."""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
        self.model = settings.whisper_model

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        if not self.client:
            return "Gemini API key not configured for STT."
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="text",
            )
            text = response if isinstance(response, str) else str(response)
            logger.info("stt_complete", length=len(text))
            return text.strip()
        except Exception as exc:
            logger.error("stt_error", error=str(exc))
            if "insufficient_quota" in str(exc) or "quota" in str(exc) or "429" in str(exc):
                from app.core.exceptions import AppError
                raise AppError("API quota exceeded.", code="openai_quota_exceeded")
            raise

    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> str:
        """Collect streaming audio chunks and transcribe."""
        buffer = io.BytesIO()
        async for chunk in audio_chunks:
            buffer.write(chunk)
        return await self.transcribe(buffer.getvalue())
