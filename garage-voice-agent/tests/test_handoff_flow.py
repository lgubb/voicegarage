from tools.call_record_tools import classify_urgency
from tools.handoff_tools import transfer_to_human


def test_handoff_requested_when_user_asks_for_human() -> None:
    urgency = classify_urgency("Je veux parler a un humain du garage.")
    handoff = transfer_to_human("client demande un humain", "Paul", "0611111111")
    assert "demande de contact humain" in urgency["risk_flags"]
    assert handoff["status"] == "handoff_requested"
    assert handoff["provider"] == "mock"
