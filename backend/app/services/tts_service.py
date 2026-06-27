import base64
from typing import AsyncIterator

import httpx

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TTSService:
    """Streaming text-to-speech via ElevenLabs."""

    def __init__(self, settings: Settings):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
        self.model = settings.elevenlabs_model
        self.base_url = "https://api.elevenlabs.io/v1"

    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        if not self.api_key:
            return b""
        vid = voice_id or self.voice_id
        url = f"{self.base_url}/text-to-speech/{vid}"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content

    async def synthesize_stream(self, text: str, voice_id: str | None = None) -> AsyncIterator[bytes]:
        if not self.api_key:
            yield b""
            return
        vid = voice_id or self.voice_id
        url = f"{self.base_url}/text-to-speech/{vid}/stream"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk

    def to_base64(self, audio_bytes: bytes) -> str:
        return base64.b64encode(audio_bytes).decode("utf-8")
