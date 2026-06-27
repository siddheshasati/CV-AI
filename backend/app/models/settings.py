from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    voice_id: str | None = None
    avatar_id: str | None = None
    theme: str = "system"
    language: str = "en"
    auto_search: bool = True
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)


class UserSettingsUpdate(BaseModel):
    voice_id: str | None = None
    avatar_id: str | None = None
    theme: str | None = None
    language: str | None = None
    auto_search: bool | None = None
    speech_rate: float | None = Field(default=None, ge=0.5, le=2.0)
