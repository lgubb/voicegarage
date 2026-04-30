import logging

from demo.fake_calendar import generate_mock_slots
from schemas import Appointment, AvailabilityResponse, Vehicle

logger = logging.getLogger(__name__)

_CHECKED_SLOT_IDS: set[str] = set()


def check_availability(
    requested_date: str | None,
    requested_period: str | None,
    service_type: str,
) -> AvailabilityResponse:
    slots = generate_mock_slots(requested_date, requested_period, service_type)
    _CHECKED_SLOT_IDS.update(slot.slot_id for slot in slots)
    response = AvailabilityResponse(
        service_type=service_type,
        requested_date=requested_date,
        requested_period=requested_period,
        slots=slots,
    )
    logger.info("mock_availability_checked", extra={"service_type": service_type})
    return response


def create_appointment(
    caller_name: str | None,
    phone: str | None,
    vehicle_make: str | None,
    vehicle_model: str | None,
    license_plate: str | None,
    service_type: str,
    selected_datetime: str,
    selected_slot_id: str | None = None,
    notes: str | None = None,
) -> Appointment:
    if not selected_slot_id or selected_slot_id not in _CHECKED_SLOT_IDS:
        raise ValueError("create_appointment requires a slot returned by check_availability")

    appointment = Appointment(
        caller_name=caller_name,
        phone=phone,
        vehicle=Vehicle(make=vehicle_make, model=vehicle_model, license_plate=license_plate),
        service_type=service_type,
        datetime=selected_datetime,
        notes=notes,
    )
    logger.info("mock_appointment_created", extra={"appointment_id": appointment.appointment_id})
    return appointment


def reset_checked_slots() -> None:
    _CHECKED_SLOT_IDS.clear()
