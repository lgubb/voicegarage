import json
from pathlib import Path

from post_call.summarizer import build_call_summary
from schemas import CallSummary
from tools.call_record_tools import create_call_record

ROOT = Path(__file__).resolve().parents[1]


def test_call_summary_matches_pydantic_schema() -> None:
    summary = build_call_summary(
        "Bonjour, je veux un rendez-vous pour une revision. Mon telephone est 0611223344.",
        tool_calls=[{"name": "check_availability"}, {"name": "create_call_record"}],
        context={"caller_name": "Nora", "vehicle_make": "Toyota", "vehicle_model": "Yaris"},
    )
    validated = CallSummary.model_validate(summary.model_dump())
    assert validated.phone == "0611223344"
    assert validated.summary_for_garage


def test_json_schema_file_is_present_and_consistent() -> None:
    schema = json.loads((ROOT / "schemas" / "call_summary.schema.json").read_text())
    assert schema["properties"]["urgency"]["enum"] == ["low", "medium", "high"]
    assert "summary_for_garage" in schema["required"]


def test_call_record_created_with_missing_info() -> None:
    record = create_call_record(
        caller_name=None,
        phone=None,
        email=None,
        vehicle_make=None,
        vehicle_model=None,
        license_plate=None,
        intent="panne",
        urgency="medium",
        requested_action="callback",
        summary="Bruit inquietant, client presse.",
    )
    assert "nom client" in record.missing_info
    assert "telephone" in record.missing_info
