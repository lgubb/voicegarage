# Scenario informations incompletes

Objectif: verifier qu'une fiche appel reste exploitable avec peu d'informations.

Phrase client de depart: "C'est pour ma voiture, elle fait un bruit, je dois raccrocher."

Informations a collecter:
- minimum: motif;
- tenter telephone et vehicule;
- noter les informations manquantes.

Tools attendus:
- `classify_urgency`;
- `create_call_record`.

Resultat attendu: fiche appel creee avec `missing_info`.

Criteres de reussite:
- aucune erreur si nom/telephone manquent;
- prochaine action: rappeler si numero disponible ou attendre nouvel appel.
