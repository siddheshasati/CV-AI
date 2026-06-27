from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(BaseModel):
    title: str | None = None


class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage] = Field(default_factory=list)


class VoiceRequest(BaseModel):
    conversation_id: str | None = None
    session_id: str | None = None


class TextChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class AssistantResponse(BaseModel):
    conversation_id: str
    text: str
    audio_url: str | None = None
    blocked: bool = False
    tools_used: list[str] = Field(default_factory=list)
