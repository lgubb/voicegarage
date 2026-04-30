from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Intent(StrEnum):
    REVISION_ENTRETIEN = "revision_entretien"
    PNEUS = "pneus"
    CARROSSERIE = "carrosserie"
    PANNE = "panne"
    DIAGNOSTIC = "diagnostic"
    DEVIS = "devis"
    SUIVI_VEHICULE = "suivi_vehicule"
    ANNULATION_REPORT_RDV = "annulation_report_rdv"
    URGENCE = "urgence"
    AUTRE = "autre"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestedAction(StrEnum):
    APPOINTMENT = "appointment"
    QUOTE = "quote"
    CALLBACK = "callback"
    TRANSFER = "transfer"
    INFORMATION = "information"
    UNKNOWN = "unknown"


class AppointmentStatus(StrEnum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    NOT_REQUESTED = "not_requested"


class Vehicle(BaseModel):
    make: str | None = None
    model: str | None = None
    license_plate: str | None = None

    def label(self) -> str:
        parts = [self.make, self.model, self.license_plate]
        return " ".join(part for part in parts if part) or "vehicule non precise"


class ClientInfo(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None


class TimeSlot(BaseModel):
    slot_id: str
    datetime: str
    period: str
    service_type: str


class AvailabilityResponse(BaseModel):
    service_type: str
    requested_date: str | None = None
    requested_period: str | None = None
    slots: list[TimeSlot]
    source: Literal["mock"] = "mock"


class Appointment(BaseModel):
    appointment_id: str = Field(default_factory=lambda: f"apt_{uuid4().hex[:10]}")
    caller_name: str | None = None
    phone: str | None = None
    vehicle: Vehicle
    service_type: str
    datetime: str
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    notes: str | None = None


class CallRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:10]}")
    caller: ClientInfo
    vehicle: Vehicle
    intent: Intent = Intent.AUTRE
    urgency: Urgency = Urgency.LOW
    requested_action: RequestedAction = RequestedAction.UNKNOWN
    summary: str
    status: str = "open"
    risk_flags: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CallSummary(BaseModel):
    caller_name: str | None = None
    phone: str | None = None
    email: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    license_plate: str | None = None
    intent: Intent = Intent.AUTRE
    urgency: Urgency = Urgency.LOW
    requested_action: RequestedAction = RequestedAction.UNKNOWN
    appointment_status: AppointmentStatus = AppointmentStatus.NOT_REQUESTED
    appointment_datetime: str | None = None
    summary_for_garage: str
    missing_info: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    next_action: str

    @field_validator("summary_for_garage", "next_action")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class ToolCallLog(BaseModel):
    name: str
    arguments: dict
    output: dict | str
    elapsed_ms: int | None = None
