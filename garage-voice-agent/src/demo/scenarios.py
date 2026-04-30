DEMO_SCENARIOS = {
    "revision": {
        "first_utterance": "Bonjour, je voudrais prendre rendez-vous pour une revision.",
        "expected_tools": ["check_availability", "create_appointment", "create_call_record"],
        "success": "Un creneau mock est propose puis une fiche appel est creee.",
    },
    "pneus": {
        "first_utterance": "Bonjour, je dois changer deux pneus avant.",
        "expected_tools": ["check_availability", "create_call_record"],
        "success": "L'agent collecte dimensions si possible et propose une suite sans inventer de prix.",
    },
    "carrosserie": {
        "first_utterance": "J'ai eu un accrochage et mon pare-choc est abime.",
        "expected_tools": ["classify_urgency", "create_call_record"],
        "success": "L'agent qualifie l'accrochage et demande photos ou rappel.",
    },
    "panne_urgente": {
        "first_utterance": "Je suis sur l'autoroute, il y a de la fumee et la voiture ne repond plus.",
        "expected_tools": ["classify_urgency", "transfer_to_human", "create_call_record"],
        "success": "L'agent escalade sans diagnostic et recommande de se mettre en securite.",
    },
}
