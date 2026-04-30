import json
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from livekit import api as livekit_api

from api.config import ApiSettings


def make_room_name(scenario: str) -> str:
    safe_scenario = scenario.replace("_", "-").lower()
    return f"garage-demo-{safe_scenario}-{uuid4().hex[:8]}"


def make_participant_identity() -> str:
    return f"demo-user-{uuid4().hex[:8]}"


def generate_participant_token(
    settings: ApiSettings,
    room_name: str,
    participant_identity: str,
    participant_name: str = "Demo utilisateur",
    scenario: str | None = None,
    voice: str | None = None,
) -> str:
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LIVEKIT_API_KEY and LIVEKIT_API_SECRET are required to generate a token.",
        )

    agent_metadata = json.dumps(
        {
            "scenario": scenario,
            "voice": voice,
            "source": "garage-demo-api",
        }
    )

    token = (
        livekit_api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(participant_identity)
        .with_name(participant_name)
        .with_ttl(timedelta(minutes=30))
        .with_room_config(
            livekit_api.RoomConfiguration(
                agents=[
                    livekit_api.RoomAgentDispatch(
                        agent_name=settings.agent_name,
                        metadata=agent_metadata,
                    )
                ]
            )
        )
        .with_grants(
            livekit_api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )
    return token.to_jwt()
