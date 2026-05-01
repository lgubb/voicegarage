from agent import build_turn_handling, selected_voice_id_for_session
from config import Settings


def test_selects_male_voice_for_session() -> None:
    settings = Settings(
        VOIX_FEMME_ID="female_voice",
        VOIX_HOMME_ID="male_voice",
    )

    assert selected_voice_id_for_session(settings, "homme") == "male_voice"


def test_selects_female_voice_for_session() -> None:
    settings = Settings(
        VOIX_FEMME_ID="female_voice",
        VOIX_HOMME_ID="male_voice",
    )

    assert selected_voice_id_for_session(settings, "femme") == "female_voice"


def test_turn_handling_uses_vad_interruption_defaults() -> None:
    settings = Settings()

    assert build_turn_handling(settings) == {
        "turn_detection": "stt",
        "endpointing": {
            "mode": "fixed",
            "min_delay": 0.3,
            "max_delay": 1.2,
        },
        "interruption": {
            "mode": "vad",
        },
        "preemptive_generation": {
            "enabled": False,
            "preemptive_tts": True,
            "max_speech_duration": 6.0,
            "max_retries": 2,
        },
    }


def test_default_deepgram_turn_thresholds_are_latency_oriented() -> None:
    settings = Settings()

    assert settings.deepgram_eager_eot_threshold == 0.4
    assert settings.deepgram_eot_threshold == 0.7
    assert settings.deepgram_eot_timeout_ms == 3000
    assert settings.elevenlabs_tts_model == "eleven_multilingual_v2"
    assert settings.aec_warmup_duration == 0.8
    assert settings.discard_audio_if_uninterruptible is False
    assert settings.preemptive_generation_enabled is False
    assert settings.preemptive_tts is True
    assert settings.preemptive_max_speech_duration == 6.0
    assert settings.preemptive_max_retries == 2
    assert settings.log_detail == "normal"
