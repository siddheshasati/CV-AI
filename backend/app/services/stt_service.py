import io
import base64
import httpx
from typing import AsyncIterator

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class STTService:
    """Speech-to-text using Gemini 2.5 Flash via REST API."""

    def __init__(self, settings: Settings):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model or "gemini-2.5-flash"

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        if not self.api_key:
            return "Gemini API key not configured for STT."
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        try:
            # We assume audio_bytes is webm/opus since it comes from MediaRecorder
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Transcribe this audio accurately. Output only the transcript, nothing else."},
                            {
                                "inlineData": {
                                    "mimeType": "audio/webm",
                                    "data": audio_b64
                                }
                            }
                        ]
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                try:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info("stt_complete", length=len(text))
                    return text.strip()
                except (KeyError, IndexError):
                    logger.error("stt_parse_error", response=data)
                    return ""
                    
        except Exception as exc:
            logger.error("stt_error", error=str(exc))
            if "429" in str(exc) or "quota" in str(exc).lower():
                from app.core.exceptions import AppError
                raise AppError("API quota exceeded.", code="openai_quota_exceeded")
            raise

    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> str:
        """Collect streaming audio chunks and transcribe."""
        buffer = io.BytesIO()
        async for chunk in audio_chunks:
            buffer.write(chunk)
        return await self.transcribe(buffer.getvalue())
