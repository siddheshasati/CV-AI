import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.config import Settings
from app.core.logging import get_logger
from app.tools.registry import ToolRegistry

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful, concise voice AI assistant similar to ChatGPT Voice Mode.
Keep responses natural and brief (2-4 sentences unless more detail is requested).
Speak conversationally — your responses will be read aloud.
Use tools automatically when the user asks about weather, news, stocks, Wikipedia facts, current time, or needs up-to-date information.
If you don't know something current, search the web.
Never provide harmful, illegal, or inappropriate content.
If a request is blocked, respond politely and suggest an alternative."""


class LLMService:
    def __init__(self, settings: Settings, tool_registry: ToolRegistry):
        self.client = AsyncOpenAI(
            api_key=settings.gemini_api_key, 
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        ) if settings.gemini_api_key else None
        self.model = settings.gemini_model
        self.tools = tool_registry
        self.max_history = settings.max_conversation_history

    def _build_messages(self, history: list[dict], user_message: str) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-self.max_history :])
        messages.append({"role": "user", "content": user_message})
        return messages

    async def chat(
        self,
        user_message: str,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str]]:
        """Non-streaming chat with automatic tool calling."""
        if not self.client:
            return "Gemini API key not configured.", []

        history = history or []
        messages = self._build_messages(history, user_message)
        tools_used: list[str] = []

        try:
            for _ in range(5):
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools.get_openai_tools(),
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=500,
                )
                choice = response.choices[0]
                message = choice.message

                if message.tool_calls:
                    messages.append(message.model_dump())
                    for tool_call in message.tool_calls:
                        tools_used.append(tool_call.function.name)
                        result = await self.tools.execute(
                            tool_call.function.name,
                            tool_call.function.arguments,
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result),
                            }
                        )
                    continue

                return message.content or "", tools_used
        except Exception as exc:
            err_str = str(exc)
            logger.error("llm_chat_error", error=err_str)
            if "insufficient_quota" in err_str or "quota" in err_str or "429" in err_str:
                from app.core.exceptions import AppError
                raise AppError(
                    "OpenAI API quota exceeded. Your account may be on a free tier with no credits. "
                    "Please add billing at platform.openai.com or use a different API key.",
                    code="openai_quota_exceeded",
                )
            if "model_not_found" in err_str or "does not exist" in err_str or "invalid_api_key" in err_str:
                from app.core.exceptions import AppError
                raise AppError(
                    "OpenAI API error: " + err_str,
                    code="openai_api_error",
                )
            raise

        return "I couldn't complete that request. Please try again.", tools_used

    async def chat_stream(
        self,
        user_message: str,
        history: list[dict] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Streaming chat — yields token deltas and final metadata."""
        if not self.client:
            yield {"type": "text", "content": "Gemini API key not configured."}
            yield {"type": "done", "tools_used": []}
            return

        history = history or []
        messages = self._build_messages(history, user_message)
        tools_used: list[str] = []

        try:
            for _ in range(5):
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools.get_openai_tools(),
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=500,
                    stream=True,
                )

                tool_calls_buffer: dict[int, dict] = {}
                content_buffer = ""

                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    if delta.content:
                        content_buffer += delta.content
                        yield {"type": "text_delta", "content": delta.content}

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls_buffer[idx]["id"] = tc.id
                            if tc.function and tc.function.name:
                                tool_calls_buffer[idx]["name"] = tc.function.name
                            if tc.function and tc.function.arguments:
                                tool_calls_buffer[idx]["arguments"] += tc.function.arguments

                if tool_calls_buffer:
                    assistant_msg: dict[str, Any] = {"role": "assistant", "content": content_buffer or None, "tool_calls": []}
                    for idx in sorted(tool_calls_buffer.keys()):
                        tc = tool_calls_buffer[idx]
                        assistant_msg["tool_calls"].append(
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": tc["arguments"]},
                            }
                        )
                    messages.append(assistant_msg)

                    for idx in sorted(tool_calls_buffer.keys()):
                        tc = tool_calls_buffer[idx]
                        tools_used.append(tc["name"])
                        yield {"type": "tool_start", "tool": tc["name"]}
                        result = await self.tools.execute(tc["name"], tc["arguments"])
                        yield {"type": "tool_end", "tool": tc["name"]}
                        messages.append(
                            {"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result)}
                        )
                    continue

                yield {"type": "done", "tools_used": tools_used, "full_text": content_buffer}
                return

            yield {"type": "done", "tools_used": tools_used, "full_text": "I couldn't complete that request."}
        except Exception as exc:
            err_str = str(exc)
            logger.error("llm_chat_stream_error", error=err_str)
            if "insufficient_quota" in err_str or "quota" in err_str or "429" in err_str:
                from app.core.exceptions import AppError
                raise AppError(
                    "OpenAI API quota exceeded. Your account may be on a free tier with no credits. "
                    "Please add billing at platform.openai.com or use a different API key.",
                    code="openai_quota_exceeded",
                )
            if "model_not_found" in err_str or "does not exist" in err_str or "invalid_api_key" in err_str:
                from app.core.exceptions import AppError
                raise AppError(
                    "OpenAI API error: " + err_str,
                    code="openai_api_error",
                )
            raise
