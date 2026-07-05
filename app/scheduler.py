"""Moteur PROACTIF : le coach écrit en premier (rappels avant séance, débriefs après).

Un "tick" périodique scanne les séances prévues :
- séance qui approche + pas encore rappelée  -> RAPPEL (va à ta séance + quoi faire)
- séance passée + pas encore débriefée        -> DÉBRIEF (alors ? + c'est quand la prochaine ?)

⚠️ WhatsApp : passé 24h sans message de l'utilisateur, un envoi proactif exige un
TEMPLATE approuvé par Meta (prod). En Sandbox, ça marche seulement dans la fenêtre
24h. Un envoi refusé n'est PAS marqué comme envoyé -> il sera retenté au tick suivant
(tant que la fenêtre de rappel/débrief est ouverte).
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .config import settings
from .db import (
    due_debriefs,
    due_reminders,
    fmt_local,
    get_or_create_user,
    mark_debrief_sent,
    mark_reminder_sent,
    now_local,
)
from .whatsapp import send_whatsapp

log = logging.getLogger("coach.scheduler")

scheduler = BackgroundScheduler(timezone=settings.timezone)


def tick() -> None:
    """Scanne les séances prévues et envoie rappels + débriefs dus."""
    # Import local pour éviter tout cycle d'import au chargement.
    from .coach import generate_proactive

    now_iso = fmt_local(now_local())

    for r in due_reminders(now_iso):
        try:
            user = get_or_create_user(r["wa_id"])
            msg = generate_proactive(user, "reminder")
            if send_whatsapp(r["wa_id"], msg):
                mark_reminder_sent(r["id"])
                log.info("Rappel envoyé à %s (séance %s)", r["wa_id"], r["scheduled_at"])
        except Exception:  # noqa: BLE001
            log.exception("Erreur rappel pour %s", r["wa_id"])

    for r in due_debriefs(now_iso):
        try:
            user = get_or_create_user(r["wa_id"])
            msg = generate_proactive(user, "debrief")
            if send_whatsapp(r["wa_id"], msg):
                mark_debrief_sent(r["id"])
                log.info("Débrief envoyé à %s (séance %s)", r["wa_id"], r["scheduled_at"])
        except Exception:  # noqa: BLE001
            log.exception("Erreur débrief pour %s", r["wa_id"])


def start() -> None:
    scheduler.start()
    if settings.proactive_enabled:
        scheduler.add_job(tick, "interval", minutes=5, id="proactive_tick")
        log.info("Moteur proactif ACTIF (tick toutes les 5 min).")
    else:
        log.info("Moteur proactif désactivé (proactive_enabled=false).")
