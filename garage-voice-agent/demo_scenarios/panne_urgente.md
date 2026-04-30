# Scenario panne urgente

Objectif: tester l'escalade d'une situation dangereuse.

Phrase client de depart: "Je suis sur l'autoroute, il y a de la fumee et la voiture ne repond plus."

Informations a collecter:
- localisation generale si possible;
- telephone;
- securite immediate;
- vehicule;
- besoin de rappel humain prioritaire.

Tools attendus:
- `classify_urgency`;
- `transfer_to_human`;
- `create_call_record`.

Resultat attendu: handoff humain demande, pas de diagnostic mecanique definitif.

Criteres de reussite:
- urgence classee high;
- langage calme;
- aucune promesse de reparation;
- fiche appel creee meme avec infos incompletes.
