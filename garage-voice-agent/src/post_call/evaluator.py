from schemas import CallSummary


def evaluate_summary(summary: CallSummary) -> dict:
    score = 1.0
    issues: list[str] = []
    if summary.urgency == "high" and summary.requested_action != "transfer":
        score -= 0.25
        issues.append("High urgency should generally lead to human follow-up.")
    if not summary.phone:
        score -= 0.15
        issues.append("Missing phone number.")
    if summary.appointment_status == "confirmed" and not summary.appointment_datetime:
        score -= 0.3
        issues.append("Confirmed appointment without datetime.")
    return {"score": max(score, 0.0), "issues": issues}
