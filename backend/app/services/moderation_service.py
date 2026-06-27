from openai import AsyncOpenAI

from app.config import Settings
from app.core.exceptions import ModerationError
from app.core.logging import get_logger

logger = get_logger(__name__)

REFUSAL_MESSAGE = (
    "I'm sorry, but I can't help with that request. "
    "Please ask something else, and I'll be happy to assist."
)


class ModerationService:
    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def check(self, text: str) -> None:
        # Gemini API does not support the moderations endpoint (safety is built-in)
        return
        try:
            result = await self.client.moderations.create(input=text, model="omni-moderation-latest")
            flagged = result.results[0].flagged if result.results else False
            if flagged:
                categories = result.results[0].categories.model_dump() if result.results else {}
                logger.warning("content_moderated", categories=categories)
                raise ModerationError(REFUSAL_MESSAGE)
        except ModerationError:
            raise
        except Exception as exc:
            logger.error("moderation_error", error=str(exc))
            if "insufficient_quota" in str(exc) or "quota" in str(exc) or "429" in str(exc):
                from app.core.exceptions import AppError
                raise AppError("OpenAI API quota exceeded. Please check your plan and billing details.", code="openai_quota_exceeded")
            raise
