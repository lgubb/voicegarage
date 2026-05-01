import pytest

from agent import extract_french_phone_number, normalize_french_phone
from schemas import Appointment
from tools.calendar_tools import check_availability, create_appointment, reset_checked_slots
from tools.call_record_tools import create_call_record


def test_revision_appointment_requires_checked_slot() -> None:
    reset_checked_slots()
    with pytest.raises(ValueError):
        create_appointment(
            caller_name="Jean Dupont",
            phone="0611223344",
            vehicle_make="Renault",
            vehicle_model="Clio",
            license_plate=None,
            service_type="revision",
            selected_datetime="2026-05-04T09:00:00+01:00",
            selected_slot_id="unknown",
        )


def test_revision_flow_creates_valid_appointment_and_record() -> None:
    reset_checked_slots()
    availability = check_availability("2026-05-04", "matin", "revision")
    slot = availability.slots[0]
    appointment = create_appointment(
        caller_name="Jean Dupont",
        phone="0611223344",
        vehicle_make="Renault",
        vehicle_model="Clio",
        license_plate="AB-123-CD",
        service_type="revision",
        selected_datetime=slot.datetime,
        selected_slot_id=slot.slot_id,
    )
    assert isinstance(Appointment.model_validate(appointment.model_dump()), Appointment)
    assert appointment.status == "confirmed"

    record = create_call_record(
        caller_name="Jean Dupont",
        phone="0611223344",
        email=None,
        vehicle_make="Renault",
        vehicle_model="Clio",
        license_plate="AB-123-CD",
        intent="revision_entretien",
        urgency="low",
        requested_action="appointment",
        summary="Revision demandee et creneau choisi.",
    )
    assert record.missing_info == []


def test_mock_availability_uses_paris_dst_offset() -> None:
    reset_checked_slots()
    availability = check_availability("2026-05-04", "matin", "revision")

    assert availability.slots[0].datetime.endswith("+02:00")


def test_spoken_french_phone_is_normalized() -> None:
    transcript = "Zéro six quarante deux quatre vingt douze cinquante huit trente et un."

    assert extract_french_phone_number(transcript) == "0642925831"
    assert normalize_french_phone("06 42 92 58 31") == "0642925831"
    assert normalize_french_phone("+33 6 42 92 58 31") == "0642925831"
