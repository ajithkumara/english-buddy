# English Buddy 🎙️

> AI-powered spoken English practice for Sri Lankan learners.

Talk to Alex — your friendly AI conversation partner — about cricket, food, travel, work, or anything else. Alex listens, replies naturally, and never judges.

---

## Quick start (local)

**Requirements:** Python 3.x · Google Chrome

```bash
git clone https://github.com/YOUR_USERNAME/english-buddy.git
cd english-buddy

# Copy the example env file and add your key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Windows
start.bat

# Mac / Linux
bash start.sh
```

Open **http://localhost:8765/frontend/english_buddy.html** in Chrome.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS — single file, no framework |
| Voice input | Chrome Web Speech API (SpeechRecognition) |
| AI backend | Claude Sonnet 4.5 (Anthropic) |
| Voice output | Browser SpeechSynthesis — Google US English |
| Backend | Python 3 HTTP server — proxies AI API calls |
| Auth (Phase 1) | Supabase |
| Payments (Phase 1) | Stripe |
| Deployment | Railway |

---

## Project structure

```
english-buddy/
├── frontend/
│   └── english_buddy.html      # Complete browser app
├── backend/
│   └── server.py               # Proxy server + future auth/payment routes
├── docs/
│   ├── Architecture.docx       # Full system architecture document
│   ├── ProjectReport.docx      # Project report and roadmap
│   └── ClickUp_Tasks.csv       # Import into ClickUp
├── scripts/
│   └── (future utility scripts)
├── .env.example                # Template — copy to .env and fill in keys
├── .gitignore
├── Procfile                    # Railway: web: python backend/server.py
├── requirements.txt
├── start.bat                   # Windows launcher
├── start.sh                    # Mac/Linux launcher
└── README.md
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in your keys. **Never commit `.env` to Git.**

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | From console.anthropic.com |
| `PORT` | No | Default: 8765 |
| `SUPABASE_URL` | Phase 1 | From supabase.com project settings |
| `SUPABASE_KEY` | Phase 1 | Supabase service role key |
| `STRIPE_SECRET` | Phase 1 | From stripe.com dashboard |
| `STRIPE_WEBHOOK_SECRET` | Phase 1 | From Stripe webhook settings |

---

## Deployment (Railway)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select `english-buddy` repository
4. Add environment variables in Railway dashboard
5. Railway reads `Procfile` and starts `server.py` automatically
6. Add custom domain `englishbuddy.lk` in Railway Settings → Domains

---

## Roadmap

| Phase | Target | Key features |
|---|---|---|
| **Phase 1** | Month 1–2 | Auth (Supabase) · Payments (Stripe) · Deploy to Railway |
| **Phase 2** | Month 2–4 | User profiles · Adaptive AI · Error highlighting · Sinhala/Tamil tips |
| **Phase 3** | Month 4–8 | School leaderboard · Referral system · Teacher dashboard · PWA |
| **Phase 4** | Month 8–12 | Premium voice (ElevenLabs) · Lip sync · Bangladesh/Nepal expansion |

See `docs/ProjectReport.docx` for the full roadmap and `docs/ClickUp_Tasks.csv` to import tasks.

---

## Contributing

This is a private project. Contact the owner before contributing.

## License

Proprietary — All rights reserved © 2026 English Buddy LK
