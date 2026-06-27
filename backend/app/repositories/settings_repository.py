import json

import aiosqlite

from app.config import Settings
from app.models.settings import UserSettings


class SettingsRepository:
    def __init__(self, db_path: str, settings: Settings):
        self.db_path = db_path.replace("sqlite+aiosqlite:///", "")
        self.settings = settings

    async def get_settings(self) -> UserSettings:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM settings WHERE id = 1") as cursor:
                row = await cursor.fetchone()
        if not row:
            db_settings = UserSettings()
        else:
            db_settings = UserSettings(**json.loads(row[0]))
        
        # Override with values from environment variables/config
        db_settings.voice_id = self.settings.elevenlabs_voice_id
        db_settings.avatar_id = self.settings.heygen_avatar_id
        db_settings.speech_rate = self.settings.speech_rate
        return db_settings

    async def update_settings(self, updates: dict) -> UserSettings:
        # Ignore changes to values managed by .env
        updates.pop("voice_id", None)
        updates.pop("avatar_id", None)
        updates.pop("speech_rate", None)

        current = await self.get_settings()
        data = current.model_dump()
        data.update({k: v for k, v in updates.items() if v is not None})
        settings = UserSettings(**data)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO settings (id, data) VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET data = excluded.data
                """,
                (json.dumps(settings.model_dump()),),
            )
            await db.commit()
        return settings
