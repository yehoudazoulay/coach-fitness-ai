"""Horloge (éventuellement) accélérée pour tester le moteur proactif.

Facteur réglable À CHAUD (bouton dans l'app) : à chaque changement on RÉ-ANCRE sur
l'instant virtuel courant pour que le temps ne "saute" pas — il change juste de
vitesse. ``factor == 1.0`` → temps réel. ``288.0`` → 5 min réelles = 1 jour.
Tous les modules qui lisent l'heure passent par ``now_utc()``.
"""

import time
from datetime import datetime, timedelta, timezone

from .config import settings

# Ancrage : virtuel(t) = _ANCHOR + (monotonic - _MONO0) * _FACTOR.
_MONO0 = time.monotonic()
_ANCHOR = datetime.now(timezone.utc)
_FACTOR = settings.time_factor


def now_utc() -> datetime:
    """Heure UTC courante (accélérée si _FACTOR > 1)."""
    elapsed = time.monotonic() - _MONO0
    return _ANCHOR + timedelta(seconds=elapsed * _FACTOR)


def set_factor(factor: float) -> None:
    """Change la vitesse du temps sans discontinuité (ré-ancre sur maintenant)."""
    global _MONO0, _ANCHOR, _FACTOR
    _ANCHOR = now_utc()          # fige l'instant virtuel courant
    _MONO0 = time.monotonic()
    _FACTOR = float(factor)


def get_factor() -> float:
    return _FACTOR
