"""Persistance SQLite : profil utilisateur, historique de conversation, mesures.

C'est la MÉMOIRE du coach — ce qui fait qu'il "te connaît" d'une discussion à
l'autre. SQLite suffit pour le proto ; migrable vers Postgres ensuite sans
toucher au reste du code (seules ces fonctions changent).
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .config import settings
from . import clock


def now_local() -> datetime:
    """Heure actuelle dans le fuseau des utilisateurs (naïve, pour comparer aux
    heures locales stockées). Passe par l'horloge (accélérable en test)."""
    return clock.now_utc().astimezone(ZoneInfo(settings.timezone)).replace(tzinfo=None)


def fmt_local(dt: datetime) -> str:
    """Formate une heure locale en 'YYYY-MM-DDTHH:MM' (précision minute)."""
    return dt.strftime("%Y-%m-%dT%H:%M")

# États du parcours utilisateur (voir le plan global).
STATE_ONBOARDING = "onboarding"  # découverte en cours
STATE_PROGRAM = "program"  # proposition/ajustement du programme
STATE_ACTIVE = "active"  # coaching au quotidien


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Crée les tables si elles n'existent pas. Appelé au démarrage de l'app."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                wa_id       TEXT UNIQUE NOT NULL,        -- ex: "whatsapp:+33612345678"
                state       TEXT NOT NULL DEFAULT 'onboarding',
                style       TEXT NOT NULL DEFAULT 'bienveillant',
                coach_id    TEXT,                        -- coach attribué (cf. coaches.py)
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                role        TEXT NOT NULL,               -- 'user' | 'assistant'
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weights (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                weight_kg   REAL NOT NULL,
                logged_at   TEXT NOT NULL
            );

            -- MÉMOIRE : les trucs importants de la vie de la personne, en SCD2.
            -- Un event a un STATUT qui évolue (actif -> rémission -> résolu...) et
            -- chaque changement crée une nouvelle version -> timeline complète.
            -- `event_key` = identité stable du fil d'event (constante entre versions).
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                event_key   INTEGER,         -- lie les versions d'un même event
                kind        TEXT NOT NULL,   -- 'sante','blessure','perso','boulot','moral','victoire','dispo'
                subject     TEXT,            -- label court stable ("rhume", "douleur genou")
                content     TEXT NOT NULL,   -- description à cette version
                status      TEXT NOT NULL DEFAULT 'actif',  -- actif / amélioration / rémission / résolu / terminé...
                valid_from  TEXT NOT NULL,
                valid_to    TEXT,            -- NULL = version en cours
                is_current  INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL
            );

            -- PROGRAMME en SCD2 : on versionne. Chaque adaptation (blessure, vie...)
            -- clôt la version courante et en ouvre une nouvelle -> historique complet.
            CREATE TABLE IF NOT EXISTS programs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                version     INTEGER NOT NULL,           -- 1, 2, 3...
                content     TEXT NOT NULL,              -- JSON : jours + séances + exos
                reason      TEXT,                       -- pourquoi cette version ("blessure genou")
                valid_from  TEXT NOT NULL,
                valid_to    TEXT,                       -- NULL = version en cours
                is_current  INTEGER NOT NULL DEFAULT 1, -- 1 = version active
                created_at  TEXT NOT NULL
            );

            -- OBJECTIFS & MOTIVATIONS : le cœur du "pourquoi" (levier de motivation).
            -- type = 'objectif' (ce qu'il veut) | 'motivation' (pourquoi, le déclencheur).
            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                type        TEXT NOT NULL,   -- 'objectif' | 'motivation'
                content     TEXT NOT NULL,
                priority    INTEGER NOT NULL DEFAULT 1,  -- 1 = principal
                is_active   INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            -- SUIVI / ADHÉRENCE : journal des séances RÉELLEMENT faites.
            CREATE TABLE IF NOT EXISTS workouts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                performed_at TEXT NOT NULL,   -- date/heure de la séance
                session_name TEXT,            -- ce qu'il a fait ("jambes", "full body"...)
                feeling      TEXT,            -- ressenti ("bien", "dur", "cramé"...)
                intensity    INTEGER,         -- intensité ressentie /10 (RPE), NULL si manquée
                done         INTEGER NOT NULL DEFAULT 1,  -- 1 = faite, 0 = manquée
                notes        TEXT,            -- note libre
                created_at   TEXT NOT NULL
            );

            -- JOURNAL des messages proactifs envoyés (anti-répétition / cooldown).
            CREATE TABLE IF NOT EXISTS proactive_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL REFERENCES users(id),
                kind     TEXT NOT NULL,   -- 'inactivity','milestone','event_news'...
                ref      TEXT NOT NULL DEFAULT '',  -- clé (ex: event_key, label jalon)
                sent_at  TEXT NOT NULL
            );

            -- SÉANCES PRÉVUES (futures) : socle du moteur proactif (rappel + débrief).
            CREATE TABLE IF NOT EXISTS planned_sessions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                scheduled_at  TEXT NOT NULL,   -- heure LOCALE naïve 'YYYY-MM-DDTHH:MM'
                session_name  TEXT,
                reminder_sent INTEGER NOT NULL DEFAULT 0,
                debrief_sent  INTEGER NOT NULL DEFAULT 0,
                status        TEXT NOT NULL DEFAULT 'planned',  -- planned/done/cancelled
                created_at    TEXT NOT NULL
            );

            -- JALONS : échéances datées importantes (mariage, compétition...).
            CREATE TABLE IF NOT EXISTS milestones (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                label       TEXT NOT NULL,    -- "mariage", "compétition"...
                target_date TEXT NOT NULL,    -- 'YYYY-MM-DD'
                created_at  TEXT NOT NULL
            );

            -- MESURES du corps (série temporelle) : générique et extensible.
            -- metric = 'poids','taille','taux_gras','tour_bras','tour_taille'... -> on
            -- ajoute n'importe quelle mesure sans changer le schéma.
            CREATE TABLE IF NOT EXISTS measurements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                metric      TEXT NOT NULL,
                value       REAL NOT NULL,
                unit        TEXT,            -- 'kg','cm','%'
                measured_at TEXT NOT NULL
            );

            -- FAITS stables/récurrents (≠ events épisodiques) : quotidien, boulot,
            -- dispos, contraintes. Nourrissent surtout la planification / le programme.
            CREATE TABLE IF NOT EXISTS facts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                category    TEXT NOT NULL,   -- boulot / routine / social / contrainte / preference / sante_fond
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
            CREATE INDEX IF NOT EXISTS idx_weights_user  ON weights(user_id);
            CREATE INDEX IF NOT EXISTS idx_events_user   ON events(user_id);
            CREATE INDEX IF NOT EXISTS idx_programs_curr ON programs(user_id, is_current);
            CREATE INDEX IF NOT EXISTS idx_facts_user    ON facts(user_id);
            CREATE INDEX IF NOT EXISTS idx_goals_user    ON goals(user_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_meas_user     ON measurements(user_id, metric);
            CREATE INDEX IF NOT EXISTS idx_workouts_user ON workouts(user_id, performed_at);
            CREATE INDEX IF NOT EXISTS idx_miles_user    ON milestones(user_id, target_date);
            CREATE INDEX IF NOT EXISTS idx_planned       ON planned_sessions(status, scheduled_at);
            CREATE INDEX IF NOT EXISTS idx_prolog        ON proactive_log(user_id, kind, ref, sent_at);
            """
        )
        # Migration douce : ajoute coach_id aux bases déjà créées avant cette colonne.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
        if "coach_id" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN coach_id TEXT")

        # Migration douce des events vers le SCD2 (bases créées avant le statut).
        ecols = [r[1] for r in conn.execute("PRAGMA table_info(events)")]
        for col, ddl in [
            ("event_key", "event_key INTEGER"),
            ("subject", "subject TEXT"),
            ("status", "status TEXT NOT NULL DEFAULT 'actif'"),
            ("valid_from", "valid_from TEXT"),
            ("valid_to", "valid_to TEXT"),
            ("is_current", "is_current INTEGER NOT NULL DEFAULT 1"),
        ]:
            if col not in ecols:
                conn.execute(f"ALTER TABLE events ADD COLUMN {ddl}")
        conn.execute("UPDATE events SET event_key = id WHERE event_key IS NULL")
        conn.execute("UPDATE events SET valid_from = created_at WHERE valid_from IS NULL")

        # Migration douce : intensité ressentie + flag fait/manquée sur les séances.
        wcols = [r[1] for r in conn.execute("PRAGMA table_info(workouts)")]
        if "intensity" not in wcols:
            conn.execute("ALTER TABLE workouts ADD COLUMN intensity INTEGER")
        if "done" not in wcols:
            conn.execute("ALTER TABLE workouts ADD COLUMN done INTEGER NOT NULL DEFAULT 1")


def _now() -> str:
    return clock.now_utc().isoformat()


def get_or_create_user(wa_id: str) -> sqlite3.Row:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE wa_id = ?", (wa_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (wa_id, state, created_at) VALUES (?, ?, ?)",
                (wa_id, STATE_ONBOARDING, _now()),
            )
            row = conn.execute(
                "SELECT * FROM users WHERE wa_id = ?", (wa_id,)
            ).fetchone()
    return row


def set_state(user_id: int, state: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET state = ? WHERE id = ?", (state, user_id))


def set_style(user_id: int, style: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET style = ? WHERE id = ?", (style, user_id))


def set_coach(user_id: int, coach_id: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET coach_id = ? WHERE id = ?", (coach_id, user_id))


def save_message(user_id: int, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, _now()),
        )


def get_history(user_id: int, limit: int = 30) -> list[dict]:
    """Renvoie les `limit` derniers messages, dans l'ordre chronologique,
    au format attendu par l'API Claude : [{"role": ..., "content": ...}]."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def log_weight(user_id: int, weight_kg: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO weights (user_id, weight_kg, logged_at) VALUES (?, ?, ?)",
            (user_id, weight_kg, _now()),
        )


def latest_weight(user_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT weight_kg, logged_at FROM weights WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()


# --- Mesures du corps (série temporelle générique) ---------------------------

def add_measurement(
    user_id: int, metric: str, value: float, unit: str | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO measurements (user_id, metric, value, unit, measured_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, metric, value, unit, _now()),
        )
        return cur.lastrowid


def latest_measurement(user_id: int, metric: str) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT metric, value, unit, measured_at FROM measurements "
            "WHERE user_id = ? AND metric = ? ORDER BY id DESC LIMIT 1",
            (user_id, metric),
        ).fetchone()


def latest_measurements(user_id: int) -> list[sqlite3.Row]:
    """La dernière valeur connue de CHAQUE métrique (pour le contexte du coach)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT m.id, m.metric, m.value, m.unit, m.measured_at FROM measurements m "
            "JOIN (SELECT metric, MAX(id) AS mid FROM measurements "
            "      WHERE user_id = ? GROUP BY metric) t ON m.id = t.mid "
            "ORDER BY m.metric",
            (user_id,),
        ).fetchall()


def measurement_history(user_id: int, metric: str) -> list[sqlite3.Row]:
    """Toutes les valeurs d'une métrique dans le temps (progression)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT value, unit, measured_at FROM measurements "
            "WHERE user_id = ? AND metric = ? ORDER BY id",
            (user_id, metric),
        ).fetchall()


# --- Suivi / adhérence : journal des séances ---------------------------------

def _week_start_iso() -> str:
    now = clock.now_utc()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return monday.isoformat()


def log_workout(
    user_id: int, session_name: str | None = None, feeling: str | None = None,
    notes: str | None = None, performed_at: str | None = None,
    intensity: int | None = None, done: bool = True,
) -> int:
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO workouts (user_id, performed_at, session_name, feeling, "
            "intensity, done, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, performed_at or now, session_name, feeling,
             intensity, 1 if done else 0, notes, now),
        )
        return cur.lastrowid


def recent_workouts(user_id: int, limit: int = 30) -> list[sqlite3.Row]:
    """Historique des séances (faites ET manquées), plus récentes d'abord —
    pour le suivi/chart : date, fait ou non, intensité ressentie, ressenti."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, performed_at, session_name, feeling, intensity, done, notes "
            "FROM workouts WHERE user_id = ? ORDER BY performed_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


def workouts_done_count(user_id: int) -> int:
    """Nombre TOTAL de séances faites (pour la relance 'point charges' périodique)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS c FROM workouts WHERE user_id = ? AND done = 1",
            (user_id,),
        ).fetchone()["c"]


def sessions_this_week(user_id: int) -> int:
    """Nombre de séances FAITES depuis lundi (semaine en cours)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS c FROM workouts "
            "WHERE user_id = ? AND done = 1 AND performed_at >= ?",
            (user_id, _week_start_iso()),
        ).fetchone()["c"]


def last_workout(user_id: int) -> sqlite3.Row | None:
    """Dernière séance RÉELLEMENT faite (done=1) — sert à l'inactivité/adhérence."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT performed_at, session_name, feeling, notes FROM workouts "
            "WHERE user_id = ? AND done = 1 ORDER BY performed_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()


# --- Jalons / échéances ------------------------------------------------------

def add_milestone(user_id: int, label: str, target_date: str) -> int:
    """Upsert par label (met à jour la date si le jalon existe déjà)."""
    now = _now()
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM milestones WHERE user_id = ? AND lower(label) = lower(?)",
            (user_id, label),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE milestones SET target_date = ? WHERE id = ?",
                (target_date, existing["id"]),
            )
            return existing["id"]
        cur = conn.execute(
            "INSERT INTO milestones (user_id, label, target_date, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, label, target_date, now),
        )
        return cur.lastrowid


def get_milestones(user_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, label, target_date FROM milestones WHERE user_id = ? "
            "ORDER BY target_date",
            (user_id,),
        ).fetchall()


def upcoming_milestones(user_id: int) -> list[sqlite3.Row]:
    """Jalons à venir (date cible >= aujourd'hui), triés par date."""
    today = clock.now_utc().date().isoformat()
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, label, target_date FROM milestones WHERE user_id = ? "
            "AND target_date >= ? ORDER BY target_date",
            (user_id, today),
        ).fetchall()


# --- Séances prévues (moteur proactif) --------------------------------------

def add_planned_session(
    user_id: int, scheduled_at: str, session_name: str | None = None,
) -> int:
    """Enregistre la prochaine séance. Annule les séances prévues encore en
    attente (une seule "prochaine séance" active à la fois)."""
    now = _now()
    with get_conn() as conn:
        conn.execute(
            "UPDATE planned_sessions SET status = 'cancelled' "
            "WHERE user_id = ? AND status = 'planned'",
            (user_id,),
        )
        cur = conn.execute(
            "INSERT INTO planned_sessions (user_id, scheduled_at, session_name, "
            "created_at) VALUES (?, ?, ?, ?)",
            (user_id, scheduled_at, session_name, now),
        )
        return cur.lastrowid


def next_planned_session(user_id: int) -> sqlite3.Row | None:
    """La prochaine séance prévue encore active."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, scheduled_at, session_name, reminder_sent, debrief_sent "
            "FROM planned_sessions WHERE user_id = ? AND status = 'planned' "
            "ORDER BY scheduled_at LIMIT 1",
            (user_id,),
        ).fetchone()


def due_reminders(now_iso: str, before_min: int = 30, late_min: int = 30) -> list[sqlite3.Row]:
    """Séances à rappeler : on vise ~30 min AVANT la séance (before_min). late_min est
    une marge de rattrapage arrière (tick manqué / temps accéléré) pour ne pas perdre
    le rappel — en usage normal le tick de 5 min tombe toujours dans la fenêtre avant.
    Renvoie aussi le wa_id pour l'envoi."""
    now = datetime.fromisoformat(now_iso)
    horizon = fmt_local(now + timedelta(minutes=before_min))
    grace = fmt_local(now - timedelta(minutes=late_min))
    with get_conn() as conn:
        return conn.execute(
            "SELECT p.id, p.user_id, p.scheduled_at, p.session_name, u.wa_id "
            "FROM planned_sessions p JOIN users u ON u.id = p.user_id "
            "WHERE p.status = 'planned' AND p.reminder_sent = 0 "
            "AND p.scheduled_at <= ? AND p.scheduled_at >= ?",
            (horizon, grace),
        ).fetchall()


def due_debriefs(now_iso: str, after_min: int = 120) -> list[sqlite3.Row]:
    """Séances passées depuis > after_min, pas encore débriefées (fenêtre 24h)."""
    cutoff = fmt_local(datetime.fromisoformat(now_iso) - timedelta(minutes=after_min))
    floor = fmt_local(datetime.fromisoformat(now_iso) - timedelta(hours=24))
    with get_conn() as conn:
        return conn.execute(
            "SELECT p.id, p.user_id, p.scheduled_at, p.session_name, u.wa_id "
            "FROM planned_sessions p JOIN users u ON u.id = p.user_id "
            "WHERE p.status = 'planned' AND p.debrief_sent = 0 "
            "AND p.scheduled_at <= ? AND p.scheduled_at >= ?",
            (cutoff, floor),
        ).fetchall()


def mark_reminder_sent(planned_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE planned_sessions SET reminder_sent = 1 WHERE id = ?", (planned_id,)
        )


def mark_debrief_sent(planned_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE planned_sessions SET debrief_sent = 1, status = 'done' "
            "WHERE id = ?", (planned_id,)
        )


# --- Journal proactif (anti-répétition) + utilisateurs actifs ---------------

def recently_sent(user_id: int, kind: str, ref: str, cooldown_hours: int) -> bool:
    """A-t-on déjà envoyé ce type de relance (même ref) dans la fenêtre de cooldown ?"""
    cutoff = (clock.now_utc() - timedelta(hours=cooldown_hours)).isoformat()
    with get_conn() as conn:
        return conn.execute(
            "SELECT 1 FROM proactive_log WHERE user_id = ? AND kind = ? AND ref = ? "
            "AND sent_at >= ? LIMIT 1",
            (user_id, kind, ref, cutoff),
        ).fetchone() is not None


def log_proactive(user_id: int, kind: str, ref: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO proactive_log (user_id, kind, ref, sent_at) VALUES (?, ?, ?, ?)",
            (user_id, kind, ref, _now()),
        )


def active_users() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, wa_id, coach_id, state FROM users WHERE state = 'active'"
        ).fetchall()


# --- Mémoire : events --------------------------------------------------------

def add_event(
    user_id: int, kind: str, content: str, subject: str | None = None,
    status: str = "actif",
) -> int:
    """Crée un nouvel event (version courante). Renvoie son event_key."""
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO events (user_id, event_key, kind, subject, content, status, "
            "valid_from, valid_to, is_current, created_at) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, NULL, 1, ?)",
            (user_id, kind, subject, content, status, now, now),
        )
        rid = cur.lastrowid
        conn.execute("UPDATE events SET event_key = ? WHERE id = ?", (rid, rid))
    return rid


def update_event(
    user_id: int, event_key: int, status: str, content: str | None = None,
) -> None:
    """Change le statut d'un event en SCD2 : clôt la version courante, en ouvre une
    nouvelle (ex: 'actif' -> 'rémission'). Garde tout l'historique."""
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT kind, subject, content FROM events "
            "WHERE user_id = ? AND event_key = ? AND is_current = 1",
            (user_id, event_key),
        ).fetchone()
        if cur is None:
            return
        conn.execute(
            "UPDATE events SET is_current = 0, valid_to = ? "
            "WHERE user_id = ? AND event_key = ? AND is_current = 1",
            (now, user_id, event_key),
        )
        conn.execute(
            "INSERT INTO events (user_id, event_key, kind, subject, content, status, "
            "valid_from, valid_to, is_current, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 1, ?)",
            (user_id, event_key, cur["kind"], cur["subject"],
             content or cur["content"], status, now, now),
        )


def active_events(user_id: int, limit: int = 12) -> list[sqlite3.Row]:
    """Les events dans leur version courante (is_current = 1)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT event_key, kind, subject, content, status, created_at "
            "FROM events WHERE user_id = ? AND is_current = 1 ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


def event_history(user_id: int, event_key: int) -> list[sqlite3.Row]:
    """Toutes les versions d'un event (timeline des statuts)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT status, content, valid_from, valid_to, is_current "
            "FROM events WHERE user_id = ? AND event_key = ? ORDER BY id",
            (user_id, event_key),
        ).fetchall()


# --- Programme en SCD2 -------------------------------------------------------

def current_program(user_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM programs WHERE user_id = ? AND is_current = 1",
            (user_id,),
        ).fetchone()


def save_new_program(user_id: int, content: str, reason: str | None = None) -> None:
    """Nouvelle version SCD2 : clôt la version courante et en ouvre une nouvelle.

    `content` est le programme sérialisé (JSON). `reason` explique le changement
    (ex: "blessure genou : jambes remplacées par haut du corps").
    """
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT MAX(version) AS v FROM programs WHERE user_id = ?", (user_id,)
        ).fetchone()
        next_version = (cur["v"] or 0) + 1
        # Clôture de la version précédente (SCD2).
        conn.execute(
            "UPDATE programs SET is_current = 0, valid_to = ? "
            "WHERE user_id = ? AND is_current = 1",
            (now, user_id),
        )
        # Ouverture de la nouvelle version courante.
        conn.execute(
            "INSERT INTO programs (user_id, version, content, reason, valid_from, "
            "valid_to, is_current, created_at) VALUES (?, ?, ?, ?, ?, NULL, 1, ?)",
            (user_id, next_version, content, reason, now, now),
        )


def program_history(user_id: int) -> list[sqlite3.Row]:
    """Toutes les versions du programme, de la plus récente à la plus ancienne."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT version, reason, valid_from, valid_to, is_current "
            "FROM programs WHERE user_id = ? ORDER BY version DESC",
            (user_id,),
        ).fetchall()


# --- Objectifs & motivations -------------------------------------------------

def add_goal(user_id: int, type: str, content: str, priority: int = 1) -> int:
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO goals (user_id, type, content, priority, is_active, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (user_id, type, content, priority, now, now),
        )
        return cur.lastrowid


def update_goal(user_id: int, goal_id: int, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE goals SET content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (content, _now(), goal_id, user_id),
        )


def deactivate_goal(user_id: int, goal_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE goals SET is_active = 0, updated_at = ? WHERE id = ? AND user_id = ?",
            (_now(), goal_id, user_id),
        )


def get_goals(user_id: int, active_only: bool = True) -> list[sqlite3.Row]:
    q = ("SELECT id, type, content, priority, is_active FROM goals WHERE user_id = ?"
         + (" AND is_active = 1" if active_only else "")
         + " ORDER BY type, priority, id")
    with get_conn() as conn:
        return conn.execute(q, (user_id,)).fetchall()


# --- Faits stables / récurrents ---------------------------------------------

def add_fact(user_id: int, category: str, content: str) -> int:
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO facts (user_id, category, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, category, content, now, now),
        )
        return cur.lastrowid


def update_fact(user_id: int, fact_id: int, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE facts SET content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (content, _now(), fact_id, user_id),
        )


def get_facts(user_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, category, content FROM facts WHERE user_id = ? ORDER BY category, id",
            (user_id,),
        ).fetchall()


# --- Édition manuelle depuis l'app : CRUD générique -------------------------
# Table + colonnes en LISTE BLANCHE (jamais d'entrée utilisateur dans le SQL) ;
# les valeurs restent paramétrées. Les tables SCD2 (events) ont leur propre chemin.

_EDIT_SPEC = {
    "goal": {"table": "goals", "fields": {"type", "content", "priority"},
             "required": {"type", "content"}, "created": ("created_at", "updated_at"),
             "touch": "updated_at"},
    "fact": {"table": "facts", "fields": {"category", "content"},
             "required": {"category", "content"}, "created": ("created_at", "updated_at"),
             "touch": "updated_at"},
    "measurement": {"table": "measurements", "fields": {"metric", "value", "unit"},
                    "required": {"metric", "value"}, "created": ("measured_at",),
                    "touch": None},
    "milestone": {"table": "milestones", "fields": {"label", "target_date"},
                  "required": {"label", "target_date"}, "created": ("created_at",),
                  "touch": None},
    "workout": {"table": "workouts",
                "fields": {"session_name", "feeling", "intensity", "done", "notes",
                           "performed_at"},
                "required": set(), "created": ("created_at",), "touch": None,
                "default_now": ("performed_at",)},
}

EDITABLE_KINDS = set(_EDIT_SPEC) | {"event"}


def create_item(user_id: int, kind: str, fields: dict) -> int:
    spec = _EDIT_SPEC[kind]
    now = _now()
    data = {k: v for k, v in fields.items() if k in spec["fields"] and v is not None}
    for col in spec.get("default_now", ()):
        data.setdefault(col, now)
    missing = spec["required"] - set(data)
    if missing:
        raise ValueError(f"champs requis manquants: {sorted(missing)}")
    for col in spec["created"]:
        data[col] = now
    data["user_id"] = user_id
    cols = ", ".join(data)
    ph = ", ".join("?" for _ in data)
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO {spec['table']} ({cols}) VALUES ({ph})", tuple(data.values())
        )
        return cur.lastrowid


def update_item(user_id: int, kind: str, item_id: int, fields: dict) -> bool:
    spec = _EDIT_SPEC[kind]
    data = {k: v for k, v in fields.items() if k in spec["fields"]}
    if not data:
        return False
    if spec["touch"]:
        data[spec["touch"]] = _now()
    sets = ", ".join(f"{k} = ?" for k in data)
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE {spec['table']} SET {sets} WHERE id = ? AND user_id = ?",
            (*data.values(), item_id, user_id),
        )
        return cur.rowcount > 0


def delete_item(user_id: int, kind: str, item_id: int) -> bool:
    spec = _EDIT_SPEC[kind]
    with get_conn() as conn:
        cur = conn.execute(
            f"DELETE FROM {spec['table']} WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        return cur.rowcount > 0


def delete_event(user_id: int, event_key: int) -> bool:
    """Retire un event de la vue courante (soft-delete SCD2 : is_current = 0)."""
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE events SET is_current = 0, valid_to = ? "
            "WHERE user_id = ? AND event_key = ? AND is_current = 1",
            (now, user_id, event_key),
        )
        return cur.rowcount > 0
