# CyberSentinel AI

> **Evidence-Grounded SOC Alert Triage and Automated Investigation System**

CyberSentinel AI is a security operations center (SOC) triage prototype designed for auditable, deterministic alert triage, threat-intelligence correlation, MITRE ATT&CK candidate mapping, and human disposition reviews.

---

## Key Features

- **Evidence Before Claim**: All generated findings and risk scores cite append-only, checksummed evidence (`EV-NNN`).
- **Deterministic Risk Engine**: 0–100 additive score computed across rules R-01 through R-06 without LLM hallucinations.
- **MITRE ATT&CK Mapping**: Vendor-neutral mapping to curated techniques (e.g. T1110, T1078, T1133) with canonical reference links.
- **Read-Only by Construction**: Recommends disposition only; contains no execution tools for automated host isolation or containment.
- **Analyst-Centric Web Dashboard**: React 18 + Vite + TypeScript frontend with 1-second investigation progress polling, alert queue, and human review forms.

---

## Project Structure

```text
cybersentinel/
├── backend/
│   ├── cybersentinel/
│   │   ├── api/           # FastAPI application, routers & middleware
│   │   ├── core/          # Settings, logging, security & constants
│   │   ├── db/            # SQLAlchemy 2.0 models & repositories
│   │   ├── domain/        # Pure Python rules, risk engine, ATT&CK catalogue & IP policy
│   │   ├── schemas/       # Pydantic v2 request/response contracts
│   │   ├── services/      # Transactional business logic
│   │   └── utils/         # IDs, time, canonical JSON & hashing
│   ├── migrations/        # Alembic database migrations
│   └── tests/             # Unit, integration & security test suites
├── frontend/              # React 18 + Vite + Tailwind CSS Dashboard
├── docs/                  # Architecture, ERD, API specs & PRD
├── RUN_INSTRUCTIONS.md    # Step-by-step setup and execution guide
└── .env                   # Local configuration
```

---

## Quick Start

See [RUN_INSTRUCTIONS.md](file:///c:/Users/hp/OneDrive/Desktop/cybersentinel/RUN_INSTRUCTIONS.md) for full setup instructions.

```powershell
# 1. Start Backend (Terminal 1)
cd backend
..\.venv\Scripts\Activate.ps1
python -m uvicorn cybersentinel.api.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start Frontend (Terminal 2)
cd frontend
npm run dev
```

- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
