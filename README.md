# Coach Fitness WhatsApp — Backend (proto)

Un coach IA accessible par WhatsApp : il mène une découverte, adapte sa
personnalité (bienveillant / militaire / culpabilisant / neutre), suit le poids
et motive dans la durée. Backend Python (FastAPI + API Claude + Twilio + SQLite).

## Architecture

```
Utilisateur (WhatsApp)
      │
      ▼  webhook
  Twilio Sandbox ──────►  FastAPI (app/main.py)
                              ├─ coach.py        cerveau (API Claude + prompt caching)
                              ├─ personalities.py styles de coach (le différenciant)
                              ├─ db.py           mémoire (SQLite : profil, historique, poids)
                              ├─ whatsapp.py     envoi sortant (Twilio REST)
                              └─ scheduler.py    relances proactives (squelette)
```

## Mise en route (local)

```bash
cd coach-fitness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # puis renseigne tes clés Anthropic + Twilio
uvicorn app.main:app --reload --port 8000
```

Vérifie que ça tourne : `curl localhost:8000/health` → `{"status":"ok"}`.

## Brancher WhatsApp (Twilio Sandbox)

1. Console Twilio → **Messaging → Try it out → WhatsApp Sandbox**.
2. Depuis ton téléphone, rejoins le sandbox (envoie le code `join <mot>` au
   numéro Twilio indiqué).
3. Expose ton serveur local à Internet :
   ```bash
   ngrok http 8000
   ```
4. Dans le sandbox, colle l'URL ngrok dans **"When a message comes in"** :
   `https://<ton-sous-domaine>.ngrok.io/webhook` (méthode **POST**).
5. Écris au coach sur WhatsApp 🎉

## État actuel (squelette)

- [x] Réception/envoi WhatsApp de bout en bout
- [x] Cerveau Claude avec personnalité adaptable + prompt caching
- [x] Mémoire (profil, historique de conversation, poids)
- [x] Détection automatique d'un poids envoyé seul (« 82 », « 82,5 kg »)
- [ ] Profilage auto en fin d'onboarding → choix du style (Phase 3, voir TODO main.py)
- [ ] Relances proactives via templates Meta (Phase 4, voir scheduler.py)
- [ ] Upload d'analyses sanguines + reco compléments (Phase 5 — sensible, garde-fous)

## Notes importantes

- **Modèle** : `gpt-4o` (OpenAI) par défaut. Pour réduire les coûts pendant les
  tests, bascule vers `gpt-4o-mini` dans `.env`.
- **Fenêtre 24h WhatsApp** : en prod, toute relance proactive hors fenêtre de 24h
  nécessite un template approuvé par Meta. Le Sandbox est permissif.
- **Santé** : la reco de compléments à partir d'analyses est volontairement hors
  périmètre du proto (risque juridique). À traiter plus tard avec garde-fous.
