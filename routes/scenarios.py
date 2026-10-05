# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  routes/scenarios.py — API Endpoints for All Jev Scenarios                  ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This module defines the FastAPI routes for all engineering scenarios.     ║
# ║  The frontend UI dispatches HTTP POST requests to these endpoints →       ║
# ║  invokes Jev + DeepSeek → returns combined, structured JSON responses.     ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  This is the core business logic hub of the application:                   ║
# ║  1. Receives user payload validated by Pydantic models                    ║
# ║  2. Formulates the contextual "state" string for Jev                      ║
# ║  3. Calls Jev Decisions API to obtain typed, calibrated answers            ║
# ║  4. Invokes DeepSeek to synthesize human-readable engineering explanations ║
# ║  5. Packages and returns unified JSON responses to the client              ║
# ║                                                                            ║
# ║  FastAPI APIRouter explained:                                              ║
# ║  An APIRouter serves as a modular mini-application to group routes.        ║
# ║  It is mounted on the main application in server.py via                     ║
# ║  app.include_router(router), analogous to Express.js Router().             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import httpx
from fastapi import APIRouter

# ── Project module imports ────────────────────────────────────────────────────
# schemas.py → request body validation models
# jev_questions.py → question definitions for each scenario
# services/ → API client functions
# config → settings & prompts
from schemas import (
    DataQualityRequest,
    PipelineRouterRequest,
    AnomalyTriageRequest,
    SchemaRequest,
    MentorChatRequest,
    CompareRequest,
)
from jev_questions import (
    DATA_QUALITY_QUESTIONS,
    PIPELINE_ROUTER_QUESTIONS,
    ANOMALY_TRIAGE_QUESTIONS,
    SCHEMA_ADVISOR_QUESTIONS,
)
from services.jev_client import call_jev_decisions
from services.mentor_chat import chat_with_mentor
from config import MENTOR_SYSTEM_PROMPT, CHAT_MODEL


# ── Create Router ────────────────────────────────────────────────────────────
# prefix="/api" groups all routes under /api/...
router = APIRouter(prefix="/api", tags=["scenarios"])


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 1 — Data Quality Gate
#  POST /api/data-quality
# ═══════════════════════════════════════════════════════════════════════════════
#
# Execution Flow:
#  1. Student sends column metadata (name, null percentage, samples)
#  2. Constructs contextual "state" string for Jev
#  3. Jev answers 3 questions in parallel (safe?, issue?, severity?)
#  4. DeepSeek synthesizes mentor recommendation and PySpark remediation code
#  5. Returns combined structured JSON response

@router.post("/data-quality")
async def data_quality(req: DataQualityRequest):
    # ── Step 1: Build context "state" for Jev evaluation ──
    state = (
        f"Column: '{req.column_name}'\n"
        f"Null percentage: {req.null_pct:.1f}%\n"
        f"Sample values (first 10): {req.sample_values[:10]}\n"
        f"Description: {req.description or 'n/a'}"
    )

    # ── Step 2: Call Jev Decisions API ──
    async with httpx.AsyncClient() as client:
        result = await call_jev_decisions(client, state, DATA_QUALITY_QUESTIONS)

        # ── Step 3: Extract typed values from Jev answers ──
        # Each answer type has a specific key:
        #   noul → "noul" key (float 0-1)
        #   choice → "choice" key (string, best option name)
        #   score → "score" key (float on rubric scale)
        a = result["answers"]
        safe = a.get("safe_to_use", {}).get("noul", 0.5)
        issue = a.get("quality_issue", {}).get("choice", "unknown")
        sev = a.get("severity", {}).get("score", 1)

        # ── Step 4: Call DeepSeek → Generate mentor explanation ──
        # Jev decision summary → DeepSeek → human-readable tip.
        # System prompt (from settings.yaml) defines mentor personality.
        tip = await chat_with_mentor(
            client,
            "You are a friendly, expert data engineering mentor.",
            f"Column '{req.column_name}': safe_to_use={safe:.2f}, issue={issue}, severity={sev:.1f}/3. "
            "Give a 3-sentence practical recommendation. Be specific and encouraging.",
        )

    # ── Step 5: Return combined response payload ──
    return {
        "scenario": "data_quality",
        "column": req.column_name,
        "jev": {
            "safe_to_use_prob": round(safe, 3),
            "quality_issue": issue,
            "issue_probabilities": a.get("quality_issue", {}).get("probabilities", {}),
            "severity_score": round(sev, 2),
        },
        "mentor_tip": tip,
        "latency_ms": result["latency_ms"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 2 — Pipeline Step Router
#  POST /api/pipeline-router
# ═══════════════════════════════════════════════════════════════════════════════
#
# Execution Flow:
#  1. Student posts pipeline context (dataset, upstream output, goal)
#  2. Jev decides: optimal next step, partition necessity, complexity score
#  3. DeepSeek generates code-level recommendation (PySpark / Pandas)

@router.post("/pipeline-router")
async def pipeline_router(req: PipelineRouterRequest):
    state = (
        f"Dataset: {req.dataset_description}\n"
        f"Output of current step: {req.current_step_output}\n"
        f"End goal: {req.goal}"
    )

    async with httpx.AsyncClient() as client:
        result = await call_jev_decisions(client, state, PIPELINE_ROUTER_QUESTIONS)
        a = result["answers"]
        step = a.get("next_step", {}).get("choice", "unknown")
        partition = a.get("needs_partitioning", {}).get("noul", 0.5)
        complexity = a.get("complexity", {}).get("score", 1)

        # Generate mentor code recommendation
        tip = await chat_with_mentor(
            client,
            "You are a friendly, expert data engineering mentor.",
            f"Pipeline needs a '{step}' step (partition={'yes' if partition > 0.6 else 'no'}, "
            f"complexity={complexity:.1f}/3). "
            "Give a concrete 3-4 sentence code-level recommendation using PySpark or Pandas. "
            "Include one specific function name.",
        )

    return {
        "scenario": "pipeline_router",
        "jev": {
            "next_step": step,
            "step_probabilities": a.get("next_step", {}).get("probabilities", {}),
            "needs_partitioning_prob": round(partition, 3),
            "complexity_score": round(complexity, 2),
        },
        "mentor_tip": tip,
        "latency_ms": result["latency_ms"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 3 — Anomaly Triage
#  POST /api/anomaly-triage
# ═══════════════════════════════════════════════════════════════════════════════
#
# Execution Flow:
#  1. Student posts anomaly parameters (metric, expected, actual, context)
#  2. Computes percentage deviation from baseline
#  3. Jev triages: real anomaly probability, classification type, urgency rubric
#  4. DeepSeek produces an actionable 3-step investigation checklist

@router.post("/anomaly-triage")
async def anomaly_triage(req: AnomalyTriageRequest):
    # Calculate percentage deviation from baseline
    deviation_pct = (
        abs(req.actual_value - req.expected_value)
        / (abs(req.expected_value) + 1e-9)
        * 100
    )

    state = (
        f"Metric: {req.metric_name}\n"
        f"Expected: {req.expected_value}\n"
        f"Actual: {req.actual_value}\n"
        f"Deviation: {deviation_pct:.1f}%\n"
        f"Context: {req.context or 'none'}"
    )

    async with httpx.AsyncClient() as client:
        result = await call_jev_decisions(client, state, ANOMALY_TRIAGE_QUESTIONS)
        a = result["answers"]
        is_real = a.get("is_real_anomaly", {}).get("noul", 0.5)
        a_type = a.get("anomaly_type", {}).get("choice", "unknown")
        urgency = a.get("urgency", {}).get("score", 1)

        tip = await chat_with_mentor(
            client,
            "You are a friendly, expert data engineering mentor.",
            f"Anomaly in '{req.metric_name}': {deviation_pct:.1f}% deviation, "
            f"{is_real:.0%} real, type='{a_type}', urgency={urgency:.1f}/3. "
            "Give a 3-step debugging checklist. Be concise and practical.",
        )

    return {
        "scenario": "anomaly_triage",
        "metric": req.metric_name,
        "deviation_pct": round(deviation_pct, 2),
        "jev": {
            "is_real_anomaly_prob": round(is_real, 3),
            "anomaly_type": a_type,
            "type_probabilities": a.get("anomaly_type", {}).get("probabilities", {}),
            "urgency_score": round(urgency, 2),
        },
        "mentor_tip": tip,
        "latency_ms": result["latency_ms"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 4 — Schema Advisor
#  POST /api/schema-advisor
# ═══════════════════════════════════════════════════════════════════════════════
#
# Execution Flow:
#  1. Student posts table schema, column definitions, and volume estimates
#  2. Formulates column schema summary for Jev
#  3. Jev advises: storage format, indexing necessity, normalization level
#  4. DeepSeek generates architectural design guidance

@router.post("/schema-advisor")
async def schema_advisor(req: SchemaRequest):
    # Compress column definitions into a concise schema summary
    col_summary = ", ".join(
        f"{c['name']} ({c.get('dtype', '?')}{'?' if c.get('nullable') else ''})"
        for c in req.columns[:20]
    )
    state = (
        f"Table: {req.table_name}\n"
        f"Rows: {req.row_count_estimate:,}\n"
        f"Columns ({len(req.columns)}): {col_summary}"
    )

    async with httpx.AsyncClient() as client:
        result = await call_jev_decisions(client, state, SCHEMA_ADVISOR_QUESTIONS)
        a = result["answers"]
        fmt = a.get("storage_format", {}).get("choice", "parquet")
        idx = a.get("needs_indexing", {}).get("noul", 0.5)
        norm = a.get("normalisation", {}).get("score", 2)

        tip = await chat_with_mentor(
            client,
            "You are a friendly, expert data engineering mentor.",
            f"Table '{req.table_name}' ({req.row_count_estimate:,} rows): "
            f"format='{fmt}', indexing={idx:.0%}, normalisation={norm:.1f}/3. "
            "Give 3 bullet-point design recommendations with specific tool/syntax names.",
        )

    return {
        "scenario": "schema_advisor",
        "table": req.table_name,
        "columns": len(req.columns),
        "row_estimate": req.row_count_estimate,
        "jev": {
            "storage_format": fmt,
            "format_probabilities": a.get("storage_format", {}).get("probabilities", {}),
            "needs_indexing_prob": round(idx, 3),
            "normalisation_score": round(norm, 2),
        },
        "mentor_tip": tip,
        "latency_ms": result["latency_ms"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 5 — Mentor Chat (Free-form)
#  POST /api/mentor-chat
# ═══════════════════════════════════════════════════════════════════════════════
#
# Free-form technical questions answered directly by the DeepSeek mentor.

@router.post("/mentor-chat")
async def mentor_chat(req: MentorChatRequest):
    async with httpx.AsyncClient() as client:
        answer = await chat_with_mentor(
            client,
            MENTOR_SYSTEM_PROMPT,
            req.question,
        )
    return {"answer": answer, "model": CHAT_MODEL}


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 6 — Jev vs Standard LLM Arena (Side-by-Side Comparison)
#  POST /api/compare-jev-vs-llm
# ═══════════════════════════════════════════════════════════════════════════════
#
# Runs the exact same data engineering evaluation simultaneously on both Jev
# (structured decision model) and DeepSeek (generative LLM) to compare execution
# latency, schema determinism, and production streaming pipeline compatibility.

@router.post("/compare-jev-vs-llm")
async def compare_jev_vs_llm(req: CompareRequest):
    import time

    state = (
        f"Column: '{req.column_name}'\n"
        f"Null percentage: {req.null_pct:.1f}%\n"
        f"Sample values (first 10): {req.sample_values[:10]}\n"
        f"Description: {req.description or 'n/a'}"
    )

    llm_prompt = (
        f"Evaluate this data engineering quality gate:\n"
        f"Column: '{req.column_name}'\n"
        f"Null percentage: {req.null_pct:.1f}%\n"
        f"Sample values: {req.sample_values[:10]}\n"
        f"Description: {req.description}\n\n"
        f"Answer these 3 questions:\n"
        f"1. Is this column safe to use downstream (Yes/No with explanation)?\n"
        f"2. What is the primary defect (nulls, mixed_types, outliers, encoding, or none)?\n"
        f"3. What is the severity score on a scale of 1 to 3?\n"
        f"Provide a concise paragraph explanation with reasoning."
    )

    async with httpx.AsyncClient() as client:
        # 1. Run Jev Structured Decisions
        jev_res = await call_jev_decisions(client, state, DATA_QUALITY_QUESTIONS)
        a = jev_res["answers"]
        safe = a.get("safe_to_use", {}).get("noul", 0.5)
        issue = a.get("quality_issue", {}).get("choice", "unknown")
        sev = a.get("severity", {}).get("score", 1.0)
        jev_latency = jev_res["latency_ms"]

        # 2. Run Standard LLM (DeepSeek Chat Completion)
        t0 = time.perf_counter()
        llm_text = await chat_with_mentor(
            client,
            "You are a strict data engineering evaluator. Answer concisely.",
            llm_prompt,
        )
        llm_latency = round((time.perf_counter() - t0) * 1000)

    speedup = round(llm_latency / max(jev_latency, 1), 1)

    return {
        "task": req.task_type,
        "column": req.column_name,
        "jev": {
            "model": "typesafe/jev-latest",
            "latency_ms": jev_latency,
            "safe_to_use_prob": round(safe, 3),
            "quality_issue": issue,
            "issue_probabilities": a.get("quality_issue", {}).get("probabilities", {}),
            "severity_score": round(sev, 2),
            "output_format": "Strict Typed Math & JSON (Deterministic)",
            "pipeline_safety": "100% Safe (No string parsing / Zero hallucination risk)",
            "best_for": "Live Spark stream filtering, Kafka routing, Airflow branch gates",
        },
        "llm": {
            "model": CHAT_MODEL,
            "latency_ms": llm_latency,
            "text_response": llm_text,
            "output_format": "Unstructured Natural Language Markdown",
            "pipeline_safety": "Unsafe in Automated Pipelines (Regex/Parse breakages, Hallucinations)",
            "best_for": "Human PR reviews, root-cause debugging, documentation",
        },
        "comparison": {
            "speedup_x": speedup,
            "summary": (
                f"Jev responded in {jev_latency}ms ({speedup}x faster than general LLM at {llm_latency}ms). "
                f"Jev returned typed probabilities ready for code branching (if prob < 0.3: quarantine), "
                f"while the LLM generated conversational text that requires fragile regex parsing."
            ),
        },
    }
