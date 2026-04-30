# Auto Voice Agent

MVP d'agent vocal telephonique pour garages automobiles et carrosseries en France.

Le socle principal est LiveKit Agents. Vapi sert uniquement de benchmark produit public pour les patterns de structured outputs, tools, handoff, logs et evaluations. ElevenLabs est utilise seulement comme provider TTS.

## Stack

- LiveKit Agents Python pour le runtime vocal temps reel.
- Deepgram pour le STT, avec Flux par defaut et fallback Nova-3/multi prevu.
- OpenRouter via le plugin OpenAI compatible LiveKit pour le LLM.
- ElevenLabs Flash v2.5 pour le TTS.
- Pydantic pour les schemas structures.
- FastAPI pour la couche API de demo.
- Next.js, React, TypeScript et Tailwind pour le frontend de demo.
- pytest pour les tests.
- Mocks pour calendrier, SMS, email et handoff humain.

## Installation

```bash
cd garage-voice-agent
uv sync
```

Installer le frontend:

```bash
cd frontend
npm install
cd ..
```

LiveKit Agents demande Python 3.11+ dans ce projet.

## Configuration

Copier `.env.example` vers `.env` ou utiliser le `.envrc` parent deja rempli.

Variables principales:

```env
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
DEEPGRAM_API_KEY=
DEEPGRAM_EAGER_EOT_THRESHOLD=0.4
DEEPGRAM_EOT_THRESHOLD=0.7
DEEPGRAM_EOT_TIMEOUT_MS=3000
OPENROUTER_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_TTS_MODEL=eleven_multilingual_v2
ELEVENLABS_APPLY_TEXT_NORMALIZATION=on
VOIX_FEMME_ID=
VOIX_HOMME_ID=
ENDPOINTING_MIN_DELAY=0.1
ENDPOINTING_MAX_DELAY=0.9
INTERRUPTION_MIN_DURATION=0.6
INTERRUPTION_MIN_WORDS=1
FALSE_INTERRUPTION_TIMEOUT=0.4
DISCARD_AUDIO_IF_UNINTERRUPTIBLE=false
AEC_WARMUP_DURATION=0.8
PREEMPTIVE_TTS=true
PREEMPTIVE_MAX_SPEECH_DURATION=6.0
PREEMPTIVE_MAX_RETRIES=2
GARAGE_NAME=Votre garage
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
LOCAL_CALL_STORE_PATH=./data/calls.json
```

Le plugin LiveKit ElevenLabs attend `ELEVEN_API_KEY`; le code renseigne cette variable automatiquement depuis `ELEVENLABS_API_KEY`.

Frontend: les variables `NEXT_PUBLIC_API_BASE_URL` et `NEXT_PUBLIC_APP_NAME` peuvent rester dans le `.envrc` parent. `frontend/.env.local.example` est seulement un exemple si tu veux lancer le frontend seul sans `direnv`.

## Lancer l'agent

Telecharger les fichiers de modeles locaux LiveKit/Silero:

```bash
uv run src/agent.py download-files
```

Mode console local:

```bash
uv run src/agent.py console
```

Mode developpement connecte a LiveKit:

```bash
uv run src/agent.py dev
```

Mode production:

```bash
uv run src/agent.py start
```

## Lancer l'API

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Endpoints principaux:
- `GET /health`
- `POST /sessions`
- `GET /calls`
- `GET /calls/{call_id}`
- `POST /calls/{call_id}/summary`
- `POST /demo/seed`
- `GET /garage-profile`
- `PUT /garage-profile`

## Lancer le frontend

```bash
cd frontend
npm run dev
```

Ouvrir `http://localhost:3000/demo`.

## Tests

```bash
uv run pytest
cd frontend
npm run typecheck
npm run build
```

Les tests actuels couvrent les tools, schemas, guardrails metier, handoff et generation de fiche appel. Les tests comportementaux LiveKit avec `AgentSession.run()` pourront etre ajoutes quand les cles LLM seront disponibles dans l'environnement CI.

## Changer la voix

Par defaut, l'agent prend `VOIX_FEMME_ID` si renseigne. Pour utiliser la voix homme:

```env
VOICE_GENDER=male
VOIX_HOMME_ID=...
```

Changer le modele TTS:

```env
ELEVENLABS_TTS_MODEL=eleven_multilingual_v2
```

## Changer le modele OpenRouter

```env
OPENROUTER_MODEL=google/gemini-3-flash-preview
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=180
```

Le branchement LiveKit utilise `openai.LLM.with_openrouter`.

## Lancer une demo web

Ordre recommande:

Une seule commande suffit en local:

```bash
uv run garage-voice-dev
```

Depuis la racine du repo parent, utiliser:

```bash
make dev
```

Elle lance l'agent LiveKit, l'API FastAPI et le frontend Next.js. Ouvrir ensuite `http://127.0.0.1:3000/demo`.

Les logs de dev sont ecrits a chaque lancement dans:

- `logs/backend/agent.log`
- `logs/backend/api.log`
- `logs/frontend/web.log`

Pour verifier les variables et l'auth LiveKit sans afficher les secrets:

```bash
make doctor
```

Pour recuperer les credentials LiveKit Cloud via la CLI officielle:

```bash
lk cloud auth
cd garage-voice-agent
lk app env -w
```

Cette commande ecrit `LIVEKIT_URL`, `LIVEKIT_API_KEY` et `LIVEKIT_API_SECRET` dans `garage-voice-agent/.env.local`. Ce fichier est ignore par git et prend priorite sur le `.envrc` parent.

Pour ce repo, la configuration locale propre est de garder les variables dans le `.envrc` parent. Si `lk app env -w` genere un `.env.local`, copie les valeurs utiles dans `.envrc`, puis supprime `garage-voice-agent/.env.local` pour eviter les doublons.

Equivalent manuel si besoin:

1. Lancer l'agent LiveKit: `uv run src/agent.py dev`.
2. Lancer l'API: `uv run uvicorn api.main:app --reload --port 8000`.
3. Lancer le frontend: `cd frontend && npm run dev`.
4. Ouvrir `http://localhost:3000/demo`.
5. Creer une session.
6. Se connecter a l'agent.
7. Parler au micro.
8. Consulter la fiche appel.

Pour enregistrer la video demo, garder a l'ecran `/demo`, puis ouvrir `/calls/{id}` pour montrer la fiche complete.

Scenarios principaux:
- `revision.md`;
- `pneus.md`;
- `carrosserie.md`;
- `panne_urgente.md`.

## Limites actuelles

- Calendrier mocke.
- SMS et emails seulement logues.
- Handoff humain seulement logue.
- Pas encore de numero SIP entrant.
- Pas de dashboard.
- Pas de persistance Supabase/Postgres.
- Le transcript web est mocke tant que les evenements LiveKit ne sont pas persistes automatiquement.
- Flux Deepgram est conserve comme chemin demande avec `flux-general-multi`; le fallback Nova-3/multi reste disponible selon les contraintes fournisseur.

## Prochaines etapes

- Ajouter tests comportementaux LiveKit texte.
- Brancher LiveKit SIP entrant.
- Persister transcripts et fiches appel.
- Remplacer les mocks par Google Calendar/Cal.com, Twilio et SendGrid.
- Ajouter evals par scenario et monitoring de latence.
