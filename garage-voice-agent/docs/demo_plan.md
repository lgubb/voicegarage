# Plan de demo commerciale

## Script video

1. Montrer le terminal avec l'agent LiveKit lance.
2. Ouvrir l'Agent Console ou une room de test.
3. Jouer quatre appels courts.
4. Montrer pour chaque appel les logs de tools et la fiche appel structuree.
5. Expliquer que les calendriers, SMS, emails et handoff sont mockes pour la demo.

## Appels a enregistrer

1. Revision: prise d'informations, disponibilites, proposition de creneaux, confirmation mock.
2. Pneus: demande de changement, collecte vehicule, refus d'inventer un prix exact.
3. Carrosserie: accrochage, collecte contexte, fiche pour rappel/devis.
4. Panne urgente: situation dangereuse, pas de diagnostic, handoff/rappel prioritaire.

## A montrer a l'ecran

- Conversation LiveKit en temps reel.
- Logs `check_availability`, `create_appointment`, `classify_urgency`, `transfer_to_human`.
- JSON final `CallSummary`.
- Fiche lisible: client, vehicule, motif, urgence, prochaine action.

## Positionnement demo

Dire clairement: "Ce n'est pas encore branche a votre agenda ni a votre ligne. Les actions externes sont simulees. L'objectif est de montrer le comportement vocal, la collecte d'informations et la fiche appel que le garage recupere."

## Email garages

Objet : Demo de l'assistant telephonique pour votre garage

Bonjour {{Prenom}},

Comme convenu, je vous envoie une courte demo d'un assistant telephonique IA pense pour les garages et carrosseries.

L'idee est simple : quand vous etes deja au telephone, en intervention ou indisponible, l'assistant repond, comprend la demande du client, recupere les informations utiles, puis vous transmet une fiche claire.

Dans la demo, je montre plusieurs cas :
- prise de rendez-vous pour revision ;
- demande pneus ;
- demande carrosserie ;
- panne urgente avec demande de rappel prioritaire.

Lien de la demo : {{lien}}

Ce n'est pas encore une version definitive branchee a votre garage, mais ca montre concretement ce que l'agent pourrait faire avec vos horaires, vos services et vos regles de prise de rendez-vous.

Bonne journee,

Louis
