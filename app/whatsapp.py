"""Couche WhatsApp via Twilio : envoi de messages sortants.

La réception se fait dans main.py (webhook). L'envoi passe par l'API REST Twilio
plutôt que par une réponse TwiML, parce que la même fonction servira aussi pour
les relances PROACTIVES (check-ins programmés), pas seulement pour répondre.
"""

from twilio.rest import Client

from .config import settings

_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_whatsapp(to: str, body: str) -> None:
    """Envoie un message WhatsApp. `to` au format 'whatsapp:+33...'."""
    _client.messages.create(
        from_=settings.twilio_whatsapp_from,
        to=to,
        body=body,
    )
