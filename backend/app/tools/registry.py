import json
from typing import Any, Callable, Awaitable

from app.config import Settings
from app.core.logging import get_logger
from app.services.cache_service import CacheService
from app.tools.search import NewsTool, SearchTool
from app.tools.stocks import StockTool
from app.tools.time_tool import TimeTool
from app.tools.weather import WeatherTool
from app.tools.wikipedia import WikipediaTool

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for OpenAI function calling tools."""

    def __init__(self, settings: Settings, cache: CacheService):
        self._tools: dict[str, Any] = {}
        self._handlers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {}

        weather = WeatherTool(settings, cache)
        search = SearchTool(settings, cache)
        news = NewsTool(settings, cache)
        wiki = WikipediaTool(cache)
        time_tool = TimeTool()
        stock = StockTool(settings, cache)

        for tool in [weather, search, news, wiki, time_tool, stock]:
            self.register(tool)

    def register(self, tool: Any) -> None:
        self._tools[tool.name] = tool
        self._handlers[tool.name] = tool.execute

    def get_openai_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, arguments: str | dict) -> dict[str, Any]:
        if name not in self._handlers:
            return {"error": f"Unknown tool: {name}"}
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
        try:
            result = await self._handlers[name](**args)
            logger.info("tool_executed", tool=name)
            return result
        except Exception as exc:
            logger.error("tool_error", tool=name, error=str(exc))
            return {"error": str(exc)}
