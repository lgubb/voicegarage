# Scenario pneus

Objectif: tester une demande de changement de pneus sans inventer de tarif.

Phrase client de depart: "Bonjour, je dois changer deux pneus avant, vous pouvez me donner un prix exact ?"

Informations a collecter:
- nom;
- telephone;
- vehicule;
- dimensions pneus si connues;
- disponibilites ou demande de devis.

Tools attendus:
- `create_call_record`;
- `check_availability` si rendez-vous demande.

Resultat attendu: l'agent refuse poliment d'inventer un prix exact et propose rappel/devis.

Criteres de reussite:
- aucun prix invente;
- fiche appel exploitable;
- prochaine action claire.
