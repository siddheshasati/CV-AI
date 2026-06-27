from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(container: Container = Depends(get_container)):
    return {
        "status": "healthy",
        "app": container.settings.app_name,
        "services": {
            "openai": bool(container.settings.openai_api_key),
            "elevenlabs": bool(container.settings.elevenlabs_api_key),
            "heygen": bool(container.settings.heygen_api_key),
            "tavily": bool(container.settings.tavily_api_key),
            "openweather": bool(container.settings.openweather_api_key),
        },
    }
