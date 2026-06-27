from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import Container, get_container

router = APIRouter(prefix="/avatar", tags=["avatar"])


class StartSessionBody(BaseModel):
    sdp: str | None = None
    type: str | None = None


class IceCandidateBody(BaseModel):
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = None
    usernameFragment: str | None = None


@router.post("/token")
async def create_avatar_token(container: Container = Depends(get_container)):
    return await container.avatar.create_session_token()


@router.post("/session")
async def create_avatar_session(
    avatar_id: str | None = None,
    container: Container = Depends(get_container),
):
    return await container.avatar.create_session(avatar_id)


@router.post("/session/{session_id}/start")
async def start_avatar_session(
    session_id: str,
    body: StartSessionBody | None = None,
    container: Container = Depends(get_container),
):
    """Start the session and optionally complete WebRTC SDP handshake."""
    sdp_offer = None
    if body and body.sdp and body.type:
        sdp_offer = {"sdp": body.sdp, "type": body.type}
    return await container.avatar.start_session(session_id, sdp_offer)


@router.post("/session/{session_id}/ice")
async def send_ice_candidate(
    session_id: str,
    body: IceCandidateBody,
    container: Container = Depends(get_container),
):
    """Forward a WebRTC ICE candidate from the browser to HeyGen."""
    candidate = {
        "candidate": body.candidate,
        "sdpMid": body.sdpMid,
        "sdpMLineIndex": body.sdpMLineIndex,
        "usernameFragment": body.usernameFragment,
    }
    return await container.avatar.send_ice_candidate(session_id, candidate)


@router.post("/session/{session_id}/interrupt")
async def interrupt_avatar(session_id: str, container: Container = Depends(get_container)):
    return await container.avatar.interrupt(session_id)


@router.delete("/session/{session_id}")
async def stop_avatar_session(session_id: str, container: Container = Depends(get_container)):
    return await container.avatar.stop_session(session_id)


@router.get("/list")
async def list_avatars(container: Container = Depends(get_container)):
    return await container.avatar.list_avatars()
