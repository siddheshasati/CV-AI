from typing import Any

import httpx

from app.config import Settings
from app.core.logging import get_logger
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class SearchTool:
    name = "web_search"
    description = "Search the internet for current information, news, facts, or recent events."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results (1-10)", "default": 5},
        },
        "required": ["query"],
    }

    def __init__(self, settings: Settings, cache: CacheService):
        self.api_key = settings.tavily_api_key
        self.cache = cache

    async def execute(self, query: str, max_results: int = 5) -> dict[str, Any]:
        cache_key = self.cache.cache_key("search", query.lower())
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        if not self.api_key:
            return {"error": "Search API not configured", "query": query}

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "include_answer": True,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        result = {
            "query": query,
            "answer": data.get("answer"),
            "results": [
                {"title": r.get("title"), "url": r.get("url"), "content": r.get("content", "")[:500]}
                for r in data.get("results", [])
            ],
        }
        await self.cache.set(cache_key, result, ttl=300)
        return result


class NewsTool:
    name = "get_news"
    description = "Get latest news headlines on a topic."
    parameters = {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "News topic, e.g. technology, sports, AI"},
            "max_results": {"type": "integer", "default": 5},
        },
        "required": ["topic"],
    }

    def __init__(self, settings: Settings, cache: CacheService):
        self.search = SearchTool(settings, cache)

    async def execute(self, topic: str, max_results: int = 5) -> dict[str, Any]:
        return await self.search.execute(f"latest news about {topic}", max_results=max_results)
