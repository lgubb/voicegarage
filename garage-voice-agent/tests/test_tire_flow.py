from tools.calendar_tools import check_availability
from tools.call_record_tools import create_call_record


def test_tire_flow_returns_three_mock_slots() -> None:
    availability = check_availability("2026-05-06", "apres-midi", "pneus")
    assert availability.source == "mock"
    assert len(availability.slots) == 3
    assert all(slot.service_type == "pneus" for slot in availability.slots)


def test_tire_flow_keeps_quote_pending_without_price() -> None:
    record = create_call_record(
        caller_name="Marie Martin",
        phone="0601020304",
        email=None,
        vehicle_make="Peugeot",
        vehicle_model="208",
        license_plate=None,
        intent="pneus",
        urgency="low",
        requested_action="quote",
        summary="Demande pneus, devis a preparer sans prix annonce.",
    )
    assert record.requested_action == "quote"
    assert "prix" in record.summary.lower()
