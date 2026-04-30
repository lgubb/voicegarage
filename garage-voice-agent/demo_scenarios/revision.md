# Scenario revision

Objectif: tester une demande standard de rendez-vous pour revision.

Phrase client de depart: "Bonjour, je voudrais prendre rendez-vous pour une revision de ma Clio."

Informations a collecter:
- nom;
- telephone;
- marque, modele, immatriculation si possible;
- disponibilites;
- accord sur un creneau.

Tools attendus:
- `check_availability`;
- `create_appointment`;
- `create_call_record`;
- `send_confirmation_sms` si confirmation.

Resultat attendu: rendez-vous mock confirme uniquement apres `check_availability`.

Criteres de reussite:
- pas de disponibilite inventee;
- une seule question a la fois;
- recapitulatif final court.
