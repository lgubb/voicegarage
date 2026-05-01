from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_env_files() -> None:
    load_dotenv(PROJECT_ROOT.parent / ".envrc")
    load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    livekit_url: str | None = Field(default=None, alias="LIVEKIT_URL")
    livekit_api_key: str | None = Field(default=None, alias="LIVEKIT_API_KEY")
    livekit_api_secret: str | None = Field(default=None, alias="LIVEKIT_API_SECRET")

    deepgram_api_key: str | None = Field(default=None, alias="DEEPGRAM_API_KEY")
    deepgram_stt_model: str = Field(default="flux-general-multi", alias="DEEPGRAM_STT_MODEL")
    deepgram_language_hint: str = Field(default="fr", alias="DEEPGRAM_LANGUAGE_HINT")
    deepgram_stt_fallback_model: str = Field(default="nova-3", alias="DEEPGRAM_STT_FALLBACK_MODEL")
    deepgram_eager_eot_threshold: float = Field(default=0.4, alias="DEEPGRAM_EAGER_EOT_THRESHOLD")
    deepgram_eot_threshold: float = Field(default=0.7, alias="DEEPGRAM_EOT_THRESHOLD")
    deepgram_eot_timeout_ms: int = Field(default=3000, alias="DEEPGRAM_EOT_TIMEOUT_MS")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4.1-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=180, alias="LLM_MAX_TOKENS")
    llm_reasoning_effort: str | None = Field(default=None, alias="LLM_REASONING_EFFORT")

    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")
    elevenlabs_tts_model: str = Field(default="eleven_multilingual_v2", alias="ELEVENLABS_TTS_MODEL")
    elevenlabs_tts_fallback_model: str = Field(default="eleven_multilingual_v2", alias="ELEVENLABS_TTS_FALLBACK_MODEL")
    elevenlabs_apply_text_normalization: str = Field(default="on", alias="ELEVENLABS_APPLY_TEXT_NORMALIZATION")
    elevenlabs_stability: float = Field(default=0.45, alias="ELEVENLABS_STABILITY")
    elevenlabs_similarity_boost: float = Field(default=0.75, alias="ELEVENLABS_SIMILARITY_BOOST")
    elevenlabs_style: float = Field(default=0.0, alias="ELEVENLABS_STYLE")
    elevenlabs_use_speaker_boost: bool = Field(default=False, alias="ELEVENLABS_USE_SPEAKER_BOOST")
    elevenlabs_speed: float = Field(default=0.95, alias="ELEVENLABS_SPEED")
    elevenlabs_pronunciation_dictionary_id: str | None = Field(
        default=None, alias="ELEVENLABS_PRONUNCIATION_DICTIONARY_ID"
    )
    elevenlabs_pronunciation_dictionary_version_id: str | None = Field(
        default=None, alias="ELEVENLABS_PRONUNCIATION_DICTIONARY_VERSION_ID"
    )
    voix_femme_id: str | None = Field(default=None, alias="VOIX_FEMME_ID")
    voix_homme_id: str | None = Field(default=None, alias="VOIX_HOMME_ID")
    voice_gender: str = Field(default="female", alias="VOICE_GENDER")

    endpointing_min_delay: float = Field(default=0.3, alias="ENDPOINTING_MIN_DELAY")
    endpointing_max_delay: float = Field(default=1.2, alias="ENDPOINTING_MAX_DELAY")
    interruption_min_duration: float = Field(default=0.6, alias="INTERRUPTION_MIN_DURATION")
    interruption_min_words: int = Field(default=1, alias="INTERRUPTION_MIN_WORDS")
    false_interruption_timeout: float = Field(default=0.4, alias="FALSE_INTERRUPTION_TIMEOUT")
    discard_audio_if_uninterruptible: bool = Field(default=False, alias="DISCARD_AUDIO_IF_UNINTERRUPTIBLE")
    aec_warmup_duration: float | None = Field(default=0.8, alias="AEC_WARMUP_DURATION")
    preemptive_generation_enabled: bool = Field(default=False, alias="PREEMPTIVE_GENERATION_ENABLED")
    preemptive_tts: bool = Field(default=True, alias="PREEMPTIVE_TTS")
    preemptive_max_speech_duration: float = Field(default=6.0, alias="PREEMPTIVE_MAX_SPEECH_DURATION")
    preemptive_max_retries: int = Field(default=2, alias="PREEMPTIVE_MAX_RETRIES")

    garage_name: str = Field(default="garage Martin", alias="GARAGE_NAME")
    agent_name: str = Field(default="garage-voice-agent", alias="AGENT_NAME")

    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    mock_calendar: bool = Field(default=True, alias="MOCK_CALENDAR")
    mock_sms: bool = Field(default=True, alias="MOCK_SMS")
    mock_email: bool = Field(default=True, alias="MOCK_EMAIL")
    mock_handoff: bool = Field(default=True, alias="MOCK_HANDOFF")
    log_detail: str = Field(default="normal", alias="LOG_DETAIL")

    @field_validator("elevenlabs_tts_model", "elevenlabs_tts_fallback_model")
    @classmethod
    def normalize_elevenlabs_model(cls, value: str) -> str:
        return value.removeprefix("elevenlabs/")

    @field_validator(
        "elevenlabs_stability",
        "elevenlabs_similarity_boost",
        "elevenlabs_style",
    )
    @classmethod
    def clamp_elevenlabs_unit_interval(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)

    @field_validator("elevenlabs_speed")
    @classmethod
    def clamp_elevenlabs_speed(cls, value: float) -> float:
        return min(max(value, 0.7), 1.2)

    @field_validator("log_detail")
    @classmethod
    def normalize_log_detail(cls, value: str) -> str:
        normalized = value.strip().lower()
        return normalized if normalized in {"debug", "normal", "quiet"} else "normal"

    @property
    def selected_voice_id(self) -> str:
        if self.voice_gender.lower() == "male" and self.voix_homme_id:
            return self.voix_homme_id
        if self.voix_femme_id:
            return self.voix_femme_id
        return "EXAVITQu4vr4xnSDxMaL"

    @property
    def resolved_llm_model(self) -> str:
        return self.llm_model.strip().removeprefix("openai/")

    @property
    def openai_model_name(self) -> str:
        return self.resolved_llm_model

    @property
    def llm_api_key(self) -> str | None:
        return self.openai_api_key

    @property
    def resolved_reasoning_effort(self) -> str | None:
        if self.llm_reasoning_effort:
            return self.llm_reasoning_effort.strip().lower()
        if self.openai_model_name.startswith("gpt-5.4"):
            return "none"
        return None

    @property
    def prompt_path(self) -> Path:
        return PROJECT_ROOT / "prompts" / "garage_agent_system.md"


@lru_cache
def get_settings() -> Settings:
    _load_env_files()
    return Settings()
