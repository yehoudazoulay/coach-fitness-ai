"""Horloge (éventuellement) accélérée pour tester le moteur proactif.

En prod, ``time_factor == 1.0`` → temps réel strict.
En test, ex. ``time_factor == 288.0`` → le temps virtuel avance 288x plus vite,
donc 5 minutes réelles valent 1 journée. Tous les modules qui lisent l'heure
passent par ``now_utc()`` : rappels, débriefs, inactivité, jalons, dates du jour.
"""

import time
from datetime import datetime, timedelta, timezone

from .config import settings

# Ancrage au démarrage du process : à t0, virtuel == réel, puis on accélère.
_START_MONO = time.monotonic()
_START_REAL = datetime.now(timezone.utc)


def now_utc() -> datetime:
    """Heure UTC courante, accélérée si settings.time_factor > 1."""
    factor = settings.time_factor
    if factor == 1.0:
        return datetime.now(timezone.utc)
    elapsed = time.monotonic() - _START_MONO
    return _START_REAL + timedelta(seconds=elapsed * factor)
