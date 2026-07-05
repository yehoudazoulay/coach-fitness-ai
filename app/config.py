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
    tick_seconds: int = 300  # cadence du scheduler (300 = 5 min ; baisser en test)

    # MODE TEST — accélération du temps. 1.0 = temps réel.
    # 288.0 = 5 min réelles valent 1 jour (1440 min / 5). Mets aussi tick_seconds bas.
    time_factor: float = 1.0


settings = Settings()
