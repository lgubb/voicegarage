import logging

logger = logging.getLogger(__name__)


def transfer_to_human(reason: str, caller_name: str | None = None, phone: str | None = None) -> dict:
    logger.warning("mock_handoff_requested", extra={"reason": reason, "phone": phone})
    return {
        "status": "handoff_requested",
        "provider": "mock",
        "reason": reason,
        "caller_name": caller_name,
        "phone": phone,
        "next_step": "Garage should call back or connect live when SIP transfer is implemented.",
    }
