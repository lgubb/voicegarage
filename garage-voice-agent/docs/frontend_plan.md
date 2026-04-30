# Plan frontend

## Objectif

Le frontend Next.js sert a enregistrer une demo commerciale propre: creation de session, connexion LiveKit, scenario choisi, visualisation du transcript, tools et fiche appel.

## Pages

- `/`: page d'accueil courte avec proposition de valeur et acces demo.
- `/demo`: experience principale pour lancer une session vocale.
- `/calls`: liste des fiches appel demo/locales.
- `/calls/[id]`: detail d'un appel avec resume, client, vehicule, flags, transcript, tools et rendez-vous.
- `/settings`: profil garage fictif editable localement.

## Composants

- `VoiceDemoPanel`: cree la session, connecte a LiveKit, gere mute/disconnect, affiche les panneaux demo.
- `ScenarioSelector`: choix revision, pneus, carrosserie, panne urgente ou custom.
- `TranscriptPanel`: affiche messages cles.
- `ToolCallsPanel`: affiche tools et arguments.
- `CallSummaryPanel`: fiche appel structuree.
- `CallRecordCard`: carte liste appels.
- `GarageSettingsForm`: edition du profil demo.

## Parcours demo

1. Lancer l'agent LiveKit.
2. Lancer l'API FastAPI.
3. Lancer Next.js.
4. Ouvrir `/demo`.
5. Choisir scenario et voix.
6. Creer une session.
7. Se connecter a l'agent.
8. Parler au micro.
9. Montrer transcript, tools, fiche appel et detail complet.

## Limites actuelles

- Le frontend affiche des messages/tools mockes tant que le transcript LiveKit n'est pas persiste automatiquement.
- Pas d'authentification.
- Pas de multi-tenant.
- Pas de dashboard analytique.
- Le stockage est local JSON.

## Prochaine etape

Brancher les evenements de session LiveKit cote agent/API pour alimenter le transcript et les tool calls en temps reel, puis persister en base.
