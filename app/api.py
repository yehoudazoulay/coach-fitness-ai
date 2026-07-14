"""API REST consommée par l'app mobile (chat + lecture des tables).

Canal-agnostique : mêmes cerveau et données que WhatsApp. Un utilisateur d'app est
identifié par une clé (ex. 'app:<id>'). Pas d'auth pour le proto — à ajouter avant
de vrais users.
"""

import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from . import clock
from .config import settings
from .db import (
    EDITABLE_KINDS,
    active_events,
    add_event,
    create_item,
    current_program,
    delete_event,
    delete_item,
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
    recent_workouts,
    save_new_program,
    sessions_this_week,
    update_event,
    update_item,
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


def _check_kind(kind: str) -> None:
    if kind not in EDITABLE_KINDS:
        raise HTTPException(404, f"type éditable inconnu: {kind}")


@router.post("/{user}/items/{kind}")
def create_entry(user: str, kind: str, fields: dict = Body(...)) -> dict:
    """Crée une entrée de suivi à la main (objectif, mesure, séance, jalon, event…)."""
    _check_kind(kind)
    u = get_or_create_user(user)
    try:
        if kind == "event":
            new_id = add_event(u["id"], fields.get("kind", "perso"),
                               fields.get("content", ""), fields.get("subject"),
                               fields.get("status", "actif"))
        else:
            new_id = create_item(u["id"], kind, fields)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": new_id}


@router.patch("/{user}/items/{kind}/{item_id}")
def update_entry(user: str, kind: str, item_id: int, fields: dict = Body(...)) -> dict:
    """Corrige une entrée de suivi existante."""
    _check_kind(kind)
    u = get_or_create_user(user)
    if kind == "event":
        update_event(u["id"], item_id, fields.get("status", "actif"),
                     fields.get("content"))
        ok = True
    else:
        ok = update_item(u["id"], kind, item_id, fields)
    return {"ok": ok}


@router.delete("/{user}/items/{kind}/{item_id}")
def delete_entry(user: str, kind: str, item_id: int) -> dict:
    """Supprime une entrée de suivi."""
    _check_kind(kind)
    u = get_or_create_user(user)
    ok = delete_event(u["id"], item_id) if kind == "event" \
        else delete_item(u["id"], kind, item_id)
    return {"ok": ok}


@router.post("/{user}/program")
def save_program(user: str, payload: dict = Body(...)) -> dict:
    """Enregistre le programme édité à la main (nouvelle version SCD2)."""
    u = get_or_create_user(user)
    prog = {
        "name": (payload.get("name") or "Programme").strip(),
        "frequence": payload.get("frequence"),
        "seances": payload.get("seances") or [],
    }
    save_new_program(u["id"], json.dumps(prog, ensure_ascii=False),
                     reason="édité dans l'app")
    return {"ok": True, "programme": prog}


@router.get("/{user}/workouts")
def workouts(user: str, limit: int = 30) -> dict:
    """Suivi des séances (pour le chart) : date/heure, faite ou non, intensité, ressenti.
    Renvoyé du plus ANCIEN au plus récent (ordre chronologique pour le graphique)."""
    u = get_or_create_user(user)
    rows = recent_workouts(u["id"], limit)
    seances = [
        {
            "id": r["id"],
            "performed_at": r["performed_at"],
            "session_name": r["session_name"],
            "feeling": r["feeling"],
            "intensity": r["intensity"],
            "done": bool(r["done"]),
        }
        for r in reversed(rows)  # chronologique
    ]
    return {"seances": seances}


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
        jalons.append({"id": m["id"], "label": m["label"],
                       "target_date": m["target_date"], "jours": j})

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
