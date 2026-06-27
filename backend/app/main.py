from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import avatar, chat, health
from app.api.routes import settings as settings_routes
from app.api.websocket import router as ws_router
from app.config import get_settings
from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger, setup_logging
from app.dependencies import init_container, get_container

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.debug)
    Path("./data").mkdir(parents=True, exist_ok=True)

    container = init_container(settings)
    app.state.container = container

    await container.chat_repo.initialize()
    await container.cache.connect()
    logger.info("application_started", app=settings.app_name)

    yield

    await container.cache.disconnect()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    app.include_router(health.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(settings_routes.router, prefix=prefix)
    app.include_router(avatar.router, prefix=prefix)
    app.include_router(ws_router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=to_http_exception(exc).status_code, content=to_http_exception(exc).detail)

    return app


app = create_app()
