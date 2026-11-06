# Startup Flow

## 1. Local (PowerShell, Python 3.12)

```mermaid
flowchart TD
    A["Clone repository"] --> B["py -3.12 -m venv .venv"]
    B --> C[".\\.venv\\Scripts\\Activate.ps1"]
    C --> D["python -m pip install -U pip"]
    D --> E["pip install -r backend/requirements.txt"]
    E --> F["Copy-Item .env.example .env"]
    F --> G["alembic upgrade head (from backend)"]
    G --> H["python -m cybersentinel.db.seed --if-empty"]
    H --> I["uvicorn cybersentinel.api.main:app --reload"]
    I --> J["GET /health -> ok/degraded"]
```

Local default is SQLite (`sqlite+aiosqlite:///./data/cybersentinel.db`) so M1 never depends on
Docker. Set `DATABASE_URL` to PostgreSQL for parity. Tests use an isolated SQLite database.

## 2. Docker Compose

```mermaid
flowchart TD
    A["docker compose -f deploy/compose.yaml --env-file .env up --build"] --> B["db starts"]
    B --> C{"pg_isready healthy?"}
    C -->|no| C
    C -->|yes| D["api entrypoint"]
    D --> E["alembic upgrade head"]
    E --> F{"migration ok?"}
    F -->|no| X["exit non-zero; container unhealthy"]
    F -->|yes| G["python -m cybersentinel.db.seed --if-empty"]
    G --> H["uvicorn :8000"]
    H --> I{"GET /health"}
    I -->|ok/degraded| J["web nginx starts"]
    J --> K["http://127.0.0.1:8080"]
```

The API waits for database health; `web` waits for API health. Migrations and seed run before
serving. Failures are visible in container status and logs, never swallowed.

## 3. Application lifespan

1. Construct `Settings` from environment and validate.
2. Configure structured JSON logging (level, service name).
3. Create the async engine and session factory; no implicit schema creation.
4. Mark stale `running` investigations as `interrupted` (M3+).
5. Expose the app.
6. On shutdown: cancel runner tasks cooperatively, dispose the engine.

`GET /health` independently checks database connectivity and reports:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2},
    "enrichment": {"mode": "mock", "configured": true},
    "llm": {"enabled": false, "configured": false}
  }
}
```

`status` is `degraded` if a non-critical dependency is unconfigured or unavailable; database
failure is reflected as `degraded` with HTTP 503 at the readiness endpoint (liveness remains
available for orchestration).

## 4. Configuration validation

| Condition | Result |
| --- | --- |
| invalid enum/range | startup fails with a clear Pydantic error |
| `ENRICHMENT_MODE=live` and no VT key | startup fails (no silent live→mock downgrade) |
| `LLM_ENABLED=true` and no Gemini key | startup fails |
| mock/off enrichment | starts without external keys |
| weak/default key present | startup refuses in live mode |
| SQLite path parent missing | created for local convenience, then Alembic runs |

Secrets are never echoed by `/health`, logs, reports or error envelopes.
