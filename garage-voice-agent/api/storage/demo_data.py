from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _call(
    *,
    call_id: str,
    caller_name: str | None,
    vehicle_make: str | None,
    vehicle_model: str | None,
    intent: str,
    urgency: str,
    requested_action: str,
    appointment_status: str,
    summary: str,
    next_action: str,
    transcript: list[dict],
    tool_calls: list[dict],
    appointment: dict | None = None,
    risk_flags: list[str] | None = None,
    missing_info: list[str] | None = None,
) -> dict:
    created_at = now_iso()
    return {
        "id": call_id,
        "garage_id": "demo-garage",
        "scenario": intent,
        "metadata": {"source": "demo_seed", "created_by": "seed"},
        "transcript": transcript,
        "tool_calls": tool_calls,
        "structured_summary": {
            "caller_name": caller_name,
            "phone": "06 11 22 33 44" if caller_name else None,
            "email": None,
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "license_plate": None,
            "intent": intent,
            "urgency": urgency,
            "requested_action": requested_action,
            "appointment_status": appointment_status,
            "appointment_datetime": appointment["datetime"] if appointment else None,
            "summary_for_garage": summary,
            "missing_info": missing_info or [],
            "risk_flags": risk_flags or [],
            "tool_calls": [tool["name"] for tool in tool_calls],
            "next_action": next_action,
        },
        "appointment": appointment,
        "status": requested_action,
        "timestamps": {"created_at": created_at, "updated_at": created_at},
    }


def demo_calls() -> list[dict]:
    calls = [
        _call(
            call_id="call-demo-revision",
            caller_name="Jean Dupont",
            vehicle_make="Renault",
            vehicle_model="Clio",
            intent="revision_entretien",
            urgency="low",
            requested_action="appointment",
            appointment_status="confirmed",
            summary="Jean Dupont souhaite une revision pour sa Renault Clio. Creneau mock confirme mardi matin.",
            next_action="Preparer le rendez-vous revision et verifier l'historique vehicule.",
            transcript=[
                {"role": "client", "text": "Bonjour, je voudrais une revision pour ma Clio."},
                {"role": "agent", "text": "Bien sur. Quel jour vous arrangerait ?"},
                {"role": "client", "text": "Mardi matin si possible."},
                {"role": "agent", "text": "J'ai un creneau mardi a 9h30. Je vous le reserve ?"},
            ],
            tool_calls=[
                {"name": "check_availability", "arguments": {"service_type": "revision"}, "status": "ok"},
                {"name": "create_appointment", "arguments": {"slot_id": "mock-revision-1"}, "status": "ok"},
                {"name": "create_call_record", "arguments": {"intent": "revision_entretien"}, "status": "ok"},
            ],
            appointment={
                "appointment_id": "apt-demo-revision",
                "caller_name": "Jean Dupont",
                "phone": "06 11 22 33 44",
                "vehicle": {"make": "Renault", "model": "Clio", "license_plate": None},
                "service_type": "revision",
                "datetime": "2026-05-05T09:30:00+01:00",
                "status": "confirmed",
                "notes": "Revision standard.",
            },
        ),
        _call(
            call_id="call-demo-pneus",
            caller_name="Marie Leroy",
            vehicle_make="Peugeot",
            vehicle_model="208",
            intent="pneus",
            urgency="low",
            requested_action="quote",
            appointment_status="not_requested",
            summary="Marie Leroy demande un prix pour deux pneus avant sur Peugeot 208. Aucun prix annonce, devis a preparer.",
            next_action="Rappeler avec une proposition de pneus et prix apres verification des dimensions.",
            transcript=[
                {"role": "client", "text": "Vous pouvez me donner un prix exact pour deux pneus avant ?"},
                {"role": "agent", "text": "Je ne veux pas inventer de prix. Je peux prendre les infos pour un devis."},
            ],
            tool_calls=[
                {"name": "create_call_record", "arguments": {"intent": "pneus"}, "status": "ok"},
            ],
            missing_info=["dimensions pneus"],
        ),
        _call(
            call_id="call-demo-carrosserie",
            caller_name="Sofia Bernard",
            vehicle_make="Toyota",
            vehicle_model="Yaris",
            intent="carrosserie",
            urgency="medium",
            requested_action="quote",
            appointment_status="not_requested",
            summary="Sofia Bernard a eu un accrochage sur parking. Pare-choc abime, demande devis carrosserie.",
            next_action="Demander photos et rappeler pour organiser estimation carrosserie.",
            transcript=[
                {"role": "client", "text": "J'ai eu un accrochage, le pare-choc est abime."},
                {"role": "agent", "text": "D'accord. La voiture peut-elle rouler en securite ?"},
            ],
            tool_calls=[
                {"name": "classify_urgency", "arguments": {"description": "accrochage parking"}, "status": "ok"},
                {"name": "create_call_record", "arguments": {"intent": "carrosserie"}, "status": "ok"},
            ],
            risk_flags=["accrochage a qualifier"],
        ),
        _call(
            call_id="call-demo-panne-urgente",
            caller_name=None,
            vehicle_make=None,
            vehicle_model=None,
            intent="panne",
            urgency="high",
            requested_action="transfer",
            appointment_status="not_requested",
            summary="Client en panne sur autoroute avec fumee. Situation potentiellement dangereuse, handoff humain demande.",
            next_action="Rappel humain prioritaire. Conseiller la mise en securite et organiser la prise en charge.",
            transcript=[
                {"role": "client", "text": "Je suis sur l'autoroute, il y a de la fumee."},
                {"role": "agent", "text": "Mettez-vous en securite si possible. Je demande un rappel prioritaire."},
            ],
            tool_calls=[
                {"name": "classify_urgency", "arguments": {"description": "fumee autoroute"}, "status": "ok"},
                {"name": "transfer_to_human", "arguments": {"reason": "panne urgente"}, "status": "ok"},
                {"name": "create_call_record", "arguments": {"intent": "panne"}, "status": "ok"},
            ],
            risk_flags=["situation potentiellement dangereuse"],
            missing_info=["nom client", "telephone", "marque vehicule", "modele vehicule"],
        ),
    ]
    return deepcopy(calls)


def empty_session_call(
    *,
    garage_id: str,
    scenario: str,
    voice: str,
    room_name: str,
    participant_identity: str,
) -> dict:
    call_id = f"call-{uuid4().hex[:12]}"
    created_at = now_iso()
    return {
        "id": call_id,
        "garage_id": garage_id,
        "scenario": scenario,
        "metadata": {
            "source": "livekit_session",
            "voice": voice,
            "room_name": room_name,
            "participant_identity": participant_identity,
        },
        "transcript": [
            {"role": "system", "text": f"Session LiveKit creee pour le scenario {scenario}."}
        ],
        "tool_calls": [],
        "structured_summary": None,
        "appointment": None,
        "status": "session_created",
        "timestamps": {"created_at": created_at, "updated_at": created_at},
    }
