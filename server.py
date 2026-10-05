# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  server.py — Application Entry Point (FastAPI Server)                     ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This file is the MAIN ENTRY POINT for the application.                   ║
# ║  Start the server with:                                                    ║
# ║    uvicorn server:app --reload --port 8001                                 ║
# ║                                                                            ║
# ║  STUDENT — SUGGESTED READ ORDER:                                           ║
# ║  1. config/settings.yaml   — Global settings (API keys, models, presets)   ║
# ║  2. config/__init__.py     — Loads YAML config and exports constants       ║
# ║  3. schemas.py             — Request body validation models (Pydantic)     ║
# ║  4. jev_questions.py       — Jev typed question definitions (noul/choice)  ║
# ║  5. services/jev_client.py — Jev Decisions API HTTP client                 ║
# ║  6. services/mentor_chat.py— DeepSeek LLM chat client                      ║
# ║  7. routes/scenarios.py    — API endpoint handlers (business logic)        ║
# ║  8. server.py (THIS FILE)  — FastAPI application & static server mount     ║
# ║  9. static/index.html      — Frontend UI & real CSV lab                    ║
# ║                                                                            ║
# ║  Architecture Overview:                                                    ║
# ║  ──────────────────────                                                    ║
# ║  [Browser / UI]                                                            ║
# ║       │  POST /api/data-quality (JSON body)                                ║
# ║       ▼                                                                    ║
# ║  [server.py] → [routes/scenarios.py]                                       ║
# ║       │                                                                    ║
# ║       ├── [services/jev_client.py] → OpenRouter Decisions API → Jev       ║
# ║       │     Returns: { noul: 0.23, choice: "nulls", score: 2.7 }         ║
# ║       │                                                                    ║
# ║       └── [services/mentor_chat.py] → OpenRouter Chat API → DeepSeek     ║
# ║             Returns: "This column has 42% nulls. I recommend..."          ║
# ║       │                                                                    ║
# ║       ▼                                                                    ║
# ║  [Browser / UI] ← Combined JSON response with decisions + guidance         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── Import configuration ─────────────────────────────────────────────────────
# Configuration module loads settings.yaml + .env and exports constants.
from config import (
    OPENROUTER_API_KEY,
    JEV_MODEL,
    CHAT_MODEL,
    STATIC_DIR,
)

# ── Import API routes ────────────────────────────────────────────────────────
# Import scenario APIRouter defined in routes/scenarios.py.
from routes.scenarios import router as scenario_router


# ═══════════════════════════════════════════════════════════════════════════════
#  Create FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════
# Instantiates FastAPI application with title, version, and documentation details.
app = FastAPI(
    title="DE Mentor — Jev Demo",
    version="2.0.0",
    description=(
        "Data Engineering Mentor Demo using Jev (TypeSafe AI) "
        "structured decisions via OpenRouter."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Mount Static Files
# ═══════════════════════════════════════════════════════════════════════════════
# Serves frontend static assets (HTML, CSS, JS, fonts).
# Requests to /static/... map directly to the static/ directory.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ═══════════════════════════════════════════════════════════════════════════════
#  Include Scenario Routes
# ═══════════════════════════════════════════════════════════════════════════════
# Mounts the APIRouter (all endpoints prefixed with /api).
app.include_router(scenario_router)


# ═══════════════════════════════════════════════════════════════════════════════
#  Root & Health Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def index():
    """
    Root URL endpoint serving the frontend single-page application.
    Navigating to http://127.0.0.1:8001/ serves static/index.html.
    """
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    """
    Health check endpoint verifying server status and API key configuration.
    Polled by the frontend status badge to display connection state.

    Returns:
        - status: "ok" (server is running)
        - jev_model: Configured Jev model identifier
        - chat_model: Configured generative LLM model identifier
        - openrouter_key_set: Boolean indicating whether API key is configured
    """
    return {
        "status": "ok",
        "jev_model": JEV_MODEL,
        "chat_model": CHAT_MODEL,
        "openrouter_key_set": bool(OPENROUTER_API_KEY),
    }
