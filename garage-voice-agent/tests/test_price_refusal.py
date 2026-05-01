from pathlib import Path

from tools.call_record_tools import classify_urgency

ROOT = Path(__file__).resolve().parents[1]


def test_prompt_forbids_invented_prices() -> None:
    prompt = (ROOT / "prompts" / "garage_agent_system.md").read_text(encoding="utf-8")
    assert "Ne jamais inventer de prix" in prompt


def test_prompt_collects_identity_in_two_short_turns_without_reconfirming_name() -> None:
    prompt = (ROOT / "prompts" / "garage_agent_system.md").read_text(encoding="utf-8")

    assert "fais-le en deux tours courts" in prompt
    assert "Et votre nom de famille, lettre par lettre ?" in prompt
    assert "ne reconfirme pas le nom" in prompt
    assert "Evite aussi \"monsieur\" et \"madame\"" in prompt


def test_exact_price_request_sets_risk_flag() -> None:
    result = classify_urgency("Je veux un prix exact pour les freins.")
    assert "demande de prix exact sans grille tarifaire" in result["risk_flags"]
