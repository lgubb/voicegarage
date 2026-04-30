# Plan telephonie LiveKit SIP

## Objectif V2

Recevoir les appels entrants d'un garage sur un numero telephonique, router l'appel vers une room LiveKit, faire repondre l'agent, puis transferer vers un humain si necessaire.

## Etapes techniques

1. Creer ou connecter un trunk SIP LiveKit.
2. Associer un numero entrant au trunk.
3. Configurer une regle de dispatch vers une room LiveKit.
4. Demarrer `src/agent.py start` ou deployer l'agent sur LiveKit Cloud.
5. Router les appels entrants vers `AGENT_NAME=garage-voice-agent`.
6. Ajouter la logique de transfert humain dans `transfer_to_human`.
7. Persister transcript, fiche appel et erreurs dans Supabase/Postgres.

## Variables attendues plus tard

```env
LIVEKIT_SIP_TRUNK_ID=
LIVEKIT_SIP_DISPATCH_RULE_ID=
GARAGE_FORWARD_PHONE=
GARAGE_OPENING_HOURS=
CALL_RECORD_DATABASE_URL=
```

## Transfert humain

En demo, `transfer_to_human` log seulement une demande. En pilote reel, ce tool devra:
- mettre l'appel en attente ou annoncer le transfert;
- appeler l'API SIP LiveKit pour transferer vers `GARAGE_FORWARD_PHONE`;
- enregistrer le motif de transfert;
- revenir a une demande de rappel si le transfert echoue.

## Reste a implementer pour pilote reel

- Provisioning SIP et numero entrant.
- Regles par garage.
- Horaires et jours feries.
- Consentement enregistrement/transcription si necessaire.
- Persistance des appels.
- Alertes email/SMS reelles.
- Tests end-to-end audio.
