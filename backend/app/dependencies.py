from dataclasses import dataclass

from app.config import Settings, get_settings
from app.repositories.chat_repository import ChatRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.avatar_service import AvatarService
from app.services.cache_service import CacheService
from app.services.llm_service import LLMService
from app.services.moderation_service import ModerationService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.voice_pipeline_service import VoicePipelineService
from app.tools.registry import ToolRegistry


@dataclass
class Container:
    settings: Settings
    chat_repo: ChatRepository
    settings_repo: SettingsRepository
    cache: CacheService
    stt: STTService
    moderation: ModerationService
    tools: ToolRegistry
    llm: LLMService
    tts: TTSService
    avatar: AvatarService
    pipeline: VoicePipelineService


_container: Container | None = None


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    chat_repo = ChatRepository(settings.database_url)
    settings_repo = SettingsRepository(settings.database_url, settings)
    cache = CacheService(settings.redis_url, settings.cache_ttl_seconds)
    stt = STTService(settings)
    moderation = ModerationService(settings)
    tools = ToolRegistry(settings, cache)
    llm = LLMService(settings, tools)
    tts = TTSService(settings)
    avatar = AvatarService(settings)
    pipeline = VoicePipelineService(stt, moderation, llm, tts, avatar, chat_repo)
    return Container(
        settings=settings,
        chat_repo=chat_repo,
        settings_repo=settings_repo,
        cache=cache,
        stt=stt,
        moderation=moderation,
        tools=tools,
        llm=llm,
        tts=tts,
        avatar=avatar,
        pipeline=pipeline,
    )


def init_container(settings: Settings | None = None) -> Container:
    global _container
    _container = build_container(settings)
    return _container


def get_container() -> Container:
    global _container
    if _container is None:
        _container = build_container()
    return _container
