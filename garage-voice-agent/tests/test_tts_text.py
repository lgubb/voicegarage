import pytest

from tts_text import oralize_for_tts, oralize_tts_stream


def test_oralizes_french_phone_number() -> None:
    assert (
        oralize_for_tts("Vous etes joignable au 06 11 22 33 44.")
        == "Vous etes joignable au zero six, onze, vingt deux, trente trois, quarante quatre."
    )


def test_oralizes_plate_as_blocks() -> None:
    assert (
        oralize_for_tts("Je note la plaque AR-868-GT.")
        == "Je note la plaque A R, huit cent soixante huit, G T."
    )


def test_oralizes_time_and_common_acronyms() -> None:
    assert (
        oralize_for_tts("Le CT BMW est prevu a 09:30 avec GPS.")
        == "Le controle technique B M W est prevu a neuf heures trente avec G P S."
    )


@pytest.mark.asyncio
async def test_oralize_tts_stream_keeps_sentence_level_streaming() -> None:
    async def chunks():
        yield "La plaque est AR-"
        yield "868-GT. Le rendez-vous est a 14:00."

    assert [chunk async for chunk in oralize_tts_stream(chunks())] == [
        "La plaque est A R, huit cent soixante huit, G T. ",
        "Le rendez-vous est a quatorze heures.",
    ]
