from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


class TimeTool:
    name = "get_current_time"
    description = "Get the current date and time for a timezone or location."
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone, e.g. America/New_York, Europe/London, Asia/Tokyo",
                "default": "UTC",
            },
        },
    }

    async def execute(self, timezone: str = "UTC") -> dict[str, Any]:
        tz = dt_timezone.utc
        label = "UTC"

        if ZoneInfo and timezone.upper() != "UTC":
            try:
                tz = ZoneInfo(timezone)
                label = timezone
            except Exception:
                tz = dt_timezone.utc
                label = "UTC"

        now = datetime.now(tz)
        return {
            "timezone": label,
            "datetime": now.isoformat(),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p %Z"),
        }
