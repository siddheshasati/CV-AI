from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.exceptions import AppError, to_http_exception
from app.dependencies import Container, get_container
from app.models.chat import TextChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/voice")
async def voice_chat(
    audio: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    avatar_session_id: str | None = Form(None),
    voice_id: str | None = Form(None),
    container: Container = Depends(get_container),
):
    try:
        audio_bytes = await audio.read()
        result = await container.pipeline.process_voice(
            audio_bytes, conversation_id, avatar_session_id, voice_id
        )
        return result
    except AppError as exc:
        raise to_http_exception(exc)


@router.post("/text")
async def text_chat(
    request: TextChatRequest,
    avatar_session_id: str | None = None,
    voice_id: str | None = None,
    container: Container = Depends(get_container),
):
    try:
        result = await container.pipeline.process_text(
            request.message,
            request.conversation_id,
            avatar_session_id,
            voice_id,
        )
        return result
    except AppError as exc:
        raise to_http_exception(exc)


@router.get("/conversations")
async def list_conversations(container: Container = Depends(get_container)):
    return await container.chat_repo.list_conversations()


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, container: Container = Depends(get_container)):
    conv = await container.chat_repo.get_conversation(conversation_id)
    if not conv:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, container: Container = Depends(get_container)):
    deleted = await container.chat_repo.delete_conversation(conversation_id)
    if not deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}
