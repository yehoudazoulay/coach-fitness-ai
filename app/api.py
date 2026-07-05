"""API REST consommée par l'app mobile (chat + lecture des tables).

Canal-agnostique : mêmes cerveau et données que WhatsApp. Un utilisateur d'app est
identifié par une clé (ex. 'app:<id>'). Pas d'auth pour le proto — à ajouter avant
de vrais users.
"""

import json
from datetime import date, datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from . import clock
from .config import settings
from .db import (
    active_events,
    current_program,
    fmt_local,
    get_facts,
    get_goals,
    get_history,
    get_or_create_user,
    last_workout,
    latest_measurements,
    measurement_history,
    next_planned_session,
    now_local,
    sessions_this_week,
    upcoming_milestones,
)
from .flow import run_turn

router = APIRouter(prefix="/api")


class ChatIn(BaseModel):
    user: str  # identifiant utilisateur, ex. "app:yehouda"
    message: str


@router.get("/clock")
def clock_now() -> dict:
    """Heure courante du backend (virtuelle si le temps est accéléré) + facteur.
    Sert à afficher la date/heure qui défile en haut de l'app en mode test."""
    factor = clock.get_factor()
    return {
        "now": now_local().replace(microsecond=0).isoformat(),
        "factor": factor,
        "accelerated": factor != 1.0,
    }


class ClockMode(BaseModel):
    accelerated: bool


@router.post("/clock/mode")
def set_clock_mode(payload: ClockMode) -> dict:
    """Bascule le temps entre accéléré et normal, à chaud (bouton dans l'app).
    Ajuste aussi la cadence du scheduler pour ne pas rater les fenêtres de rappel."""
    from .scheduler import set_tick_seconds
    if payload.accelerated:
        clock.set_factor(settings.accel_factor)
        set_tick_seconds(settings.accel_tick_seconds)
    else:
        clock.set_factor(1.0)
        set_tick_seconds(settings.tick_seconds)
    factor = clock.get_factor()
    return {"accelerated": factor != 1.0, "factor": factor,
            "now": now_local().replace(microsecond=0).isoformat()}


@router.post("/chat")
def chat(payload: ChatIn) -> dict:
    """Envoie un message au coach et renvoie sa réponse (synchrone)."""
    reply = run_turn(payload.user, payload.message)
    return {"reply": reply}


@router.get("/{user}/messages")
def messages(user: str, limit: int = 50) -> dict:
    """Historique de la conversation."""
    u = get_or_create_user(user)
    return {"messages": [dict(m) for m in _history_rows(u["id"], limit)]}


def _history_rows(user_id: int, limit: int):
    # get_history renvoie [{role, content}] ; on veut aussi les dates -> requête directe.
    from .db import get_conn
    with get_conn() as conn:
        return conn.execute(
            "SELECT role, content, created_at FROM messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()[::-1]


@router.get("/{user}/dashboard")
def dashboard(user: str) -> dict:
    """Vue d'ensemble pour l'app : profil, adhérence, programme, mesures, jalons…"""
    u = get_or_create_user(user)
    uid = u["id"]

    goals = [dict(g) for g in get_goals(uid)]
    facts = [dict(f) for f in get_facts(uid)]
    events = [dict(e) for e in active_events(uid)]
    mesures = [dict(m) for m in latest_measurements(uid)]

    # Programme (JSON parsé si possible).
    prog_row = current_program(uid)
    programme = None
    freq = None
    if prog_row is not None:
        try:
            programme = json.loads(prog_row["content"])
            freq = programme.get("frequence")
        except Exception:  # noqa: BLE001
            programme = {"raw": prog_row["content"]}

    # Adhérence.
    lw = last_workout(uid)
    jours_depuis = None
    if lw is not None:
        try:
            jours_depuis = (clock.now_utc()
                            - datetime.fromisoformat(lw["performed_at"])).days
        except Exception:  # noqa: BLE001
            jours_depuis = None

    # Prochaine séance prévue.
    nps = next_planned_session(uid)

    # Jalons (avec compte à rebours).
    today = now_local().date()
    jalons = []
    for m in upcoming_milestones(uid):
        try:
            j = (date.fromisoformat(m["target_date"]) - today).days
        except Exception:  # noqa: BLE001
            j = None
        jalons.append({"label": m["label"], "target_date": m["target_date"], "jours": j})

    # Progression du poids (série).
    poids = [
        {"value": h["value"], "unit": h["unit"], "date": h["measured_at"][:10]}
        for h in measurement_history(uid, "poids")
    ]

    return {
        "state": u["state"],
        "coach_id": u["coach_id"],
        "goals": goals,
        "facts": facts,
        "events": events,
        "mesures": mesures,
        "programme": programme,
        "adherence": {
            "seances_cette_semaine": sessions_this_week(uid),
            "objectif_semaine": freq,
            "jours_depuis_derniere": jours_depuis,
            "derniere_seance": dict(lw) if lw else None,
        },
        "prochaine_seance": dict(nps) if nps else None,
        "jalons": jalons,
        "progression_poids": poids,
    }
