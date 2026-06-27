from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container
from app.models.settings import UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(container: Container = Depends(get_container)):
    return await container.settings_repo.get_settings()


@router.patch("")
async def update_settings(
    updates: UserSettingsUpdate,
    container: Container = Depends(get_container),
):
    return await container.settings_repo.update_settings(updates.model_dump(exclude_none=True))
