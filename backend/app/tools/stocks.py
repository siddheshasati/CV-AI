from typing import Any

import httpx

from app.config import Settings
from app.core.logging import get_logger
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class StockTool:
    name = "get_stock_price"
    description = "Get current stock price and daily change for a ticker symbol."
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL, GOOGL, TSLA"},
        },
        "required": ["symbol"],
    }

    def __init__(self, settings: Settings, cache: CacheService):
        self.api_key = settings.finnhub_api_key
        self.cache = cache

    async def execute(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        cache_key = self.cache.cache_key("stock", symbol)
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        if not self.api_key:
            return {"error": "Stock API not configured", "symbol": symbol}

        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol, "token": self.api_key}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not data.get("c"):
            return {"error": f"No data found for symbol '{symbol}'"}

        result = {
            "symbol": symbol,
            "current_price": data.get("c"),
            "change": data.get("d"),
            "percent_change": data.get("dp"),
            "high": data.get("h"),
            "low": data.get("l"),
            "previous_close": data.get("pc"),
        }
        await self.cache.set(cache_key, result, ttl=120)
        return result
