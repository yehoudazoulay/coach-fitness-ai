"""Couche WhatsApp via Twilio : envoi de messages sortants.

La réception se fait dans main.py (webhook). L'envoi passe par l'API REST Twilio
plutôt que par une réponse TwiML, parce que la même fonction servira aussi pour
les relances PROACTIVES (check-ins programmés), pas seulement pour répondre.
"""

import logging

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from .config import settings

log = logging.getLogger("coach.whatsapp")

_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_whatsapp(to: str, body: str) -> bool:
    """Envoie un message WhatsApp (`to` au format 'whatsapp:+33...').

    Renvoie True si envoyé, False si Twilio a refusé (quota, numéro non abonné,
    fenêtre 24h...). On ne laisse PAS l'erreur remonter : un échec d'envoi ne doit
    pas planter le traitement du message.
    """
    try:
        _client.messages.create(
            from_=settings.twilio_whatsapp_from, to=to, body=body
        )
        return True
    except TwilioRestException as e:
        if e.code == 63038 or "daily messages limit" in str(e):
            log.warning("Twilio : quota quotidien du sandbox atteint (50 msg/jour). "
                        "Réponse générée mais NON envoyée à %s.", to)
        else:
            log.warning("Twilio a refusé l'envoi à %s (code %s) : %s", to, e.code, e.msg)
        return False
