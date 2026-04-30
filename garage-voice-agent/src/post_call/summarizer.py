from __future__ import annotations

import re

from schemas import AppointmentStatus, CallSummary, Intent, RequestedAction, ToolCallLog, Urgency
from tools.call_record_tools import classify_urgency


def _detect_intent(text: str) -> Intent:
    lower = text.lower()
    if any(word in lower for word in ["revision", "révision", "vidange", "entretien"]):
        return Intent.REVISION_ENTRETIEN
    if any(word in lower for word in ["pneu", "pneus", "crevaison"]):
        return Intent.PNEUS
    if any(word in lower for word in ["carrosserie", "accrochage", "pare-choc", "peinture"]):
        return Intent.CARROSSERIE
    if any(word in lower for word in ["panne", "demarre", "démarre", "moteur", "voyant"]):
        return Intent.PANNE
    if "devis" in lower or "prix" in lower or "tarif" in lower:
        return Intent.DEVIS
    if "annuler" in lower or "deplacer" in lower or "déplacer" in lower:
        return Intent.ANNULATION_REPORT_RDV
    return Intent.AUTRE


def _detect_requested_action(text: str, urgency: Urgency) -> RequestedAction:
    lower = text.lower()
    if urgency == Urgency.HIGH or any(word in lower for word in ["humain", "rappeler", "urgence"]):
        return RequestedAction.TRANSFER if "humain" in lower else RequestedAction.CALLBACK
    if any(word in lower for word in ["rendez-vous", "rdv", "creneau", "créneau"]):
        return RequestedAction.APPOINTMENT
    if any(word in lower for word in ["devis", "prix", "tarif"]):
        return RequestedAction.QUOTE
    return RequestedAction.UNKNOWN


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(?:(?:\+33|0)\s?[1-9](?:[\s.-]?\d{2}){4})", text)
    return match.group(0) if match else None


def _tool_names(tool_calls: list[ToolCallLog | dict]) -> list[str]:
    names: list[str] = []
    for call in tool_calls:
        if isinstance(call, ToolCallLog):
            names.append(call.name)
        elif isinstance(call, dict) and call.get("name"):
            names.append(str(call["name"]))
    return names


def build_call_summary(
    transcript: str,
    tool_calls: list[ToolCallLog | dict] | None = None,
    context: dict | None = None,
) -> CallSummary:
    context = context or {}
    tool_calls = tool_calls or []
    urgency_payload = classify_urgency(transcript)
    urgency = Urgency(urgency_payload["urgency"])
    intent = _detect_intent(transcript)
    requested_action = _detect_requested_action(transcript, urgency)
    names = _tool_names(tool_calls)

    appointment_datetime = context.get("appointment_datetime")
    appointment_status = AppointmentStatus.NOT_REQUESTED
    if "create_appointment" in names:
        appointment_status = AppointmentStatus.CONFIRMED
    elif requested_action == RequestedAction.APPOINTMENT:
        appointment_status = AppointmentStatus.PENDING

    phone = context.get("phone") or _extract_phone(transcript)
    caller_name = context.get("caller_name")
    vehicle_make = context.get("vehicle_make")
    vehicle_model = context.get("vehicle_model")
    license_plate = context.get("license_plate")

    missing_info = [
        label
        for label, value in {
            "nom client": caller_name,
            "telephone": phone,
            "marque vehicule": vehicle_make,
            "modele vehicule": vehicle_model,
        }.items()
        if not value
    ]

    return CallSummary(
        caller_name=caller_name,
        phone=phone,
        email=context.get("email"),
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        license_plate=license_plate,
        intent=intent,
        urgency=urgency,
        requested_action=requested_action,
        appointment_status=appointment_status,
        appointment_datetime=appointment_datetime,
        summary_for_garage=(
            context.get("summary_for_garage")
            or f"Appel client detecte: {intent.value}. Demande a traiter avec priorite {urgency.value}."
        ),
        missing_info=missing_info,
        risk_flags=urgency_payload["risk_flags"],
        tool_calls=names,
        next_action=context.get("next_action") or _default_next_action(requested_action, urgency),
    )


def _default_next_action(requested_action: RequestedAction, urgency: Urgency) -> str:
    if urgency == Urgency.HIGH:
        return "Rappel humain prioritaire avant toute promesse de diagnostic."
    if requested_action == RequestedAction.APPOINTMENT:
        return "Valider ou confirmer le rendez-vous avec le client."
    if requested_action == RequestedAction.QUOTE:
        return "Preparer un devis ou rappeler le client pour cadrer la demande."
    return "Relire la fiche appel et rappeler si necessaire."
