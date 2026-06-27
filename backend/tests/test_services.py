import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools.registry import ToolRegistry
from app.services.cache_service import CacheService
from app.config import Settings
from app.tools.time_tool import TimeTool


@pytest.fixture
def settings():
    return Settings(
        gemini_api_key="test-key",
        tavily_api_key="test-tavily",
        openweather_api_key="test-weather",
        finnhub_api_key="test-finnhub",
    )


@pytest.fixture
def cache():
    c = CacheService("redis://localhost:6379/0", ttl=60)
    c.get = AsyncMock(return_value=None)
    c.set = AsyncMock()
    return c


@pytest.fixture
def tool_registry(settings, cache):
    return ToolRegistry(settings, cache)


@pytest.mark.asyncio
async def test_time_tool():
    tool = TimeTool()
    result = await tool.execute(timezone="UTC")
    assert result["timezone"] == "UTC"
    assert "formatted" in result
    assert "datetime" in result


@pytest.mark.asyncio
async def test_tool_registry_has_all_tools(tool_registry):
    tools = tool_registry.get_openai_tools()
    names = {t["function"]["name"] for t in tools}
    expected = {"get_weather", "web_search", "get_news", "wikipedia_search", "get_current_time", "get_stock_price"}
    assert expected == names


@pytest.mark.asyncio
async def test_wikipedia_tool_cache_hit(cache):
    from app.tools.wikipedia import WikipediaTool

    cache.get = AsyncMock(return_value={"title": "Python", "summary": "A language"})
    tool = WikipediaTool(cache)
    result = await tool.execute("Python")
    assert result["title"] == "Python"
    cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_moderation_skips():
    from app.services.moderation_service import ModerationService

    service = ModerationService(Settings())
    await service.check("offensive content")  # Should not raise


@pytest.mark.asyncio
async def test_health_endpoint():
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.dependencies import init_container
    from unittest.mock import AsyncMock

    container = init_container(Settings())
    container.chat_repo.initialize = AsyncMock()
    container.cache.connect = AsyncMock()
    container.cache.disconnect = AsyncMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
