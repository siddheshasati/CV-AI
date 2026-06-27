import json
import uuid
from datetime import datetime

import aiosqlite

from app.core.logging import get_logger
from app.models.chat import ChatMessage, Conversation, MessageRole

logger = get_logger(__name__)


class ChatRepository:
    def __init__(self, db_path: str = "./data/voice_assistant.db"):
        self.db_path = db_path.replace("sqlite+aiosqlite:///", "")

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    data TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            await db.commit()
        logger.info("database_initialized", path=self.db_path)

    async def create_conversation(self, title: str | None = None) -> Conversation:
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        title = title or "New Conversation"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, now, now),
            )
            await db.commit()
        return Conversation(
            id=conv_id,
            title=title,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            messages=[],
        )

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
            if not row:
                return None
            async with db.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,),
            ) as cursor:
                msg_rows = await cursor.fetchall()
        messages = [
            ChatMessage(
                role=MessageRole(r["role"]),
                content=r["content"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in msg_rows
        ]
        return Conversation(
            id=row["id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            messages=messages,
        )

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
        results = []
        for row in rows:
            conv = await self.get_conversation(row["id"])
            if conv:
                results.append(conv)
        return results

    async def add_message(self, conversation_id: str, message: ChatMessage) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO messages (conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    message.role.value,
                    message.content,
                    message.timestamp.isoformat(),
                    json.dumps(message.metadata),
                ),
            )
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            await db.commit()

    async def delete_conversation(self, conversation_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor = await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
            return cursor.rowcount > 0
