import logging

from schemas import CallRecord, ClientInfo, Intent, RequestedAction, Urgency, Vehicle

logger = logging.getLogger(__name__)

HIGH_RISK_TERMS = {
    "frein ne repond plus",
    "plus de freins",
    "fumee",
    "fumée",
    "odeur de brule",
    "odeur de brûlé",
    "accident",
    "danger",
    "autoroute",
    "moteur bloque",
    "moteur bloqué",
    "panne urgente",
    "roue bloquee",
    "roue bloquée",
}

MEDIUM_RISK_TERMS = {
    "voyant moteur",
    "bruit",
    "vibration",
    "ne demarre pas",
    "ne démarre pas",
    "crevaison",
    "fuite",
    "carrosserie",
    "accrochage",
}


def classify_urgency(description: str) -> dict:
    normalized = description.lower()
    risk_flags: list[str] = []

    if any(term in normalized for term in HIGH_RISK_TERMS):
        urgency = Urgency.HIGH
        risk_flags.append("situation potentiellement dangereuse")
    elif any(term in normalized for term in MEDIUM_RISK_TERMS):
        urgency = Urgency.MEDIUM
    else:
        urgency = Urgency.LOW

    if "prix exact" in normalized or "tarif exact" in normalized:
        risk_flags.append("demande de prix exact sans grille tarifaire")
    if "humain" in normalized or "responsable" in normalized or "quelqu'un" in normalized:
        risk_flags.append("demande de contact humain")

    return {
        "urgency": urgency.value,
        "risk_flags": risk_flags,
        "disclaimer": "Classification indicative uniquement, sans diagnostic mecanique definitif.",
    }


def _missing_info(caller: ClientInfo, vehicle: Vehicle, summary: str) -> list[str]:
    missing: list[str] = []
    if not caller.name:
        missing.append("nom client")
    if not caller.phone:
        missing.append("telephone")
    if not vehicle.make:
        missing.append("marque vehicule")
    if not vehicle.model:
        missing.append("modele vehicule")
    if not summary:
        missing.append("resume")
    return missing


def create_call_record(
    caller_name: str | None,
    phone: str | None,
    email: str | None,
    vehicle_make: str | None,
    vehicle_model: str | None,
    license_plate: str | None,
    intent: str,
    urgency: str,
    requested_action: str,
    summary: str,
    status: str = "open",
    risk_flags: list[str] | None = None,
) -> CallRecord:
    caller = ClientInfo(name=caller_name, phone=phone, email=email)
    vehicle = Vehicle(make=vehicle_make, model=vehicle_model, license_plate=license_plate)
    record = CallRecord(
        caller=caller,
        vehicle=vehicle,
        intent=Intent(intent) if intent in Intent._value2member_map_ else Intent.AUTRE,
        urgency=Urgency(urgency) if urgency in Urgency._value2member_map_ else Urgency.LOW,
        requested_action=RequestedAction(requested_action)
        if requested_action in RequestedAction._value2member_map_
        else RequestedAction.UNKNOWN,
        summary=summary or "Fiche creee avec informations partielles.",
        status=status,
        risk_flags=risk_flags or [],
        missing_info=_missing_info(caller, vehicle, summary),
    )
    logger.info("mock_call_record_created", extra={"record_id": record.record_id})
    return record
