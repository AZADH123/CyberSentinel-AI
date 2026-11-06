# CyberSentinel AI — Project Execution Instructions

Evidence-grounded SOC alert triage and automated investigation system.

---

## Prerequisites

1. **Python 3.12+**
2. **Node.js 20+** & **npm**
3. **PostgreSQL 16** (running locally on port `55432` or via Docker Compose)

---

## 1. Quick Start (Windows PowerShell)

### Step 1: Start PostgreSQL (if not already running)
If you have Docker installed:
```powershell
docker compose up -d db
```
*Or ensure your local PostgreSQL 16 server is running at the connection string specified in `.env` (`127.0.0.1:55432`).*

---

### Step 2: Start the Backend (Terminal 1)

```powershell
# From project root:
cd backend

# Activate virtual environment
..\.venv\Scripts\Activate.ps1

# Apply database migrations (required on first run)
python -m alembic upgrade head

# Start FastAPI server (hot-reload enabled)
python -m uvicorn cybersentinel.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health & Readiness Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 3: Start the Frontend (Terminal 2)

```powershell
# From project root:
cd frontend

# Install dependencies (if not already done)
npm install

# Start Vite development server
npm run dev
```

- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 2. Using the Dashboard

1. Open **[http://localhost:5173](http://localhost:5173)** in your browser.
2. In the top-right header, confirm the health status shows **System Ready** (green indicator).
3. Click **"Ingest Test Alert"** to submit a synthetic authentication anomaly alert.
4. Click on any alert row in the **Alerts Queue** to view the alert details.
5. Click **"Launch Investigation"** to execute deterministic triage, risk scoring, evidence capture, and MITRE ATT&CK candidate mapping.
6. Click **"Review Incident"** to record an analyst review disposition:
   - **Accept**: Confirm alert and close incident.
   - **Reject**: Dismiss as false positive (requires notes).
   - **Escalate**: Tier-2 escalation (requires notes).

---

## 3. Running Automated Tests & Linting

### Unit Tests
```powershell
cd backend
..\.venv\Scripts\Activate.ps1
python -m pytest tests/unit -v
```

### Code Formatting & Lint Check
```powershell
cd backend
python -m ruff check cybersentinel tests
```

### Frontend Production Build Test
```powershell
cd frontend
npm run build
```

---

## 4. Stopping the Project

- Press `Ctrl + C` in both terminal windows to gracefully terminate the backend and frontend processes.
- If running PostgreSQL via Docker:
  ```powershell
  docker compose down
  ```
