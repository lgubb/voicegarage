# Scenario interruption

Objectif: verifier le comportement barge-in.

Phrase client de depart: "Bonjour, je veux un rendez-vous... attendez, non, c'est pour une panne."

Informations a collecter:
- motif corrige;
- urgence;
- telephone;
- vehicule.

Tools attendus:
- `classify_urgency`;
- `create_call_record`.

Resultat attendu: l'agent s'arrete, ecoute la correction, puis reprend sur le nouveau motif.

Criteres de reussite:
- l'agent ne force pas le flux initial;
- une seule question a la fois.
