from typing import Any
from urllib.parse import quote

import httpx

from app.core.logging import get_logger
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class WikipediaTool:
    name = "wikipedia_search"
    description = "Search Wikipedia for factual information about a topic."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic to look up on Wikipedia"},
        },
        "required": ["query"],
    }

    def __init__(self, cache: CacheService):
        self.cache = cache

    async def execute(self, query: str) -> dict[str, Any]:
        cache_key = self.cache.cache_key("wiki", query.lower())
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            search_resp = await client.get(search_url, params=params)
            search_resp.raise_for_status()
            search_data = search_resp.json()
            results = search_data.get("query", {}).get("search", [])
            if not results:
                return {"error": f"No Wikipedia article found for '{query}'"}

            title = results[0]["title"]
            summary_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": title,
                "format": "json",
            }
            summary_resp = await client.get(search_url, params=summary_params)
            summary_resp.raise_for_status()
            pages = summary_resp.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            extract = page.get("extract", "")

        result = {
            "title": title,
            "summary": extract[:1500],
            "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
        }
        await self.cache.set(cache_key, result, ttl=3600)
        return result
