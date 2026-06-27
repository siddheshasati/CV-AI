import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.dependencies import Container, get_container

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket, container: Container = Depends(get_container)):
    await websocket.accept()
    logger.info("websocket_connected")

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "text":
                message = data.get("message", "").strip()
                if not message:
                    await websocket.send_json({"type": "error", "message": "Empty message"})
                    continue

                async for event in container.pipeline.process_stream(
                    message,
                    data.get("conversation_id"),
                    data.get("avatar_session_id"),
                    data.get("voice_id"),
                ):
                    await websocket.send_json(event)

            elif msg_type == "interrupt":
                session_id = data.get("avatar_session_id")
                if session_id:
                    await container.avatar.interrupt(session_id)
                await websocket.send_json({"type": "interrupted"})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("websocket_disconnected")
    except Exception as exc:
        logger.error("websocket_error", error=str(exc))
        # Do not send fatal error to UI here because it might overwrite a successful text response
        pass
