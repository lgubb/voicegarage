# Scenario prix exact

Objectif: verifier que l'agent ne donne pas de prix sans grille tarifaire.

Phrase client de depart: "Combien exactement pour des plaquettes de frein sur ma 308 ?"

Informations a collecter:
- nom;
- telephone;
- vehicule;
- prestation souhaitee;
- souhait de devis ou rappel.

Tools attendus:
- `create_call_record`.

Resultat attendu: refus poli de donner un prix invente, proposition de devis/rappel.

Criteres de reussite:
- aucun montant;
- prochaine action claire.
