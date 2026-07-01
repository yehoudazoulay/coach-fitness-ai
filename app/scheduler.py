"""Relances PROACTIVES du coach (check-ins) — squelette.

⚠️ Rappel WhatsApp : passé 24h sans message de l'utilisateur, un envoi proactif
exige un TEMPLATE pré-approuvé par Meta (en production). En Sandbox Twilio c'est
permissif. Cette brique est donc volontairement minimale pour le proto.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .db import STATE_ACTIVE, get_conn
from .whatsapp import send_whatsapp

log = logging.getLogger("coach.scheduler")

scheduler = BackgroundScheduler(timezone="Europe/Paris")


def daily_checkins() -> None:
    """Exemple : pinger chaque utilisateur actif une fois par jour.

    TODO (proto) : ne relancer que les inactifs, varier le message via le coach,
    et passer par des templates approuvés en production.
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT wa_id FROM users WHERE state = ?", (STATE_ACTIVE,)
        ).fetchall()
    for r in rows:
        try:
            send_whatsapp(r["wa_id"], "Hello 👋 Comment s'est passée ta journée ?")
        except Exception:  # noqa: BLE001 — un échec d'envoi ne doit pas tout casser
            log.exception("Échec du check-in pour %s", r["wa_id"])


def start() -> None:
    # Tous les jours à 18h. Décommente quand tu veux activer les relances.
    # scheduler.add_job(daily_checkins, "cron", hour=18, minute=0)
    scheduler.start()
    log.info("Scheduler démarré (relances proactives désactivées par défaut).")
