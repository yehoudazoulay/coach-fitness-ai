"""Cœur d'un tour de conversation, INDÉPENDANT du canal (WhatsApp OU app).

`run_turn` fait tout le travail (générer la réponse, mettre à jour la mémoire,
gérer la mise en place du programme) et RENVOIE la réponse du coach. À charge de
l'appelant de l'acheminer : WhatsApp l'envoie via Twilio, l'API la renvoie en JSON.
"""

import logging

from .coach import (
    finalize_program,
    generate_reply,
    program_validated,
    update_memory,
)
from .coaches import DEFAULT_COACH_ID
from .db import (
    STATE_ACTIVE,
    get_history,
    get_or_create_user,
    save_message,
    set_coach,
    set_state,
)

log = logging.getLogger("coach.flow")


def run_turn(user_key: str, body: str) -> str:
    """Traite un message entrant et renvoie la réponse du coach.

    `user_key` identifie l'utilisateur : 'whatsapp:+33...' pour WhatsApp, ou par ex.
    'app:<id>' pour l'app. Le reste du code s'en fiche : tout est keyé par cet id.
    """
    user = get_or_create_user(user_key)
    save_message(user["id"], "user", body)
    history = get_history(user["id"])

    try:
        reply = generate_reply(user, history)
    except Exception:  # noqa: BLE001
        log.exception("Erreur de génération pour %s", user_key)
        reply = "Bug de mon côté, 2 secondes. Réessaie."

    save_message(user["id"], "assistant", reply)

    # Mémoire : route les infos du message (goals/facts/events/mesures/workouts...).
    try:
        changes = update_memory(user["id"], history)
        if changes:
            log.info("Mémoire mise à jour pour %s : %s", user_key, changes)
    except Exception:  # noqa: BLE001
        log.exception("Mise à jour mémoire KO pour %s", user_key)

    # Sortie de la mise en place : programme concret proposé ET accepté -> actif.
    if user["state"] != STATE_ACTIVE:
        full = get_history(user["id"])
        try:
            if program_validated(full) and finalize_program(user["id"], full):
                set_coach(user["id"], DEFAULT_COACH_ID)
                set_state(user["id"], STATE_ACTIVE)
                log.info("Programme validé pour %s -> actif", user_key)
        except Exception:  # noqa: BLE001
            log.exception("Finalisation programme KO pour %s", user_key)

    return reply
