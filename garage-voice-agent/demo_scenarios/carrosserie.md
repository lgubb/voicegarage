# Scenario carrosserie

Objectif: tester une demande apres accrochage.

Phrase client de depart: "J'ai eu un accrochage, le pare-choc est abime et je voudrais un devis."

Informations a collecter:
- nom;
- telephone;
- vehicule;
- circonstances simples;
- photos disponibles ou non;
- souhait: devis ou rappel.

Tools attendus:
- `classify_urgency`;
- `create_call_record`;
- `send_garage_summary_email`.

Resultat attendu: pas de diagnostic, collecte des infos utiles pour devis carrosserie.

Criteres de reussite:
- l'agent ne promet pas une reparation;
- il signale si situation dangereuse;
- il finit par un recapitulatif.
