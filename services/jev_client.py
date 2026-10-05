# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  services/jev_client.py — Jev Decisions API Client                        ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This module manages HTTP client communication with the Jev                ║
# ║  (TypeSafe AI) Decisions API via OpenRouter.                               ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  Dispatches POST requests to the OpenRouter Decisions endpoint.            ║
# ║  The Jev model does not generate conversational text — instead it returns  ║
# ║  structured, typed decisions (noul, choice, score).                         ║
# ║                                                                            ║
# ║  KEY CONCEPT — Jev vs ChatGPT:                                             ║
# ║  ChatGPT: "Is this column safe?" → "Well, considering the null rate..."    ║
# ║  Jev:     "Is this column safe?" → { "noul": 0.23 }                        ║
# ║                                                                            ║
# ║  Jev does not chat — it evaluates structured questions and returns         ║
# ║  machine-readable decisions with calibrated probabilities.                 ║
# ║  This is why it is directly applicable in automated streaming pipelines.   ║
# ║                                                                            ║
# ║  How this works:                                                           ║
# ║  1. Builds the "state" string (context describing pipeline state)          ║
# ║  2. Formulates the "questions" dictionary (typed question definitions)     ║
# ║  3. Dispatches HTTP POST to the OpenRouter Decisions API                   ║
# ║  4. Extracts answers and returns structured payload                        ║
# ║  5. Measures latency in milliseconds for performance monitoring            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import time

import httpx
from fastapi import HTTPException

# Import configuration constants from config module
from config import (
    OPENROUTER_API_KEY,
    JEV_MODEL,
    DECISIONS_URL,
    HTTP_REFERER,
    APP_TITLE,
)


def _auth_headers() -> dict[str, str]:
    """
    Returns standard HTTP headers required for OpenRouter authentication.

    Headers explanation:
    - Authorization: Bearer token containing the API key
    - Content-Type: Designates JSON payload body
    - HTTP-Referer: Identifies client application for OpenRouter rankings
    - X-Title: Application title displayed in the OpenRouter console
    """
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": APP_TITLE,
    }


async def call_jev_decisions(
    client: httpx.AsyncClient,
    state: str,
    questions: dict,
) -> dict:
    """
    Sends a request to the Jev Decisions API and retrieves structured typed answers.

    Parameters:
    ───────────
    client : httpx.AsyncClient
        Asynchronous HTTP client supporting connection pooling and async/await.

    state : str
        Pipeline state context provided to Jev for evaluation.
        Example:
            "Column: 'customer_age'
             Null percentage: 42%
             Sample values: [25, 31, null, -999]"

    questions : dict
        Dictionary of typed questions to evaluate:
        {
            "question_name": {
                "type": "noul" | "choice" | "score",
                "instructions": "Evaluation prompt",
                "criteria": { ... }
            }
        }

        Three question types:
        - noul:   Binary yes/no condition outputting a float probability (0.0 → 1.0)
        - choice: Categorical selection from a candidate set with full distribution
        - score:  Position on an ordered rubric scale (e.g. 1.0 → 3.0)

    Returns:
    ────────
    dict containing:
        - "answers": Parsed dictionary of answers keyed by question identifier
        - "latency_ms": Roundtrip API execution latency in milliseconds

    Raises:
    ───────
    HTTPException(502) if the upstream Jev API returns a non-200 status code.

    Note:
    ─────
    Jev evaluates all questions in parallel within a single API request (~200ms latency),
    ensuring minimal overhead in automated data engineering workflows.
    """
    # High-resolution performance timer start
    t0 = time.perf_counter()

    # Asynchronous HTTP POST request to OpenRouter Decisions endpoint
    resp = await client.post(
        DECISIONS_URL,
        headers=_auth_headers(),
        json={
            "model": JEV_MODEL,
            "state": state,
            "questions": questions,
        },
        timeout=30.0,
    )

    # Validate upstream response status
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Jev API error {resp.status_code}: {resp.text[:400]}",
        )

    # Parse response payload and record latency
    data = resp.json()
    latency_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "answers": data.get("answers", {}),
        "latency_ms": latency_ms,
    }
