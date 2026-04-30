from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from api.config import ApiSettings, get_api_settings
from api.livekit_tokens import generate_participant_token, make_participant_identity, make_room_name
from api.schemas import SessionCreateRequest, SessionCreateResponse

router = APIRouter(tags=["sessions"])
API_SETTINGS_DEP = Depends(get_api_settings)


@router.post("/sessions", response_model=SessionCreateResponse)
def create_session(
    payload: SessionCreateRequest,
    settings: ApiSettings = API_SETTINGS_DEP,
) -> SessionCreateResponse:
    if not settings.livekit_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LIVEKIT_URL is required to create a session.",
        )

    room_name = make_room_name(payload.scenario)
    participant_identity = make_participant_identity()
    token = generate_participant_token(
        settings,
        room_name,
        participant_identity,
        scenario=payload.scenario,
        voice=payload.voice,
    )
    return SessionCreateResponse(
        room_name=room_name,
        participant_identity=participant_identity,
        livekit_url=settings.livekit_url,
        token=token,
        call_id=f"call-{uuid4().hex[:12]}",
    )
