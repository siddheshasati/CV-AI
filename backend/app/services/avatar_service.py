from typing import Any

import httpx

from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AvatarService:
    """HeyGen Streaming Avatar API integration."""

    BASE_URL = "https://api.heygen.com"

    def __init__(self, settings: Settings):
        self.api_key = settings.heygen_api_key
        self.avatar_id = settings.heygen_avatar_id
        self._cached_token = None
        self._token_expires_at = 0.0

    async def _get_token(self) -> str:
        import time
        if self._cached_token and time.time() < self._token_expires_at:
            return self._cached_token
        
        token_res = await self.create_session_token()
        if token_res.get("error"):
            raise RuntimeError(token_res["error"])
        token = token_res.get("token")
        if not token:
            raise RuntimeError("Failed to create session token: empty token received")
        
        self._cached_token = token
        # Cache for 50 minutes (3000 seconds)
        self._token_expires_at = time.time() + 3000
        return token

    async def _token_headers(self) -> dict[str, str]:
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_session_token(self) -> dict[str, Any]:
        """Create a streaming avatar session token for the frontend."""
        if not self.api_key:
            return {"error": "HeyGen API key not configured", "enabled": False}

        url = f"{self.BASE_URL}/v1/streaming.create_token"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self._headers())
                response.raise_for_status()
                data = response.json()
                token = data.get("data", {}).get("token")
                logger.info("avatar_session_token_created")
                return {"token": token, "enabled": True}
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("avatar_token_http_error", status=status, url=url)
            if status == 410:
                return {"error": f"HeyGen streaming is no longer available on this API key's plan (410 Gone). Upgrade your HeyGen plan to use streaming avatars.", "enabled": False}
            if status == 401:
                return {"error": "HeyGen API key is invalid or lacks streaming permissions.", "enabled": False}
            return {"error": f"HeyGen API error: HTTP {status}", "enabled": False}
        except Exception as exc:
            logger.warning("avatar_token_error", error=str(exc))
            return {"error": f"HeyGen connection error: {str(exc)}", "enabled": False}

    async def create_session(self, avatar_id: str | None = None) -> dict[str, Any]:
        """Create a new streaming avatar session."""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}

        try:
            token_res = await self.create_session_token()
            if token_res.get("error"):
                return token_res  # propagate error

            url = f"{self.BASE_URL}/v1/streaming.new"
            payload = {
                "quality": "high",
                "avatar_id": avatar_id or self.avatar_id,
                "voice": {"voice_id": ""},
                "version": "v2",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json().get("data", {})
                logger.info("avatar_session_created", session_id=data.get("session_id"))
                return {
                    "session_id": data.get("session_id"),
                    "access_token": data.get("access_token"),
                    "url": data.get("url"),
                    "ice_servers": data.get("ice_servers2") or data.get("ice_servers"),
                }
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("avatar_session_http_error", status=status)
            return {"error": f"HeyGen session error: HTTP {status}"}
        except Exception as exc:
            logger.warning("avatar_session_error", error=str(exc))
            return {"error": f"HeyGen session error: {str(exc)}"}

    async def start_session(self, session_id: str, sdp_offer: dict | None = None) -> dict[str, Any]:
        """Start session and complete WebRTC signaling."""
        url = f"{self.BASE_URL}/v1/streaming.start"
        payload: dict[str, Any] = {"session_id": session_id}
        if sdp_offer:
            payload["sdp"] = sdp_offer

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                data = result.get("data", {})
                logger.info("avatar_session_started", session_id=session_id)
                return {
                    "sdp": data.get("sdp"),
                    "type": data.get("type"),
                    "data": data,
                }
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("avatar_start_http_error", status=status)
            return {"error": f"HeyGen start error: HTTP {status}"}
        except Exception as exc:
            logger.warning("avatar_start_error", error=str(exc))
            return {"error": f"HeyGen start error: {str(exc)}"}

    async def send_ice_candidate(self, session_id: str, candidate: dict) -> dict[str, Any]:
        """Forward a client ICE candidate to HeyGen for NAT traversal."""
        url = f"{self.BASE_URL}/v1/streaming.ice"
        payload = {
            "session_id": session_id,
            "candidate": candidate,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("avatar_ice_candidate_sent", session_id=session_id)
                return response.json()
        except Exception as exc:
            logger.warning("avatar_ice_error", error=str(exc))
            return {"error": str(exc)}

    async def speak(self, session_id: str, text: str) -> dict[str, Any]:
        """Send text for the avatar to speak with lip sync."""
        url = f"{self.BASE_URL}/v1/streaming.task"
        payload = {
            "session_id": session_id,
            "text": text,
            "task_type": "repeat",
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("avatar_speak", session_id=session_id, text_length=len(text))
                return response.json()
        except Exception as exc:
            logger.warning("avatar_speak_error", error=str(exc))
            return {"error": str(exc)}

    async def interrupt(self, session_id: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/v1/streaming.interrupt"
        payload = {"session_id": session_id}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("avatar_interrupt_error", error=str(exc))
            return {"error": str(exc)}

    async def stop_session(self, session_id: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/v1/streaming.stop"
        payload = {"session_id": session_id}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._token_headers()
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("avatar_stop_error", error=str(exc))
            return {"error": str(exc)}

    async def list_avatars(self) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/v2/avatars"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers())
            if response.status_code != 200:
                return []
            data = response.json()
            avatars = data.get("data", {}).get("avatars", [])
            return [{"avatar_id": a.get("avatar_id"), "name": a.get("avatar_name")} for a in avatars[:20]]
