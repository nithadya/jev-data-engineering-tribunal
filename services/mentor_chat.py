# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  services/mentor_chat.py — Mentor Chat Client (LLM Explanations)          ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This module manages client requests to the DeepSeek generative LLM        ║
# ║  via OpenRouter. Once Jev renders a structured decision, this LLM is       ║
# ║  invoked to provide human-readable explanations and code recommendations.  ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  - Jev produces structured numbers, enums, and probabilities.              ║
# ║  - To explain "why" to students, a standard LLM (DeepSeek) generates       ║
# ║    approachable, actionable explanations and code snippets.                ║
# ║  - Also powers the free-form Mentor Chat / Forum tab.                      ║
# ║                                                                            ║
# ║  KEY CONCEPT — Two-Model Architecture:                                     ║
# ║  Step 1: Jev → Structured decision (fast, typed, deterministic, ~200ms)    ║
# ║  Step 2: DeepSeek → Rich explanation of that decision (~1-2s)              ║
# ║                                                                            ║
# ║  This pattern is widespread in modern production architectures:            ║
# ║  a "fast brain" executes real-time pipeline decisions, while a             ║
# ║  "slow brain" handles ad-hoc human-facing synthesis and explanation.       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import httpx

from config import (
    OPENROUTER_API_KEY,
    CHAT_MODEL,
    CHAT_MAX_TOKENS,
    CHAT_URL,
    HTTP_REFERER,
    APP_TITLE,
)


def _auth_headers() -> dict[str, str]:
    """Returns OpenRouter authentication headers for chat completions."""
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": APP_TITLE,
    }


async def chat_with_mentor(
    client: httpx.AsyncClient,
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Sends a chat completion request to DeepSeek and retrieves text guidance.

    Parameters:
    ───────────
    client : httpx.AsyncClient
        Asynchronous HTTP client reusing active connection pools.

    system_prompt : str
        Persona instructions for the LLM.
        Example: "You are an expert data engineering and data science mentor."

    user_message : str
        Input query or formatted decision context.
        Two primary use cases:
        1. Explaining a Jev decision:
           "Column 'age': safe=0.23, issue=nulls, severity=2.7/3. Give recommendation."
        2. Free-form question:
           "What is dbt and how does it fit into a modern data stack?"

    Returns:
    ────────
    str: Generated markdown text explanation.
         If an error occurs, returns "(chat unavailable: {status_code})" rather
         than raising an unhandled exception, ensuring Jev metrics still display.

    Note:
    ─────
    OpenRouter uses an OpenAI-compatible Chat Completions API format, ensuring
    interoperability with standard toolchains.
    """
    # Build standard OpenAI-compatible messages array
    resp = await client.post(
        CHAT_URL,
        headers=_auth_headers(),
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": CHAT_MAX_TOKENS,
        },
        timeout=45.0,
    )

    # Graceful degradation if LLM is unavailable
    if resp.status_code != 200:
        return f"(chat unavailable: {resp.status_code})"

    # Extract assistant message content
    return resp.json()["choices"][0]["message"]["content"]
