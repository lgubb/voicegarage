from post_call.summarizer import build_call_summary
from tools.call_record_tools import classify_urgency


def test_bodywork_accident_is_not_definitive_diagnosis() -> None:
    urgency = classify_urgency("Accrochage sur parking, pare-choc abime, demande carrosserie.")
    assert urgency["urgency"] == "medium"
    assert "sans diagnostic mecanique definitif" in urgency["disclaimer"]


def test_bodywork_summary_detects_intent() -> None:
    summary = build_call_summary(
        "J'ai eu un accrochage et je voudrais un devis carrosserie.",
        context={"caller_name": "Sofia", "phone": "0600000000"},
    )
    assert summary.intent == "carrosserie"
    assert summary.requested_action == "quote"
