"""Configuration centralisée, lue depuis les variables d'environnement / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Twilio WhatsApp
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # Base de données
    database_path: str = "coach.db"

    # Proactif
    timezone: str = "Europe/Brussels"  # fuseau des utilisateurs (rappels à l'heure locale)
    proactive_enabled: bool = True  # moteur de relances (rappels/débriefs) actif
    tick_seconds: int = 300  # cadence du scheduler en mode normal (300 = 5 min)

    # MODE TEST — accélération du temps, pilotable À CHAUD depuis l'app.
    # time_factor = vitesse AU DÉMARRAGE (1.0 = temps réel).
    # Quand on active l'accéléré (bouton app) : facteur -> accel_factor, cadence
    # scheduler -> accel_tick_seconds. 600 = 2,4 min réelles valent 1 jour ; à cette
    # vitesse la fenêtre de rappel (55 min virt.) dure ~5,5 s réelles -> tick à 5 s.
    time_factor: float = 1.0
    accel_factor: float = 600.0
    accel_tick_seconds: int = 5


settings = Settings()
