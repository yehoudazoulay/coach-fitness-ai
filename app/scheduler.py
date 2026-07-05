"""Moteur PROACTIF : le coach écrit en premier.

Un "tick" périodique déclenche :
- RAPPEL avant une séance prévue + DÉBRIEF après (via planned_sessions).
- Relances conditionnelles (1 max par utilisateur par tick, avec cooldown) :
  · prise de NEWS sur un event santé/blessure/moral ("ça va mieux le genou ?")
  · relance d'INACTIVITÉ ("t'as fait combien de séances ?")
  · compte à rebours d'un JALON ("plus que N semaines avant le mariage")

⚠️ WhatsApp : envoi proactif hors fenêtre 24h = template Meta (prod). En Sandbox,
seulement dans la fenêtre 24h. ⚠️ Render free : le scheduler ne tourne que quand le
service est éveillé (veille après 15 min) -> proactif fiable = always-on.
"""

import logging
from datetime import date, datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from . import clock
from .config import settings
from .db import (
    active_events,
    active_users,
    due_debriefs,
    due_reminders,
    fmt_local,
    get_or_create_user,
    last_workout,
    log_proactive,
    mark_debrief_sent,
    mark_reminder_sent,
    now_local,
    recently_sent,
    save_message,
    upcoming_milestones,
)
from .whatsapp import send_whatsapp

log = logging.getLogger("coach.scheduler")

scheduler = BackgroundScheduler(timezone=settings.timezone)

_UNRESOLVED = {"actif", "amélioration", "amelioration", "rémission", "remission",
               "aggravation"}


def _days_since(iso: str) -> int:
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (clock.now_utc() - dt).days
    except Exception:  # noqa: BLE001
        return 0


def _deliver(user, msg: str) -> bool:
    """Livre un message proactif : (1) on l'ENREGISTRE en base comme message du
    coach — c'est ce qui le fait apparaître dans l'app (via son poll) ; (2) on
    l'envoie sur WhatsApp seulement si l'utilisateur est un contact WhatsApp."""
    save_message(user["id"], "assistant", msg)
    if str(user["wa_id"]).startswith("whatsapp:"):
        return send_whatsapp(user["wa_id"], msg)
    return True  # utilisateur app : le message est en base, le poll le récupérera


def _send_nudge(user, kind: str, ref: str = "", detail: str | None = None) -> None:
    """Génère + envoie une relance, et la journalise (même si l'envoi échoue, pour
    ne pas régénérer en boucle tant que le cooldown n'est pas écoulé)."""
    from .coach import generate_proactive
    try:
        msg = generate_proactive(user, kind, detail)
        sent = _deliver(user, msg)
        log_proactive(user["id"], kind, ref)
        log.info("Relance '%s' %s pour %s", kind,
                 "envoyée" if sent else "générée (envoi refusé)", user["wa_id"])
    except Exception:  # noqa: BLE001
        log.exception("Erreur relance '%s' pour %s", kind, user["wa_id"])


def _condition_nudge(user) -> None:
    """Une relance conditionnelle max par utilisateur (par priorité + cooldown)."""
    uid = user["id"]

    # 1. Prise de news sur un event santé/blessure/moral non résolu, âgé de >= 2 jours.
    for e in active_events(uid):
        if e["kind"] in ("sante", "blessure", "moral", "perso") \
                and e["status"] in _UNRESOLVED and _days_since(e["created_at"]) >= 2:
            if not recently_sent(uid, "event_news", str(e["event_key"]), 72):
                _send_nudge(user, "event_news", str(e["event_key"]), e["content"])
                return

    # 2. Inactivité : aucune séance ou dernière séance il y a >= 4 jours.
    lw = last_workout(uid)
    if (lw is None or _days_since(lw["performed_at"]) >= 4) \
            and not recently_sent(uid, "inactivity", "", 48):
        _send_nudge(user, "inactivity")
        return

    # 3. Compte à rebours d'un jalon proche (<= 90 jours), 1x/semaine.
    ms = upcoming_milestones(uid)
    if ms:
        m = ms[0]
        try:
            days = (date.fromisoformat(m["target_date"]) - now_local().date()).days
        except Exception:  # noqa: BLE001
            days = -1
        if 0 <= days <= 90 and not recently_sent(uid, "milestone", m["label"], 168):
            _send_nudge(user, "milestone", m["label"],
                        f"{m['label']} le {m['target_date']}")
            return


def tick() -> None:
    now_iso = fmt_local(now_local())

    # Rappels + débriefs (basés sur les séances prévues).
    for r in due_reminders(now_iso):
        try:
            from .coach import generate_proactive
            user = get_or_create_user(r["wa_id"])
            if _deliver(user, generate_proactive(user, "reminder")):
                mark_reminder_sent(r["id"])
                log.info("Rappel envoyé à %s (séance %s)", r["wa_id"], r["scheduled_at"])
        except Exception:  # noqa: BLE001
            log.exception("Erreur rappel pour %s", r["wa_id"])

    for r in due_debriefs(now_iso):
        try:
            from .coach import generate_proactive
            user = get_or_create_user(r["wa_id"])
            if _deliver(user, generate_proactive(user, "debrief")):
                mark_debrief_sent(r["id"])
                log.info("Débrief envoyé à %s (séance %s)", r["wa_id"], r["scheduled_at"])
        except Exception:  # noqa: BLE001
            log.exception("Erreur débrief pour %s", r["wa_id"])

    # Relances conditionnelles (news / inactivité / jalon).
    for user in active_users():
        try:
            _condition_nudge(user)
        except Exception:  # noqa: BLE001
            log.exception("Erreur relance conditionnelle pour %s", user["wa_id"])


def set_tick_seconds(seconds: int) -> None:
    """Change la cadence du scheduler à chaud (rapide en accéléré, lente en normal)."""
    secs = max(5, int(seconds))
    try:
        scheduler.reschedule_job("proactive_tick", trigger="interval", seconds=secs)
        log.info("Cadence scheduler -> %ss.", secs)
    except Exception:  # noqa: BLE001
        log.exception("Impossible de re-planifier le tick")


def start() -> None:
    scheduler.start()
    if settings.proactive_enabled:
        secs = max(5, settings.tick_seconds)
        scheduler.add_job(tick, "interval", seconds=secs, id="proactive_tick")
        extra = f" — temps ACCÉLÉRÉ x{clock.get_factor():g}" \
            if clock.get_factor() != 1.0 else ""
        log.info("Moteur proactif ACTIF (tick toutes les %ss)%s.", secs, extra)
    else:
        log.info("Moteur proactif désactivé (proactive_enabled=false).")
