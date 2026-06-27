from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.core.logging import get_logger
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class WeatherTool:
    name = "get_weather"
    description = "Get current weather for a city or location."
    parameters = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name, e.g. London or New York"},
            "units": {"type": "string", "enum": ["metric", "imperial"], "description": "Temperature units"},
        },
        "required": ["location"],
    }

    def __init__(self, settings: Settings, cache: CacheService):
        self.api_key = settings.openweather_api_key
        self.cache = cache

    async def execute(self, location: str, units: str = "metric") -> dict[str, Any]:
        cache_key = self.cache.cache_key("weather", location.lower(), units)
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        if not self.api_key:
            return {"error": "Weather API not configured", "location": location}

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": self.api_key, "units": units}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 404:
                return {"error": f"Location '{location}' not found"}
            response.raise_for_status()
            data = response.json()

        result = {
            "location": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "description": data.get("weather", [{}])[0].get("description"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "units": "°C" if units == "metric" else "°F",
        }
        await self.cache.set(cache_key, result, ttl=600)
        return result
