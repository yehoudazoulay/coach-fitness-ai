"""Point d'entrée FastAPI : reçoit les messages WhatsApp et orchestre le coach.

Flux d'un message entrant :
    Twilio --(webhook POST)--> /webhook
        1. on identifie / crée l'utilisateur (par son numéro WhatsApp)
        2. on persiste son message
        3. on répond 200 IMMÉDIATEMENT (Twilio coupe au bout de ~15s)
        4. en tâche de fond : Claude génère la réponse -> on l'envoie via Twilio
"""

import logging

from fastapi import BackgroundTasks, FastAPI, Form
from fastapi.responses import PlainTextResponse

from . import scheduler
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
    init_db,
    save_message,
    set_coach,
    set_state,
)
from .whatsapp import send_whatsapp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("coach.main")

app = FastAPI(title="Coach Fitness WhatsApp")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    scheduler.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _process_message(wa_id: str, body: str) -> None:
    """Traitement lourd (appel Claude + envoi), exécuté en tâche de fond."""
    user = get_or_create_user(wa_id)
    save_message(user["id"], "user", body)
    history = get_history(user["id"])

    try:
        reply = generate_reply(user, history)  # mise en place (le coach mène) / actif
    except Exception:  # noqa: BLE001
        log.exception("Erreur de génération pour %s", wa_id)
        reply = "Bug de mon côté, 2 secondes. Réessaie."

    save_message(user["id"], "assistant", reply)
    send_whatsapp(wa_id, reply)

    # Mémoire : on route les infos du message vers goals/facts/events/mesures.
    try:
        changes = update_memory(user["id"], history)
        if changes:
            log.info("Mémoire mise à jour pour %s : %s", wa_id, changes)
    except Exception:  # noqa: BLE001
        log.exception("Mise à jour mémoire KO pour %s", wa_id)

    # Sortie de la mise en place : dès qu'un programme CONCRET est proposé ET
    # accepté, on le fige (SCD2) et on passe en coaching quotidien.
    if user["state"] != STATE_ACTIVE:
        full = get_history(user["id"])  # inclut la dernière réponse du coach
        try:
            if program_validated(full) and finalize_program(user["id"], full):
                set_coach(user["id"], DEFAULT_COACH_ID)
                set_state(user["id"], STATE_ACTIVE)
                log.info("Programme validé et enregistré pour %s -> actif", wa_id)
        except Exception:  # noqa: BLE001
            log.exception("Finalisation programme KO pour %s", wa_id)


@app.post("/webhook")
async def webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),  # ex: "whatsapp:+33612345678"
    Body: str = Form(""),
) -> PlainTextResponse:
    background_tasks.add_task(_process_message, From, Body)
    # Réponse vide : on a déjà accusé réception, on enverra la réponse via REST.
    return PlainTextResponse("", status_code=200)
