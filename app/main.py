"""Point d'entrée FastAPI. Deux canaux, un seul cerveau :
- WhatsApp : POST /webhook (Twilio) -> réponse envoyée via Twilio (async).
- App : POST /api/chat -> réponse renvoyée en JSON (synchrone).
Les deux passent par `flow.run_turn`.
"""

import logging

from fastapi import BackgroundTasks, FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from . import scheduler
from .api import router as api_router
from .db import init_db
from .flow import run_turn
from .whatsapp import send_whatsapp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("coach.main")

app = FastAPI(title="Coach Fitness")

# CORS : l'app (Expo web / PWA) appelle l'API depuis une autre origine. Ouvert pour
# le proto ; à restreindre avant de vrais users.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    scheduler.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _process_whatsapp(wa_id: str, body: str) -> None:
    """Tâche de fond WhatsApp : génère la réponse puis l'envoie via Twilio."""
    reply = run_turn(wa_id, body)
    send_whatsapp(wa_id, reply)


@app.post("/webhook")
async def webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),  # ex: "whatsapp:+33612345678"
    Body: str = Form(""),
) -> PlainTextResponse:
    background_tasks.add_task(_process_whatsapp, From, Body)
    return PlainTextResponse("", status_code=200)
