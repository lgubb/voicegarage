# Scenario handoff humain

Objectif: verifier le transfert si le client demande une personne.

Phrase client de depart: "Je prefere parler a quelqu'un du garage."

Informations a collecter:
- nom;
- telephone;
- raison courte du rappel si le client accepte.

Tools attendus:
- `transfer_to_human`;
- `create_call_record`.

Resultat attendu: demande de handoff loguee, fiche appel creee.

Criteres de reussite:
- pas d'insistance;
- transfert ou rappel humain priorise.
