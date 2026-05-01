import json

from agent import LiveCallSheetState
from config import Settings


class FakeParticipant:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    async def publish_data(self, data: str, reliable: bool, topic: str) -> None:
        self.payloads.append(
            {
                "data": json.loads(data),
                "reliable": reliable,
                "topic": topic,
            }
        )


class FakeRoom:
    def __init__(self) -> None:
        self.local_participant = FakeParticipant()


def test_availability_proposal_does_not_trigger_recap() -> None:
    state = LiveCallSheetState(FakeRoom(), Settings())

    assert not state.looks_like_recap(
        "Voici trois créneaux disponibles pour une révision : lundi neuf heures trente."
    )


def test_confirmed_appointment_still_triggers_recap() -> None:
    state = LiveCallSheetState(FakeRoom(), Settings())

    assert state.looks_like_recap(
        "Nous avons rendez-vous lundi quatre mai à neuf heures trente."
    )


def test_identity_payload_overrides_hallucinated_caller_name() -> None:
    state = LiveCallSheetState(FakeRoom(), Settings())
    state.set_identity(
        {
            "caller_name": "Louis Gubbiotti",
            "needs_reask": False,
        }
    )

    record = state.build_record_payload(
        {
            "caller_name": "Louis Bbitti",
            "phone": "06 00 00 00 00",
            "summary": "Demande de rendez-vous.",
        },
        "test",
    )

    assert record["caller"]["name"] == "Louis Gubbiotti"


async def test_disconnect_refreshes_record_created_from_assistant_recap() -> None:
    room = FakeRoom()
    state = LiveCallSheetState(room, Settings())
    state.record_payload = {
        "source": "assistant_recap",
        "summary": "Fiche précoce",
    }
    state.add_user_transcript(
        "Zéro six quarante deux quatre vingt douze cinquante huit trente et un."
    )
    state.add_user_transcript("Le véhicule est une Volkswagen Polo immatriculée AR 868 GT.")
    state.add_assistant_message("Nous avons rendez-vous lundi quatre mai à neuf heures trente.")

    await state.ensure_sheet("disconnect")

    assert state.record_payload is not None
    assert state.record_payload["source"] == "disconnect"
    assert state.record_payload["summary"] != "Fiche précoce"
    assert state.record_payload["caller"]["phone"] == "0642925831"


async def test_disconnect_keeps_tool_created_record() -> None:
    room = FakeRoom()
    state = LiveCallSheetState(room, Settings())
    state.record_payload = {
        "summary": "Fiche créée par tool",
        "caller": {"phone": "0600000000"},
    }

    await state.ensure_sheet("disconnect")

    assert state.record_payload["summary"] == "Fiche créée par tool"
    assert room.local_participant.payloads[-1]["data"]["record"]["summary"] == "Fiche créée par tool"
