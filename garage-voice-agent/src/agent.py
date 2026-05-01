import asyncio
import json
import logging
import os
import re
import unicodedata
from typing import Any

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
)
from livekit.plugins import deepgram, elevenlabs, openai, silero
from openai import AsyncOpenAI

try:
    from livekit.plugins import ai_coustics
except ImportError:  # pragma: no cover - optional plugin in self-hosted setups
    ai_coustics = None

from config import PROJECT_ROOT, Settings, get_settings
from identity import normalize_customer_identity_payload
from logging_config import configure_logging
from prompts import load_system_prompt
from tools.calendar_tools import check_availability as check_availability_impl
from tools.calendar_tools import create_appointment as create_appointment_impl
from tools.call_record_tools import classify_urgency as classify_urgency_impl
from tools.call_record_tools import create_call_record as create_call_record_impl
from tools.handoff_tools import transfer_to_human as transfer_to_human_impl
from tools.notification_tools import send_confirmation_sms as send_confirmation_sms_impl
from tools.notification_tools import send_garage_summary_email as send_garage_summary_email_impl
from tts_text import oralize_tts_stream

logger = logging.getLogger("garage_voice_agent")

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".envrc")
configure_logging(log_detail=os.getenv("LOG_DETAIL", "normal").strip().lower())


_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def schedule_background_task(coro: Any) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def publish_call_sheet_payload(room: rtc.Room, source: str, payload: dict[str, Any]) -> None:
    await room.local_participant.publish_data(
        json.dumps(
            {
                "type": "voiceauto_call_sheet",
                "source": source,
                source: payload,
            },
            ensure_ascii=False,
        ),
        reliable=True,
        topic="voiceauto_call_sheet",
    )
    logger.info("call_sheet_payload_published", extra={"source": source})


def clean_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def strip_json_fence(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


FRENCH_NUMBER_WORDS = {
    "zero": 0,
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
    "onze": 11,
    "douze": 12,
    "treize": 13,
    "quatorze": 14,
    "quinze": 15,
    "seize": 16,
    "vingt": 20,
    "vingts": 20,
    "trente": 30,
    "quarante": 40,
    "cinquante": 50,
    "soixante": 60,
}


def normalize_spoken_text(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9+]+", " ", ascii_text).split()


def french_number_value(tokens: list[str]) -> int | None:
    tokens = [token for token in tokens if token != "et"]
    if not tokens:
        return None
    if len(tokens) == 1:
        return FRENCH_NUMBER_WORDS.get(tokens[0])
    if tokens[:2] == ["quatre", "vingt"]:
        suffix = french_number_value(tokens[2:]) if len(tokens) > 2 else 0
        return 80 + suffix if suffix is not None and suffix <= 19 else None
    first = FRENCH_NUMBER_WORDS.get(tokens[0])
    if first is None:
        return None
    if first in {20, 30, 40, 50}:
        suffix = french_number_value(tokens[1:])
        return first + suffix if suffix is not None and 0 < suffix < 10 else None
    if first == 60:
        suffix = french_number_value(tokens[1:])
        return first + suffix if suffix is not None and 0 < suffix < 20 else None
    return None


def parse_french_number_chunk(tokens: list[str], start: int) -> tuple[int, int] | None:
    for length in range(4, 0, -1):
        value = french_number_value(tokens[start : start + length])
        if value is not None and 0 <= value <= 99:
            return value, length
    return None


def normalize_french_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if digits.startswith("33") and len(digits) == 11:
        digits = f"0{digits[2:]}"
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    return None


def extract_french_phone_number(text: str) -> str | None:
    numeric_phone = normalize_french_phone(text)
    if numeric_phone:
        return numeric_phone

    tokens = normalize_spoken_text(text)
    for index, token in enumerate(tokens[:-1]):
        if token != "zero":
            continue
        first_digit = FRENCH_NUMBER_WORDS.get(tokens[index + 1])
        if first_digit is None or not 1 <= first_digit <= 9:
            continue
        cursor = index + 2
        chunks = [f"0{first_digit}"]
        while len(chunks) < 5:
            parsed = parse_french_number_chunk(tokens, cursor)
            if parsed is None:
                break
            value, consumed = parsed
            chunks.append(f"{value:02d}")
            cursor += consumed
        if len(chunks) == 5:
            return "".join(chunks)
    return None


class LiveCallSheetState:
    def __init__(self, room: rtc.Room, settings: Settings) -> None:
        self.room = room
        self.settings = settings
        self.user_transcripts: list[str] = []
        self.assistant_messages: list[str] = []
        self.record_payload: dict[str, Any] | None = None
        self.appointment_payload: dict[str, Any] | None = None
        self.identity_payload: dict[str, Any] | None = None
        self._lock = asyncio.Lock()

    def add_user_transcript(self, transcript: str) -> None:
        transcript = transcript.strip()
        if transcript:
            self.user_transcripts.append(transcript)

    def add_assistant_message(self, message: str) -> None:
        message = message.strip()
        if message:
            self.assistant_messages.append(message)

    async def publish(self, source: str, payload: dict[str, Any]) -> None:
        if source == "record":
            self.record_payload = payload
        if source == "appointment":
            self.appointment_payload = payload
        await publish_call_sheet_payload(self.room, source, payload)

    def conversation_text(self) -> str:
        lines: list[str] = []
        for text in self.user_transcripts:
            lines.append(f"Client: {text}")
        for text in self.assistant_messages[-3:]:
            lines.append(f"Assistant: {text}")
        return "\n".join(lines).strip()

    def best_phone(self, fallback: str | None) -> str | None:
        transcript_phone = extract_french_phone_number("\n".join(self.user_transcripts))
        return transcript_phone or normalize_french_phone(fallback) or clean_text(fallback)

    def set_identity(self, payload: dict[str, Any]) -> None:
        if payload.get("caller_name") and not payload.get("needs_reask"):
            self.identity_payload = payload

    def best_caller_name(self, fallback: str | None) -> str | None:
        if self.identity_payload and self.identity_payload.get("caller_name"):
            return clean_text(self.identity_payload.get("caller_name"))
        return clean_text(fallback)

    def looks_like_recap(self, message: str) -> bool:
        normalized = message.lower()
        return any(
            marker in normalized
            for marker in (
                "je vous récapitule",
                "je vous recapitul",
                "nous avons rendez-vous",
                "rendez-vous le",
            )
        )

    def should_refresh_record(self, reason: str) -> bool:
        if self.record_payload is None:
            return True
        return reason == "disconnect" and self.record_payload.get("source") == "assistant_recap"

    async def ensure_sheet(self, reason: str) -> None:
        async with self._lock:
            if self.record_payload is not None and not self.should_refresh_record(reason):
                await self.publish("record", self.record_payload)
                return

            extracted = await self.extract_with_llm()
            if extracted is None:
                extracted = self.fallback_extraction()

            appointment_payload = self.build_appointment_payload(extracted)
            if appointment_payload is not None:
                await self.publish("appointment", appointment_payload)

            record_payload = self.build_record_payload(extracted, reason)
            await self.publish("record", record_payload)
            logger.info("fallback_call_sheet_published", extra={"reason": reason})

    async def extract_with_llm(self) -> dict[str, Any] | None:
        api_key = self.settings.llm_api_key
        if not api_key:
            return None

        transcript = self.conversation_text()
        if not transcript:
            return None

        client = AsyncOpenAI(
            api_key=api_key,
            timeout=5.0,
        )
        try:
            completion = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.settings.openai_model_name,
                    temperature=0,
                    max_tokens=500,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Tu extrais une fiche garage depuis une conversation vocale. "
                                "Reponds uniquement en JSON valide. Si une information manque, mets null. "
                                "Champs attendus: caller_name, phone, email, vehicle_make, vehicle_model, "
                                "license_plate, intent, urgency, requested_action, appointment_datetime, "
                                "appointment_confirmed, summary, notes."
                            ),
                        },
                        {"role": "user", "content": transcript},
                    ],
                ),
                timeout=6,
            )
        except Exception as error:
            logger.warning("call_sheet_llm_extraction_failed", extra={"error": str(error)})
            return None
        finally:
            await client.close()

        content = completion.choices[0].message.content
        if not content:
            return None

        try:
            payload = json.loads(strip_json_fence(content))
        except json.JSONDecodeError:
            logger.warning("call_sheet_llm_json_invalid", extra={"content": content[:300]})
            return None
        return payload if isinstance(payload, dict) else None

    def fallback_extraction(self) -> dict[str, Any]:
        transcript = self.conversation_text()
        summary_source = self.assistant_messages[-1] if self.assistant_messages else transcript
        return {
            "caller_name": None,
            "phone": self.extract_phone(transcript),
            "email": None,
            "vehicle_make": None,
            "vehicle_model": None,
            "license_plate": None,
            "intent": "revision_entretien" if "révision" in transcript.lower() or "revision" in transcript.lower() else "autre",
            "urgency": "low",
            "requested_action": "appointment" if "rendez-vous" in transcript.lower() else "unknown",
            "appointment_datetime": None,
            "appointment_confirmed": "rendez-vous" in summary_source.lower(),
            "summary": summary_source or "Informations collectées pendant l'appel.",
            "notes": "Fiche générée depuis le récapitulatif de l'appel.",
        }

    def build_record_payload(self, extracted: dict[str, Any], reason: str) -> dict[str, Any]:
        summary = clean_text(extracted.get("summary")) or "Informations collectées pendant l'appel."
        phone = self.best_phone(clean_text(extracted.get("phone")))
        record = create_call_record_impl(
            caller_name=self.best_caller_name(clean_text(extracted.get("caller_name"))),
            phone=phone,
            email=clean_text(extracted.get("email")),
            vehicle_make=clean_text(extracted.get("vehicle_make")),
            vehicle_model=clean_text(extracted.get("vehicle_model")),
            license_plate=clean_text(extracted.get("license_plate")),
            intent=clean_text(extracted.get("intent")) or "autre",
            urgency=clean_text(extracted.get("urgency")) or "low",
            requested_action=clean_text(extracted.get("requested_action")) or "unknown",
            summary=summary,
            status="open",
            risk_flags=[],
        )
        payload = record.model_dump(mode="json")
        payload["source"] = reason
        return payload

    def build_appointment_payload(self, extracted: dict[str, Any]) -> dict[str, Any] | None:
        appointment_datetime = clean_text(extracted.get("appointment_datetime"))
        appointment_confirmed = bool(extracted.get("appointment_confirmed"))
        if not appointment_datetime and not appointment_confirmed:
            return self.appointment_payload
        phone = self.best_phone(clean_text(extracted.get("phone")))
        return {
            "caller_name": self.best_caller_name(clean_text(extracted.get("caller_name"))),
            "phone": phone,
            "vehicle": {
                "make": clean_text(extracted.get("vehicle_make")),
                "model": clean_text(extracted.get("vehicle_model")),
                "license_plate": clean_text(extracted.get("license_plate")),
            },
            "service_type": clean_text(extracted.get("intent")) or "autre",
            "datetime": appointment_datetime or "Rendez-vous confirmé pendant l'appel",
            "status": "confirmed",
            "notes": clean_text(extracted.get("notes")),
        }

    @staticmethod
    def extract_phone(text: str) -> str | None:
        return extract_french_phone_number(text)


class GarageAgent(Agent):
    def __init__(
        self,
        settings: Settings | None = None,
        room: rtc.Room | None = None,
        call_sheet_state: LiveCallSheetState | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.room = room
        self.call_sheet_state = call_sheet_state
        super().__init__(instructions=load_system_prompt())

    async def publish_call_sheet_update(self, source: str, payload: dict[str, Any]) -> None:
        if self.call_sheet_state is not None:
            await self.call_sheet_state.publish(source, payload)
            return
        if self.room is None:
            return
        await publish_call_sheet_payload(self.room, source, payload)

    @function_tool()
    async def normalize_customer_identity(
        self,
        context: RunContext,
        first_name: str | None,
        last_name_heard: str | None,
        spelling_transcript: str,
    ) -> dict[str, Any]:
        """Normalise le nom client depuis l'epellation avant toute confirmation orale.

        Args:
            first_name: Prenom entendu, si disponible.
            last_name_heard: Nom de famille entendu comme un mot, meme approximatif.
            spelling_transcript: Segment exact ou le client epelle son nom.
        """
        payload = normalize_customer_identity_payload(
            first_name=first_name,
            last_name_heard=last_name_heard,
            spelling_transcript=spelling_transcript,
        )
        if self.call_sheet_state is not None:
            self.call_sheet_state.set_identity(payload)
        return payload

    @function_tool()
    async def check_availability(
        self,
        context: RunContext,
        requested_date: str | None,
        requested_period: str | None,
        service_type: str,
    ) -> dict[str, Any]:
        """Retourne uniquement trois creneaux fictifs disponibles pour la demo.

        Args:
            requested_date: Date souhaitee au format ISO si connue.
            requested_period: Periode souhaitee, par exemple matin ou apres-midi.
            service_type: Type de service demande.
        """
        response = check_availability_impl(requested_date, requested_period, service_type)
        return response.model_dump(mode="json")

    @function_tool()
    async def create_appointment(
        self,
        context: RunContext,
        caller_name: str | None,
        phone: str | None,
        vehicle_make: str | None,
        vehicle_model: str | None,
        license_plate: str | None,
        service_type: str,
        selected_datetime: str,
        selected_slot_id: str | None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Cree un rendez-vous mocke apres un check_availability.

        Args:
            caller_name: Nom du client.
            phone: Telephone du client.
            vehicle_make: Marque du vehicule.
            vehicle_model: Modele du vehicule.
            license_plate: Immatriculation si connue.
            service_type: Type de service.
            selected_datetime: Date/heure du creneau choisi.
            selected_slot_id: Identifiant du creneau renvoye par check_availability.
            notes: Notes utiles pour le garage.
        """
        if self.call_sheet_state is not None:
            phone = self.call_sheet_state.best_phone(phone)
            caller_name = self.call_sheet_state.best_caller_name(caller_name)
        else:
            phone = normalize_french_phone(phone) or clean_text(phone)
        appointment = create_appointment_impl(
            caller_name=caller_name,
            phone=phone,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            license_plate=license_plate,
            service_type=service_type,
            selected_datetime=selected_datetime,
            selected_slot_id=selected_slot_id,
            notes=notes,
        )
        appointment_payload = appointment.model_dump(mode="json")
        await self.publish_call_sheet_update("appointment", appointment_payload)
        return appointment_payload

    @function_tool()
    async def create_call_record(
        self,
        context: RunContext,
        caller_name: str | None,
        phone: str | None,
        email: str | None,
        vehicle_make: str | None,
        vehicle_model: str | None,
        license_plate: str | None,
        intent: str,
        urgency: str,
        requested_action: str,
        summary: str,
        status: str = "open",
        risk_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Cree une fiche appel exploitable, meme avec des informations incompletes."""
        if self.call_sheet_state is not None:
            phone = self.call_sheet_state.best_phone(phone)
            caller_name = self.call_sheet_state.best_caller_name(caller_name)
        else:
            phone = normalize_french_phone(phone) or clean_text(phone)
        record = create_call_record_impl(
            caller_name=caller_name,
            phone=phone,
            email=email,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            license_plate=license_plate,
            intent=intent,
            urgency=urgency,
            requested_action=requested_action,
            summary=summary,
            status=status,
            risk_flags=risk_flags,
        )
        record_payload = record.model_dump(mode="json")
        await self.publish_call_sheet_update("record", record_payload)
        return record_payload

    @function_tool()
    async def send_confirmation_sms(self, context: RunContext, phone: str | None, message: str) -> dict[str, Any]:
        """Log un SMS de confirmation sans envoyer de vrai message."""
        return send_confirmation_sms_impl(phone, message)

    @function_tool()
    async def send_garage_summary_email(
        self,
        context: RunContext,
        to_email: str | None,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        """Log un email de synthese garage sans envoyer de vrai email."""
        return send_garage_summary_email_impl(to_email, subject, body)

    @function_tool()
    async def transfer_to_human(
        self,
        context: RunContext,
        reason: str,
        caller_name: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any]:
        """Demande un transfert ou rappel humain pour les cas urgents, complexes ou demandes par le client."""
        return transfer_to_human_impl(reason=reason, caller_name=caller_name, phone=phone)

    @function_tool()
    async def classify_urgency(self, context: RunContext, description: str) -> dict[str, Any]:
        """Classe l'urgence sans poser de diagnostic mecanique definitif."""
        return classify_urgency_impl(description)


def build_stt(settings: Settings):
    model = settings.deepgram_stt_model.lower()
    if "flux" in model:
        flux_model = "flux-general-multi" if "multi" in model else "flux-general-en"
        return deepgram.STTv2(
            model=flux_model,
            eager_eot_threshold=settings.deepgram_eager_eot_threshold,
            eot_threshold=settings.deepgram_eot_threshold,
            eot_timeout_ms=settings.deepgram_eot_timeout_ms,
            language_hint=[settings.deepgram_language_hint],
            api_key=settings.deepgram_api_key,
        )
    language = "multi" if settings.deepgram_language_hint in {"fr", "multi"} else settings.deepgram_language_hint
    return deepgram.STT(
        model=settings.deepgram_stt_fallback_model,
        language=language,
        api_key=settings.deepgram_api_key,
    )


def build_llm(settings: Settings):
    kwargs: dict[str, Any] = {
        "model": settings.openai_model_name,
        "api_key": settings.openai_api_key,
        "temperature": settings.llm_temperature,
    }
    if settings.resolved_reasoning_effort:
        kwargs["reasoning_effort"] = settings.resolved_reasoning_effort
    return openai.LLM(**kwargs)


def selected_voice_id_for_session(settings: Settings, voice: str | None = None) -> str:
    normalized_voice = (voice or settings.voice_gender).strip().lower()
    if normalized_voice in {"homme", "male", "man", "masculin"} and settings.voix_homme_id:
        return settings.voix_homme_id
    if normalized_voice in {"femme", "female", "woman", "feminin", "féminin"} and settings.voix_femme_id:
        return settings.voix_femme_id
    return settings.selected_voice_id


def pronunciation_dictionary_locators(
    settings: Settings,
) -> list[elevenlabs.PronunciationDictionaryLocator] | None:
    dictionary_id = settings.elevenlabs_pronunciation_dictionary_id
    version_id = settings.elevenlabs_pronunciation_dictionary_version_id
    if not dictionary_id and not version_id:
        return None
    if not dictionary_id or not version_id:
        logger.warning(
            "elevenlabs_pronunciation_dictionary_incomplete",
            extra={
                "has_dictionary_id": bool(dictionary_id),
                "has_version_id": bool(version_id),
            },
        )
        return None
    return [
        elevenlabs.PronunciationDictionaryLocator(
            pronunciation_dictionary_id=dictionary_id,
            version_id=version_id,
        )
    ]


def session_metadata(ctx: JobContext) -> dict[str, Any]:
    if not ctx.job.metadata:
        return {}
    try:
        metadata = json.loads(ctx.job.metadata)
    except json.JSONDecodeError:
        logger.warning("invalid LiveKit job metadata", extra={"metadata": ctx.job.metadata})
        return {}
    return metadata if isinstance(metadata, dict) else {}


def build_tts(settings: Settings, voice: str | None = None):
    if settings.elevenlabs_api_key:
        os.environ.setdefault("ELEVEN_API_KEY", settings.elevenlabs_api_key)
    kwargs: dict[str, Any] = {}
    locators = pronunciation_dictionary_locators(settings)
    if locators:
        kwargs["pronunciation_dictionary_locators"] = locators
    return elevenlabs.TTS(
        voice_id=selected_voice_id_for_session(settings, voice),
        model=settings.elevenlabs_tts_model,
        language="fr",
        api_key=settings.elevenlabs_api_key,
        apply_text_normalization=settings.elevenlabs_apply_text_normalization,
        **kwargs,
    )


def build_turn_handling(settings: Settings) -> dict[str, Any]:
    return {
        "turn_detection": "stt",
        "endpointing": {
            "mode": "fixed",
            "min_delay": settings.endpointing_min_delay,
            "max_delay": settings.endpointing_max_delay,
        },
        "interruption": {
            "mode": "adaptive",
            "min_duration": settings.interruption_min_duration,
            "min_words": settings.interruption_min_words,
            "false_interruption_timeout": settings.false_interruption_timeout,
            "discard_audio_if_uninterruptible": settings.discard_audio_if_uninterruptible,
            "resume_false_interruption": True,
        },
        "preemptive_generation": {
            "enabled": settings.preemptive_generation_enabled,
            "preemptive_tts": settings.preemptive_tts,
            "max_speech_duration": settings.preemptive_max_speech_duration,
            "max_retries": settings.preemptive_max_retries,
        },
    }


def initial_greeting(settings: Settings) -> str:
    return (
        f"Bonjour, je suis l'assistant virtuel du {settings.garage_name}. "
        "Comment puis-je vous aider?"
    )


def seconds_to_ms(value: Any) -> float | None:
    return round(value * 1000, 2) if isinstance(value, int | float) else None


def log_voice_metric(metric: Any, log_detail: str = "normal") -> None:
    metric_payload = metric.model_dump(mode="json")
    metadata = metric_payload.get("metadata") or {}
    metric_type = metric_payload.get("type")
    if metric_type == "vad_metrics":
        return
    if log_detail == "quiet":
        return
    if log_detail != "debug" and metric_type == "stt_metrics":
        logger.debug(
            "voice_metric_collected",
            extra={
                "metric_type": metric_type,
                "metric_provider": metadata.get("model_provider"),
                "metric_model": metadata.get("model_name"),
                "metric_request_id": metric_payload.get("request_id"),
            },
        )
        return
    timing_fields = {
        f"{key}_ms": seconds_to_ms(metric_payload.get(key))
        for key in (
            "duration",
            "ttft",
            "ttfb",
            "audio_duration",
            "acquire_time",
            "end_of_utterance_delay",
            "transcription_delay",
            "on_user_turn_completed_delay",
            "total_duration",
            "prediction_duration",
            "detection_delay",
        )
        if seconds_to_ms(metric_payload.get(key)) is not None
    }
    extra = {
        "metric_type": metric_type,
        "metric_label": metric_payload.get("label"),
        "metric_provider": metadata.get("model_provider"),
        "metric_model": metadata.get("model_name"),
        "metric_request_id": metric_payload.get("request_id"),
        "metric_speech_id": metric_payload.get("speech_id"),
        "metric_timing": timing_fields,
    }
    if log_detail == "debug":
        extra["metric"] = metric_payload
    logger.info(
        "voice_metric_collected",
        extra=extra,
    )


def log_turn_message_metrics(item: Any, log_detail: str = "normal") -> None:
    metrics = getattr(item, "metrics", None)
    if not metrics:
        return
    text_content = getattr(item, "text_content", None)
    text_preview = text_content[:180] if isinstance(text_content, str) else None
    extra = {
        "message_role": getattr(item, "role", None),
        "message_id": getattr(item, "id", None),
        "message_text_preview": text_preview,
        "e2e_latency_ms": seconds_to_ms(metrics.get("e2e_latency")),
        "llm_node_ttft_ms": seconds_to_ms(metrics.get("llm_node_ttft")),
        "tts_node_ttfb_ms": seconds_to_ms(metrics.get("tts_node_ttfb")),
        "transcription_delay_ms": seconds_to_ms(metrics.get("transcription_delay")),
        "end_of_turn_delay_ms": seconds_to_ms(metrics.get("end_of_turn_delay")),
        "on_user_turn_completed_delay_ms": seconds_to_ms(
            metrics.get("on_user_turn_completed_delay")
        ),
    }
    if log_detail == "debug":
        extra["turn_metrics"] = dict(metrics)
    logger.info(
        "voice_turn_message_metrics",
        extra=extra,
    )


def register_session_observability(
    session: AgentSession,
    settings: Settings,
    call_sheet_state: LiveCallSheetState | None = None,
) -> None:
    def on_metrics_collected(event: Any) -> None:
        log_voice_metric(event.metrics, settings.log_detail)

    def on_conversation_item_added(event: Any) -> None:
        log_turn_message_metrics(event.item, settings.log_detail)
        text_content = getattr(event.item, "text_content", None)
        if not isinstance(text_content, str) or not call_sheet_state:
            return
        role = getattr(event.item, "role", None)
        if role == "assistant":
            call_sheet_state.add_assistant_message(text_content)
            if call_sheet_state.looks_like_recap(text_content):
                schedule_background_task(call_sheet_state.ensure_sheet("assistant_recap"))

    def on_user_input_transcribed(event: Any) -> None:
        log_method = logger.info if event.is_final or settings.log_detail == "debug" else logger.debug
        log_method(
            "voice_user_transcript",
            extra={
                "transcript_final": event.is_final,
                "transcript_language": str(event.language) if event.language else None,
                "transcript_text": event.transcript,
            },
        )
        if call_sheet_state is not None and event.is_final:
            call_sheet_state.add_user_transcript(event.transcript)

    def on_agent_state_changed(event: Any) -> None:
        log_method = logger.debug if settings.log_detail != "debug" else logger.info
        log_method(
            "voice_agent_state_changed",
            extra={"old_state": event.old_state, "new_state": event.new_state},
        )

    def on_user_state_changed(event: Any) -> None:
        log_method = logger.debug if settings.log_detail != "debug" else logger.info
        log_method(
            "voice_user_state_changed",
            extra={"old_state": event.old_state, "new_state": event.new_state},
        )

    def on_speech_created(event: Any) -> None:
        speech_handle = event.speech_handle
        log_method = logger.debug if settings.log_detail != "debug" else logger.info
        log_method(
            "voice_speech_created",
            extra={
                "speech_id": getattr(speech_handle, "id", None),
                "speech_source": event.source,
                "speech_user_initiated": event.user_initiated,
            },
        )

    def on_agent_false_interruption(event: Any) -> None:
        logger.warning(
            "voice_false_interruption",
            extra={"false_interruption_resumed": event.resumed},
        )

    session.on("metrics_collected", on_metrics_collected)
    session.on("conversation_item_added", on_conversation_item_added)
    session.on("user_input_transcribed", on_user_input_transcribed)
    session.on("user_state_changed", on_user_state_changed)
    session.on("agent_state_changed", on_agent_state_changed)
    session.on("speech_created", on_speech_created)
    session.on("agent_false_interruption", on_agent_false_interruption)


def register_call_sheet_finalization(room: rtc.Room, call_sheet_state: LiveCallSheetState) -> None:
    def on_data_received(packet: rtc.DataPacket) -> None:
        if packet.topic != "voiceauto_finalize":
            return
        try:
            payload = json.loads(packet.data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("invalid finalization payload")
            return
        if isinstance(payload, dict) and payload.get("type") == "voiceauto_finalize":
            schedule_background_task(call_sheet_state.ensure_sheet("disconnect"))

    room.on("data_received", on_data_received)


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=get_settings().agent_name)
async def garage_voice_session(ctx: JobContext) -> None:
    settings = get_settings()
    metadata = session_metadata(ctx)
    voice = metadata.get("voice")
    voice = voice if isinstance(voice, str) else None
    ctx.log_context_fields = {"room": ctx.room.name, "agent": settings.agent_name, "voice": voice}
    logger.info(
        "starting garage voice session",
        extra={"room": ctx.room.name, "voice": voice or settings.voice_gender},
    )

    session = AgentSession(
        stt=build_stt(settings),
        llm=build_llm(settings),
        tts=build_tts(settings, voice),
        tts_text_transforms=["filter_markdown", "filter_emoji", oralize_tts_stream],
        vad=ctx.proc.userdata["vad"],
        turn_handling=build_turn_handling(settings),
        aec_warmup_duration=settings.aec_warmup_duration,
    )
    call_sheet_state = LiveCallSheetState(ctx.room, settings)
    register_session_observability(session, settings, call_sheet_state)
    register_call_sheet_finalization(ctx.room, call_sheet_state)

    audio_input = room_io.AudioInputOptions()
    if ai_coustics is not None:
        audio_input = room_io.AudioInputOptions(
            noise_cancellation=ai_coustics.audio_enhancement(
                model=ai_coustics.EnhancerModel.QUAIL_VF_L
            )
        )

    await session.start(
        room=ctx.room,
        agent=GarageAgent(settings, ctx.room, call_sheet_state),
        room_options=room_io.RoomOptions(audio_input=audio_input),
    )
    await ctx.connect()
    await session.generate_reply(
        instructions=f"Dis exactement: {initial_greeting(settings)}"
    )


if __name__ == "__main__":
    cli.run_app(server)
