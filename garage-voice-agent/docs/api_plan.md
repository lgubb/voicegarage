# Plan API

## Role

L'API FastAPI sert de couche produit minimale autour du socle LiveKit Agents. Elle ne remplace pas l'agent vocal: elle cree les sessions de demo, genere les tokens LiveKit cote serveur, expose les fiches appel et garde un stockage local remplacable.

## Endpoints

- `GET /health`: verification simple.
- `POST /sessions`: cree une room demo, genere un token LiveKit temporaire et cree une fiche appel locale initiale.
- `GET /calls`: liste les appels mockes ou locaux.
- `GET /calls/{call_id}`: detail complet d'un appel.
- `POST /calls/{call_id}/summary`: regenere un resume structure a partir du transcript et des tool calls.
- `POST /demo/seed`: recharge les quatre appels de demonstration.
- `GET /garage-profile`: profil garage fictif.
- `PUT /garage-profile`: mise a jour du profil garage fictif.

## Securite

`LIVEKIT_API_SECRET` reste uniquement cote API. Le frontend recoit seulement:
- `livekit_url`;
- `room_name`;
- `participant_identity`;
- `token` temporaire;
- `call_id`.

Les cles Deepgram, OpenAI, ElevenLabs et LiveKit secret ne sont jamais exposees dans le frontend.

## Stockage local

`JsonCallStore` ecrit dans `LOCAL_CALL_STORE_PATH` et `LOCAL_GARAGE_PROFILE_PATH`. Les fichiers JSON generes sont ignores par git. L'interface `CallStore` isole les operations principales:
- list;
- get;
- upsert;
- seed demo;
- get/update garage profile.

## Evolution Supabase/Postgres

Remplacer `JsonCallStore` par une implementation `SupabaseCallStore` ou `PostgresCallStore` sans changer les routes. Les tables futures probables:
- `calls`;
- `transcript_messages`;
- `tool_calls`;
- `call_summaries`;
- `garage_profiles`.

La prochaine etape consiste a brancher les evenements LiveKit pour persister automatiquement le transcript, les tool calls et la fiche finale.
