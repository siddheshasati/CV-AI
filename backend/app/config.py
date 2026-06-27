from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Voice AI Assistant"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,https://*.vercel.app"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    whisper_model: str = "whisper-1"

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_model: str = "eleven_turbo_v2_5"

    # HeyGen
    heygen_api_key: str = ""
    heygen_avatar_id: str = ""

    # Speech rate
    speech_rate: float = 1.0

    # External APIs
    tavily_api_key: str = ""
    openweather_api_key: str = ""
    finnhub_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/voice_assistant.db"

    # Rate limiting
    max_conversation_history: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
