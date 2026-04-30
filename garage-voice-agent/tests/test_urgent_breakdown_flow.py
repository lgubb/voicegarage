from post_call.summarizer import build_call_summary
from tools.call_record_tools import classify_urgency


def test_urgent_breakdown_is_high_priority() -> None:
    result = classify_urgency("Je suis sur l'autoroute, fumee moteur et plus de freins.")
    assert result["urgency"] == "high"
    assert result["risk_flags"]


def test_urgent_breakdown_summary_requests_priority_callback() -> None:
    summary = build_call_summary("Panne urgente sur autoroute avec fumee moteur.")
    assert summary.urgency == "high"
    assert "prioritaire" in summary.next_action.lower()
