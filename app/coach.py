"""Le CERVEAU : construction du system prompt + appels à l'API OpenAI.

Mono-coach (pour l'instant) : LE MILITAIRE fait tout.
- DÉCOUVERTE (state=onboarding) : il mène lui-même un entretien court et cash.
- ACTIF (state=active) : il coache au quotidien, même voix.
Pas de Head Coach ni de matching tant qu'on n'a qu'un seul coach.

NB : OpenAI applique un prompt caching AUTOMATIQUE (> ~1024 tokens), rien à coder.
"""

import json
import sqlite3
from datetime import date, datetime, timezone

from openai import OpenAI

from .coaches import COMMON_RULES, coach_persona, discovery_instructions
from .config import settings
from .db import (
    STATE_ACTIVE,
    active_events,
    add_event,
    add_fact,
    add_goal,
    add_measurement,
    add_milestone,
    add_planned_session,
    current_program,
    fmt_local,
    get_facts,
    get_goals,
    get_milestones,
    last_workout,
    latest_measurements,
    log_workout,
    measurement_history,
    next_planned_session,
    now_local,
    save_new_program,
    sessions_this_week,
    update_event,
    update_fact,
    update_goal,
    upcoming_milestones,
)
from .programs_lib import program_instructions

_client = OpenAI(api_key=settings.openai_api_key)


_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
         "septembre", "octobre", "novembre", "décembre"]


def _today_str() -> str:
    now = datetime.now()
    return (f"{_JOURS[now.weekday()]} {now.day} {_MOIS[now.month - 1]} "
            f"{now.year}, {now:%H:%M}")


def _dynamic_context(user: sqlite3.Row) -> str:
    """Contexte qui change au fil du temps : date, poids, mémoire (events), programme."""
    parts = [
        f"DATE ET HEURE ACTUELLES : {_today_str()}. Tiens-en TOUJOURS compte pour "
        "toute notion de temps (depuis quand, quel jour, prochaine séance...).",
        f"CONTEXTE CLIENT — état : {user['state']}.",
    ]

    # Objectifs & motivations : le cœur -> rappelle-les, appuie-toi sur le POURQUOI.
    goals = get_goals(user["id"])
    if goals:
        objs = [g["content"] for g in goals if g["type"] == "objectif"]
        mots = [g["content"] for g in goals if g["type"] == "motivation"]
        block = ["SON OBJECTIF ET SON POURQUOI (le cœur — rappelle-les, appuie-toi "
                 "dessus dans les moments durs) :"]
        if objs:
            block.append("Objectif(s) : " + " ; ".join(objs))
        if mots:
            block.append("Motivation(s) / déclencheur : " + " ; ".join(mots))
        parts.append("\n".join(block))

    ms = latest_measurements(user["id"])
    if ms:
        line = ", ".join(
            f"{m['metric']} {m['value']}{m['unit'] or ''} (le {m['measured_at'][:10]})"
            for m in ms
        )
        parts.append("SES DERNIÈRES MESURES : " + line + ".")

    # Mémoire : ce que tu sais de sa vie (version courante + statut) -> tu t'en
    # souviens, tu reviens dessus, tu prends des news quand c'est pertinent.
    events = active_events(user["id"], 10)
    if events:
        lines = "\n".join(
            f"- ({e['created_at'][:10]}) [{e['kind']}] {e['content']} "
            f"— statut : {e['status']}"
            for e in events
        )
        parts.append(
            "CE QUE TU SAIS DE SA VIE (souviens-t'en, reviens dessus, prends des "
            "news quand c'est pertinent ; tiens compte du statut) :\n" + lines
        )

    # Faits stables : son quotidien (boulot, dispos, contraintes) -> planification.
    facts = get_facts(user["id"])
    if facts:
        lines = "\n".join(f"- [{f['category']}] {f['content']}" for f in facts)
        parts.append(
            "SON QUOTIDIEN (routine, boulot, dispos, contraintes — utilise-le pour "
            "proposer/adapter les séances et rester pertinent) :\n" + lines
        )

    # Programme en cours (source des rappels de séance).
    prog = current_program(user["id"])
    if prog is not None:
        parts.append(f"SON PROGRAMME ACTUEL (v{prog['version']}) : {prog['content']}")

    # Suivi / adhérence : séances de la semaine vs objectif + dernière séance.
    suivi = []
    n = sessions_this_week(user["id"])
    freq = None
    if prog is not None:
        try:
            freq = json.loads(prog["content"]).get("frequence")
        except Exception:  # noqa: BLE001
            freq = None
    if n or freq:
        s = f"Séances faites cette semaine : {n}"
        if freq:
            s += f" (objectif : {freq}/semaine)"
        suivi.append(s + ".")
    lw = last_workout(user["id"])
    if lw is not None:
        try:
            days = (datetime.now(timezone.utc)
                    - datetime.fromisoformat(lw["performed_at"])).days
            desc = f" ({lw['session_name']})" if lw["session_name"] else ""
            suivi.append(f"Dernière séance{desc} : il y a {days} jour(s).")
        except Exception:  # noqa: BLE001
            pass
    if suivi:
        parts.append("SUIVI / ASSIDUITÉ (débriefe, félicite ou secoue selon) :\n"
                     + "\n".join("- " + x for x in suivi))

    # Prochaine séance prévue (base des rappels) — sinon, demande-la.
    if user["state"] == STATE_ACTIVE:
        nps = next_planned_session(user["id"])
        if nps is not None:
            quand = nps["scheduled_at"].replace("T", " à ")
            quoi = f" ({nps['session_name']})" if nps["session_name"] else ""
            parts.append(f"PROCHAINE SÉANCE PRÉVUE : {quand}{quoi}.")
        else:
            parts.append("PAS DE PROCHAINE SÉANCE PRÉVUE : demande-lui, de toi-même, "
                         "c'est quand sa prochaine séance, pour pouvoir la lui rappeler.")

    # Jalons à venir (compte à rebours).
    ms = upcoming_milestones(user["id"])
    if ms:
        today = datetime.now(timezone.utc).date()
        lines = []
        for m in ms:
            try:
                days = (date.fromisoformat(m["target_date"]) - today).days
                lines.append(f"{m['label']} : dans {days} jour(s) ({m['target_date']})")
            except Exception:  # noqa: BLE001
                lines.append(f"{m['label']} ({m['target_date']})")
        parts.append("JALON(S) À VENIR (fais le compte à rebours quand c'est "
                     "pertinent) :\n" + "\n".join("- " + x for x in lines))

    # Progression poids (si ≥ 2 mesures).
    hist = measurement_history(user["id"], "poids")
    if len(hist) >= 2:
        f0, fn = hist[0], hist[-1]
        parts.append(
            f"PROGRESSION POIDS : {f0['value']}{f0['unit'] or ''} "
            f"({f0['measured_at'][:10]}) -> {fn['value']}{fn['unit'] or ''} "
            f"({fn['measured_at'][:10]})."
        )

    return "\n".join(parts)


def _build_system(user: sqlite3.Row) -> str:
    """System prompt : persona du coach (+ consignes découverte si onboarding)."""
    parts = [COMMON_RULES, coach_persona(user["coach_id"])]
    if user["state"] != STATE_ACTIVE:
        # Phase de MISE EN PLACE : une seule conversation fluide, le coach mène.
        parts.append(
            "PHASE DE MISE EN PLACE (avant le coaching quotidien) — tu MÈNES, en "
            "deux temps, dans la MÊME conversation, sans rupture brutale :\n"
            "1) D'ABORD tu fais connaissance et tu récoltes les infos (voir "
            "DÉCOUVERTE ci-dessous), UNE question à la fois, dans ta voix. Ne "
            "propose PAS de programme tant que tu n'as pas l'essentiel : objectif, "
            "niveau, dispo (nb séances + durée + jours ou 'au feeling'), TAILLE et "
            "POIDS, blessures.\n"
            "2) DÈS que tu as tout ça, tu ENCHAÎNES toi-même sur le programme (voir "
            "PROGRAMME ci-dessous) : tu annonces qu'on passe aux choses sérieuses, "
            "tu proposes un programme CONCRET et clair (ou pars du sien), tu "
            "l'ajustes avec lui, et tu attends qu'il valide avant de conclure."
        )
        parts.append(discovery_instructions(user["coach_id"]))
        parts.append(program_instructions())
    parts.append(_dynamic_context(user))
    return "\n\n".join(parts)


def generate_reply(user: sqlite3.Row, history: list[dict]) -> str:
    """Réponse du coach. `history` inclut déjà le dernier message de l'utilisateur."""
    messages = [{"role": "system", "content": _build_system(user)}, *history]
    response = _client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=400,  # messages WhatsApp courts et qui claquent
        messages=messages,
    )
    return (response.choices[0].message.content or "").strip()


def generate_proactive(user: sqlite3.Row, kind: str) -> str:
    """Génère un message PROACTIF (le coach écrit en PREMIER) dans sa voix.

    kind = 'reminder' (juste avant la séance) | 'debrief' (juste après)."""
    if kind == "reminder":
        instr = (
            "TU ÉCRIS EN PREMIER — RAPPEL DE SÉANCE. La personne ne t'a rien demandé, "
            "c'est toi qui l'interpelles : sa prochaine séance approche. Rappelle-lui "
            "d'y aller, cash et motivant, dans TA voix, et rappelle brièvement ce "
            "qu'elle est censée faire (cf. son programme). Court et qui claque."
        )
    else:  # debrief
        instr = (
            "TU ÉCRIS EN PREMIER — DÉBRIEF POST-SÉANCE. Sa séance vient de passer : "
            "demande, dans TA voix, comment ça s'est passé (si elle l'a faite ou pas), "
            "puis ENCHAÎNE en lui demandant c'est quand sa PROCHAINE séance. Court."
        )
    system = "\n\n".join(
        [COMMON_RULES, coach_persona(user["coach_id"]), instr, _dynamic_context(user)]
    )
    response = _client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=300,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": "[Déclencheur automatique : écris ton message.]"},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def onboarding_done(history: list[dict]) -> bool:
    """Décide si la découverte est bouclée (objectif + fréquence + pourquoi il a
    lâché avant). Appel JSON léger et séparé. En cas de pépin -> on continue."""
    system = (
        "Tu analyses un échange entre un coach fitness et un nouveau client. "
        "La phase de découverte est-elle terminée ? Réponds done=true SEULEMENT si "
        "TOUTES ces infos ont été ABORDÉES dans la conversation :\n"
        "1) l'objectif ; 2) le niveau/expérience ; 3) la dispo d'entraînement "
        "(nombre de séances/semaine + durée + jours OU 'au feeling') ; 4) la "
        "TAILLE et le POIDS de départ ; 5) les blessures/pépins éventuels.\n"
        "Pour (4) et (5), il SUFFIT que le coach ait posé la question (le client "
        "peut refuser ou ne pas savoir). S'il MANQUE ne serait-ce qu'une de ces "
        "cinq infos, ou qu'elle n'a pas encore été abordée, done=FALSE. "
        'Réponds UNIQUEMENT en JSON : {"done": true|false}.'
    )
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=10,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": convo},
            ],
        )
        return bool(json.loads(response.choices[0].message.content or "{}").get("done"))
    except Exception:  # noqa: BLE001
        return False


def update_memory(user_id: int, history: list[dict]) -> list[dict]:
    """Met à jour la mémoire à partir du DERNIER message, en routant :

    - EVENTS (épisodiques, avec statut) : nouveau, ou mise à jour de statut (SCD2).
    - FACTS (stables/récurrents : boulot, dispos, routine, contraintes) : nouveau
      ou mise à jour.
    Ignore le trivial. Renvoie la liste des changements (pour log)."""
    last_user = next(
        (m["content"] for m in reversed(history) if m["role"] == "user"), None
    )
    if not last_user:
        return []
    # On sépare CONTEXTE (à ne pas extraire, juste pour les références) et le
    # MESSAGE à traiter -> évite de re-logguer une séance/mesure déjà vue au tour d'avant.
    ctx_msgs = history[:-1][-4:] if history and history[-1]["content"] == last_user \
        else history[-4:]
    ctx = "\n".join(f'{m["role"]}: {m["content"]}' for m in ctx_msgs) or "(aucun)"
    user_content = (
        "CONTEXTE (pour comprendre les références — n'extrais RIEN d'ici) :\n" + ctx
        + "\n\nMESSAGE À TRAITER (extrais UNIQUEMENT ce que CE message apporte) :\n"
        + last_user
    )

    ev = active_events(user_id, 20)
    known_ev = "\n".join(
        f'- event_key={e["event_key"]} [{e["kind"]}] {e["content"]} '
        f'(statut : {e["status"]})'
        for e in ev
    ) or "(aucun)"
    fs = get_facts(user_id)
    known_fa = "\n".join(
        f'- fact_id={f["id"]} [{f["category"]}] {f["content"]}' for f in fs
    ) or "(aucun)"
    gs = get_goals(user_id)
    known_go = "\n".join(
        f'- goal_id={g["id"]} [{g["type"]}] {g["content"]}' for g in gs
    ) or "(aucun)"
    mi = get_milestones(user_id)
    known_mi = "\n".join(
        f'- {m["label"]} ({m["target_date"]})' for m in mi
    ) or "(aucun)"
    maintenant = fmt_local(now_local())

    system = (
        "Tu tiens à jour la mémoire d'un coach sur son client, depuis son DERNIER "
        f"message. Date et heure locales actuelles : {maintenant}. Tu ROUTES "
        "l'info entre ces catégories :\n\n"
        "GOALS = ce qu'il VEUT atteindre (type 'objectif') et POURQUOI, son "
        "déclencheur profond (type 'motivation'). C'est le cœur du coaching.\n"
        "EVENTS = épisodique, ça arrive puis ça passe, statut qui évolue (malade, "
        "blessure, vacances la semaine prochaine, coup dur, victoire, stress ponctuel).\n"
        "FACTS = stable/récurrent, son quotidien (horaires de boulot, sport le "
        "mercredi, amis le jeudi soir, sommeil, alimentation en gros, contraintes).\n"
        "MESURES = données chiffrées du corps qu'il RAPPORTE (poids, taille, taux "
        "de gras, tour de bras/taille/cuisse...). metric + valeur + unité.\n"
        "WORKOUTS = une SÉANCE qu'il dit avoir FAITE (pas prévue) : session_name (ce "
        "qu'il a fait), feeling (ressenti), notes.\n"
        "MILESTONES = une échéance DATÉE importante (mariage, compétition, deadline "
        "d'objectif). label + target_date au format AAAA-MM-JJ (résous les dates "
        "relatives/ambiguës avec la date du jour).\n"
        "NEXT_SESSION = la PROCHAINE séance qu'il PRÉVOIT de faire (future, pas encore "
        "faite) : scheduled_at à l'heure locale AAAA-MM-JJTHH:MM (résous 'demain 18h', "
        "'ce soir', 'jeudi', 'dans 2h' avec l'heure actuelle) + session_name (optionnel).\n"
        "Règles : ce qu'il veut/pourquoi -> goal ; début/fin/statut -> event ; "
        "permanent/récurrent -> fact ; chiffre du corps -> mesure ; séance FAITE -> "
        "workout ; séance PRÉVUE -> next_session ; échéance datée -> milestone.\n\n"
        "Pour chaque catégorie tu peux CRÉER ou METTRE À JOUR l'existant (ne "
        "duplique pas : si ça évolue, mets à jour via l'id). IGNORE le trivial.\n\n"
        "Objectifs/motivations connus :\n" + known_go + "\n\n"
        "Events actifs connus :\n" + known_ev + "\n\n"
        "Faits connus :\n" + known_fa + "\n\n"
        "Jalons connus :\n" + known_mi + "\n\n"
        "Réponds UNIQUEMENT en JSON :\n"
        '{"new_goals": [{"type": "objectif|motivation", "content": "phrase", '
        '"priority": 1}],\n'
        ' "goal_updates": [{"goal_id": <int>, "content": "phrase mise à jour"}],\n'
        ' "new_events": [{"kind": "...", "subject": "label", "content": "phrase", '
        '"status": "actif"}],\n'
        ' "event_updates": [{"event_key": <int>, "status": "résolu|amélioration|'
        'rémission|aggravation|terminé", "content": "(optionnel)"}],\n'
        ' "new_facts": [{"category": "boulot|routine|social|contrainte|preference|'
        'sante_fond", "content": "phrase"}],\n'
        ' "fact_updates": [{"fact_id": <int>, "content": "phrase mise à jour"}],\n'
        ' "new_measurements": [{"metric": "poids|taille|taux_gras|tour_bras|'
        'tour_taille|...", "value": <nombre>, "unit": "kg|cm|%"}],\n'
        ' "new_workouts": [{"session_name": "...", "feeling": "...", "notes": "..."}],\n'
        ' "new_milestones": [{"label": "...", "target_date": "AAAA-MM-JJ"}],\n'
        ' "next_session": {"scheduled_at": "AAAA-MM-JJTHH:MM", "session_name": "..."}}\n'
        "(next_session = null si aucune séance future n'est annoncée dans le message). "
        "Listes vides si rien. Le texte fourni contient les derniers échanges pour "
        "le CONTEXTE ; n'extrais que ce qu'apporte le TOUT DERNIER message de "
        "l'utilisateur."
    )
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=400,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception:  # noqa: BLE001
        return []

    changes = []
    for g in data.get("new_goals", []):
        content = (g.get("content") or "").strip()
        if content and g.get("type") in ("objectif", "motivation"):
            add_goal(user_id, g["type"], content, g.get("priority", 1))
            changes.append({"action": "goal+", "type": g["type"], "content": content})
    for up in data.get("goal_updates", []):
        gid, content = up.get("goal_id"), (up.get("content") or "").strip()
        if gid is not None and content:
            update_goal(user_id, int(gid), content)
            changes.append({"action": "goal~", "goal_id": gid, "content": content})
    for e in data.get("new_events", []):
        content = (e.get("content") or "").strip()
        if content:
            add_event(user_id, e.get("kind", "autre"), content,
                      subject=e.get("subject"), status=e.get("status", "actif"))
            changes.append({"action": "event+", "content": content})
    for up in data.get("event_updates", []):
        key, status = up.get("event_key"), (up.get("status") or "").strip()
        if key is not None and status:
            update_event(user_id, int(key), status, content=up.get("content"))
            changes.append({"action": "event~", "event_key": key, "status": status})
    for f in data.get("new_facts", []):
        content = (f.get("content") or "").strip()
        if content:
            add_fact(user_id, f.get("category", "autre"), content)
            changes.append({"action": "fact+", "content": content})
    for up in data.get("fact_updates", []):
        fid, content = up.get("fact_id"), (up.get("content") or "").strip()
        if fid is not None and content:
            update_fact(user_id, int(fid), content)
            changes.append({"action": "fact~", "fact_id": fid, "content": content})
    for m in data.get("new_measurements", []):
        metric, value = (m.get("metric") or "").strip(), m.get("value")
        if metric and isinstance(value, (int, float)):
            add_measurement(user_id, metric, float(value), m.get("unit"))
            changes.append({"action": "mesure+", "metric": metric, "value": value})
    for w in data.get("new_workouts", []):
        log_workout(user_id, session_name=w.get("session_name"),
                    feeling=w.get("feeling"), notes=w.get("notes"))
        changes.append({"action": "workout+", "session": w.get("session_name")})
    for m in data.get("new_milestones", []):
        label, td = (m.get("label") or "").strip(), (m.get("target_date") or "").strip()
        if label and td:
            add_milestone(user_id, label, td)
            changes.append({"action": "milestone+", "label": label, "date": td})
    ns = data.get("next_session")
    if ns and ns.get("scheduled_at"):
        try:
            at = fmt_local(datetime.fromisoformat(ns["scheduled_at"]))
            add_planned_session(user_id, at, ns.get("session_name"))
            changes.append({"action": "next_session", "at": at})
        except Exception:  # noqa: BLE001
            pass
    return changes


def program_validated(history: list[dict]) -> bool:
    """La personne vient-elle d'accepter/valider le programme proposé ?"""
    tail = "\n".join(f'{m["role"]}: {m["content"]}' for m in history[-6:])
    system = (
        "Un coach fitness discute d'un PROGRAMME d'entraînement avec son client. "
        "Réponds validated=true UNIQUEMENT si les DEUX conditions sont réunies :\n"
        "(1) le coach a bel et bien PROPOSÉ un programme CONCRET (avec des "
        "exercices ou une structure de séances claire) DANS la conversation, ET\n"
        "(2) le client vient de l'ACCEPTER explicitement pour démarrer.\n"
        "Un simple 'ok', 'cool', 'ça marche', 'merci' en réaction à un conseil ou "
        "une remarque générale NE compte PAS comme validation d'un programme. S'il "
        "demande encore des changements, hésite, ou qu'aucun programme concret n'a "
        "été proposé, validated=FALSE. En cas de doute, false. "
        'Réponds UNIQUEMENT en JSON : {"validated": true|false}.'
    )
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=10,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": tail},
            ],
        )
        return bool(json.loads(response.choices[0].message.content or "{}").get("validated"))
    except Exception:  # noqa: BLE001
        return False


def finalize_program(user_id: int, history: list[dict]) -> bool:
    """Extrait le programme FINAL convenu (JSON structuré) et le stocke en SCD2.

    Renvoie True si un programme a bien été enregistré."""
    tail = "\n".join(f'{m["role"]}: {m["content"]}' for m in history[-20:])
    system = (
        "Extrait le programme d'entraînement FINAL convenu entre le coach et le "
        "client dans la conversation ci-dessous. Rends-le en JSON structuré :\n"
        '{"name": "...", "frequence": <int>, "duree_min": <int|null>, '
        '"planning_type": "fixe|flexible", '
        '"seances": [{"jour": "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche'
        '|null", "moment": "matin|midi|soir|null", "nom": "...", '
        '"exos": [{"exo": "...", "series": <int>, "reps": "..."}]}]}\n'
        'planning_type = "fixe" si des jours précis sont convenus (remplis alors '
        '"jour"/"moment") ; "flexible" si les séances sont à caser librement (mets '
        '"jour"/"moment" à null). Respecte les ajustements (jours, durée, exos '
        "remplacés). Réponds UNIQUEMENT avec ce JSON."
    )
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=800,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": tail},
            ],
        )
        content = response.choices[0].message.content or "{}"
        prog = json.loads(content)
    except Exception:  # noqa: BLE001
        return False

    if not prog.get("seances"):
        return False
    save_new_program(user_id, json.dumps(prog, ensure_ascii=False),
                     reason="programme initial validé en découverte")
    return True
