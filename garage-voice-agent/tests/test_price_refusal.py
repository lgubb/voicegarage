from pathlib import Path

from tools.call_record_tools import classify_urgency

ROOT = Path(__file__).resolve().parents[1]


def test_prompt_forbids_invented_prices() -> None:
    prompt = (ROOT / "prompts" / "garage_agent_system.md").read_text(encoding="utf-8")
    assert "Ne jamais inventer de prix" in prompt


def test_prompt_collects_identity_without_spelling_in_normal_flow() -> None:
    prompt = (ROOT / "prompts" / "garage_agent_system.md").read_text(encoding="utf-8")

    assert "demande seulement le prenom et le nom de famille" in prompt
    assert "Ne demande pas d'epeler le nom de famille dans le flow normal" in prompt
    assert "seulement si le client epelle spontanement" in prompt
    assert "Evite aussi \"monsieur\" et \"madame\"" in prompt


def test_exact_price_request_sets_risk_flag() -> None:
    result = classify_urgency("Je veux un prix exact pour les freins.")
    assert "demande de prix exact sans grille tarifaire" in result["risk_flags"]
