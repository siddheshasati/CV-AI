import asyncio
import base64
import re
from typing import Any, AsyncIterator

from app.core.exceptions import ModerationError
from app.core.logging import get_logger
from app.models.chat import ChatMessage, MessageRole
from app.repositories.chat_repository import ChatRepository
from app.services.avatar_service import AvatarService
from app.services.llm_service import LLMService
from app.services.moderation_service import ModerationService, REFUSAL_MESSAGE
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

logger = get_logger(__name__)


class VoicePipelineService:
    """Orchestrates the full voice AI pipeline."""

    def __init__(
        self,
        stt: STTService,
        moderation: ModerationService,
        llm: LLMService,
        tts: TTSService,
        avatar: AvatarService,
        chat_repo: ChatRepository,
    ):
        self.stt = stt
        self.moderation = moderation
        self.llm = llm
        self.tts = tts
        self.avatar = avatar
        self.chat_repo = chat_repo

    def _history_to_openai(self, messages: list[ChatMessage]) -> list[dict]:
        return [{"role": m.role.value, "content": m.content} for m in messages if m.role != MessageRole.SYSTEM]

    async def process_voice(
        self,
        audio_bytes: bytes,
        conversation_id: str | None = None,
        avatar_session_id: str | None = None,
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        transcript = await self.stt.transcribe(audio_bytes)
        if not transcript:
            return {"conversation_id": conversation_id, "error": "Could not transcribe audio."}

        return {
            "conversation_id": conversation_id,
            "transcript": transcript,
            "response": "",
            "audio_base64": None,
            "tools_used": [],
            "blocked": False,
        }

    async def process_text(
        self,
        message: str,
        conversation_id: str | None = None,
        avatar_session_id: str | None = None,
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        if not conversation_id:
            conv = await self.chat_repo.create_conversation(title=message[:50])
            conversation_id = conv.id
        else:
            conv = await self.chat_repo.get_conversation(conversation_id)
            if not conv:
                conv = await self.chat_repo.create_conversation(title=message[:50])
                conversation_id = conv.id

        try:
            await self.moderation.check(message)
        except ModerationError as exc:
            return await self._blocked_response(conversation_id, exc.message, avatar_session_id, voice_id)

        await self.chat_repo.add_message(conversation_id, ChatMessage(role=MessageRole.USER, content=message))
        history = self._history_to_openai(conv.messages)
        response_text, tools_used = await self.llm.chat(message, history)

        await self.chat_repo.add_message(
            conversation_id,
            ChatMessage(role=MessageRole.ASSISTANT, content=response_text, metadata={"tools": tools_used}),
        )

        audio_bytes_out = await self.tts.synthesize(response_text, voice_id)
        if avatar_session_id:
            await self.avatar.speak(avatar_session_id, response_text)

        return {
            "conversation_id": conversation_id,
            "response": response_text,
            "audio_base64": base64.b64encode(audio_bytes_out).decode("utf-8") if audio_bytes_out else None,
            "tools_used": tools_used,
            "blocked": False,
        }

    async def process_stream(
        self,
        message: str,
        conversation_id: str | None = None,
        avatar_session_id: str | None = None,
        voice_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Streaming pipeline for WebSocket — yields incremental events."""
        if not conversation_id:
            conv = await self.chat_repo.create_conversation(title=message[:50])
            conversation_id = conv.id
        else:
            conv = await self.chat_repo.get_conversation(conversation_id)
            if not conv:
                conv = await self.chat_repo.create_conversation(title=message[:50])
                conversation_id = conv.id

        yield {"type": "conversation_id", "conversation_id": conversation_id}

        try:
            await self.moderation.check(message)
        except ModerationError as exc:
            yield {"type": "blocked", "message": exc.message}
            audio = await self.tts.synthesize(exc.message, voice_id)
            yield {"type": "audio", "data": base64.b64encode(audio).decode("utf-8") if audio else ""}
            yield {"type": "done"}
            return

        await self.chat_repo.add_message(conversation_id, ChatMessage(role=MessageRole.USER, content=message))
        history = self._history_to_openai(conv.messages)

        full_text = ""
        tools_used: list[str] = []
        
        tts_tasks = []
        sentence_buffer = ""
        
        def flush_sentence(force=False):
            nonlocal sentence_buffer
            if not sentence_buffer.strip():
                return
            
            if force:
                text_to_tts = sentence_buffer
                sentence_buffer = ""
            else:
                match = re.search(r'([.!?;]+)(?:\s|\n|$)', sentence_buffer)
                if match:
                    split_idx = match.end()
                    text_to_tts = sentence_buffer[:split_idx]
                    sentence_buffer = sentence_buffer[split_idx:]
                else:
                    return
                    
            if text_to_tts.strip():
                task = asyncio.create_task(self.tts.synthesize(text_to_tts.strip(), voice_id))
                tts_tasks.append(task)

        async for event in self.llm.chat_stream(message, history):
            if event["type"] == "text_delta":
                content = event["content"]
                full_text += content
                sentence_buffer += content
                yield event
                
                flush_sentence()
                
                while tts_tasks and tts_tasks[0].done():
                    task = tts_tasks.pop(0)
                    try:
                        audio = task.result()
                        if audio:
                            yield {"type": "audio_sentence", "data": base64.b64encode(audio).decode("utf-8")}
                    except Exception as e:
                        logger.error("tts_streaming_error", error=str(e))
                        
            elif event["type"] in ("tool_start", "tool_end"):
                yield event
            elif event["type"] == "done":
                full_text = event.get("full_text", full_text)
                tools_used = event.get("tools_used", [])

        await self.chat_repo.add_message(
            conversation_id,
            ChatMessage(role=MessageRole.ASSISTANT, content=full_text, metadata={"tools": tools_used}),
        )

        avatar_task = None
        if avatar_session_id and full_text:
            avatar_task = asyncio.create_task(self.avatar.speak(avatar_session_id, full_text))

        flush_sentence(force=True)
        for task in tts_tasks:
            try:
                audio = await task
                if audio:
                    yield {"type": "audio_sentence", "data": base64.b64encode(audio).decode("utf-8")}
            except Exception as e:
                logger.error("tts_streaming_error", error=str(e))

        if avatar_task:
            await avatar_task

        yield {"type": "done", "tools_used": tools_used, "response": full_text}

    async def _blocked_response(
        self,
        conversation_id: str,
        message: str,
        avatar_session_id: str | None,
        voice_id: str | None,
    ) -> dict[str, Any]:
        await self.chat_repo.add_message(
            conversation_id,
            ChatMessage(role=MessageRole.ASSISTANT, content=message, metadata={"blocked": True}),
        )
        audio = await self.tts.synthesize(message, voice_id)
        if avatar_session_id:
            await self.avatar.speak(avatar_session_id, message)
        return {
            "conversation_id": conversation_id,
            "response": message,
            "audio_base64": base64.b64encode(audio).decode("utf-8") if audio else None,
            "blocked": True,
            "tools_used": [],
        }
