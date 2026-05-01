from identity import normalize_customer_identity_payload


def test_reconstructs_spelled_last_name_from_letter_sequence() -> None:
    payload = normalize_customer_identity_payload(
        first_name="Louis",
        last_name_heard="Gubioty",
        spelling_transcript="G U B B I O T T I",
    )

    assert payload["caller_name"] == "Louis Gubbiotti"
    assert payload["last_name_spelling"] == "G U B B I O T T I"
    assert payload["needs_reask"] is False
    assert payload["spoken_acknowledgement"] == "Parfait, merci."
    assert payload["spoken_confirmation"] == "Parfait, merci."


def test_uses_last_name_hint_for_french_g_heard_as_j_ai() -> None:
    payload = normalize_customer_identity_payload(
        first_name="Louis",
        last_name_heard="Gubioty",
        spelling_transcript="j ai U B B I O double T I",
    )

    assert payload["caller_name"] == "Louis Gubbiotti"
    assert payload["last_name_spelling"] == "G U B B I O T T I"


def test_requests_reask_when_spelling_is_too_short() -> None:
    payload = normalize_customer_identity_payload(
        first_name="Louis",
        last_name_heard="Gubioty",
        spelling_transcript="B B",
    )

    assert payload["caller_name"] is None
    assert payload["needs_reask"] is True
