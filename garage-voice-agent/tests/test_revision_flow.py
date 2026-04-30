import pytest

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
