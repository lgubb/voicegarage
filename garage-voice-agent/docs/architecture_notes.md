# Notes d'architecture

## Sources et decisions

LiveKit Agents est le socle runtime. La documentation actuelle presente `AgentSession` comme l'orchestrateur principal: il collecte l'entree utilisateur, gere le pipeline STT -> LLM -> TTS, invoque les tools et emet les evenements utiles a l'observabilite. L'agent, lui, porte les instructions et les tools metier.

Sources consultees:
- https://docs.livekit.io/agents/
- https://docs.livekit.io/agents/logic/sessions/
- https://docs.livekit.io/reference/agents/turn-handling-options/
- https://docs.livekit.io/telephony/
- https://docs.livekit.io/agents/start/testing/
- https://docs.livekit.io/agents/models/stt/deepgram/
- https://docs.livekit.io/agents/models/llm/openai/
- https://docs.livekit.io/agents/models/tts/elevenlabs/
- https://github.com/livekit-examples/agent-starter-python
- https://github.com/livekit-examples/python-agents-examples
- https://docs.vapi.ai/how-vapi-works
- https://docs.vapi.ai/tools
- https://docs.vapi.ai/assistants/structured-outputs-quickstart
- https://elevenlabs.io/docs/overview/models
- https://elevenlabs.io/docs/api-reference/text-to-speech

## Structure LiveKit d'un agent vocal

Un serveur LiveKit Agents s'enregistre via `AgentServer`. A chaque dispatch de room, une fonction `@server.rtc_session` cree une `AgentSession`, connecte le job a la room, puis demarre un `Agent`. Le MVP suit cette forme dans `src/agent.py`.

La classe `GarageAgent` herite de `Agent`. Elle charge le prompt systeme depuis `prompts/garage_agent_system.md` et expose les tools avec `@function_tool`. Les fonctions metier reelles restent dans `src/tools/` pour etre testables sans session LiveKit.

## Configuration de session

La session est construite avec:
- `stt=build_stt(settings)`;
- `llm=build_llm(settings)`;
- `tts=build_tts(settings)`;
- `vad=silero.VAD.load()` prechauffe en `prewarm`;
- `turn_detection="stt"` pour utiliser l'endpointing STT quand Flux est actif;
- `preemptive_generation=True` pour reduire la latence.

Les credentials sont charges depuis `.env`, `.env.local` ou le `.envrc` parent. Ils ne sont jamais hardcodes.

## STT, LLM, TTS

STT: Deepgram est branche via le plugin LiveKit `deepgram`. Le chemin par defaut utilise `deepgram.STTv2` pour Flux et respecte `DEEPGRAM_STT_MODEL=flux-general-multi` avec `language_hint=fr`. Le fallback `DEEPGRAM_STT_FALLBACK_MODEL=nova-3` avec `language=multi` reste prevu si Flux n'est pas disponible sur un compte ou une region.

LLM: OpenAI direct passe par le plugin OpenAI compatible LiveKit: `openai.LLM(model=...)`.

TTS: ElevenLabs est seulement utilise comme provider TTS via `elevenlabs.TTS`. Le code aligne `ELEVENLABS_API_KEY` vers `ELEVEN_API_KEY`, nom attendu par le plugin LiveKit. ElevenLabs Agents n'est pas utilise comme orchestrateur.

## Turn detection, interruptions et barge-in

LiveKit combine VAD, STT endpointing et turn detection. Pour Flux, `turn_detection="stt"` exploite les signaux de fin de tour du STT. Le VAD Silero reste actif pour detecter rapidement la parole utilisateur et permettre l'interruption naturelle de la voix agent. Le prompt demande explicitement de s'arreter si le client interrompt.

## Tools

Les tools LiveKit sont des methodes `@function_tool` qui appellent des fonctions pures:
- `check_availability`;
- `create_appointment`;
- `create_call_record`;
- `send_confirmation_sms`;
- `send_garage_summary_email`;
- `transfer_to_human`;
- `classify_urgency`.

Les mocks retournent des objets Pydantic serialisables. `create_appointment` refuse un creneau qui ne vient pas d'un `check_availability`.

## Tests LiveKit

La doc LiveKit recommande les tests texte via `AgentSession.run()` pour verifier messages et appels tools sans demarrer une room audio. Dans ce MVP, les tests unitaires ciblent d'abord les fonctions metier, schemas et guardrails deterministes. La prochaine etape est d'ajouter des tests comportementaux LiveKit avec un LLM de test quand les cles seront disponibles.

## Telephonie SIP future

LiveKit Telephony/SIP permettra de connecter un numero entrant a une room puis de dispatcher l'agent. Le MVP ne bloque pas dessus: l'agent est testable en local via `console`, `dev` ou Agent Console. Le plan SIP est dans `docs/telephony_plan.md`.

## Patterns Vapi utiles a reproduire

Patterns produit publics interessants:
- structured outputs post-call;
- tools metier explicites;
- call summaries lisibles par l'equipe;
- handoff humain;
- logs de tool calls;
- monitoring des erreurs et latences;
- evals de scenarios;
- call flows par intention.

Ces patterns sont des idees produit generales. Ils sont implementes dans notre code avec LiveKit, Pydantic, nos prompts et nos mocks.

## Ce qui ne doit pas etre copie

Ne pas copier le code, la configuration proprietaire, les prompts internes, les schemas exacts de plateforme, le packaging produit ou l'orchestration Vapi/Retell/ElevenLabs Agents. Vapi reste un benchmark public, pas une dependance d'architecture.
