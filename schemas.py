# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  schemas.py — Pydantic Request/Response Models                            ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This module defines Pydantic models used to validate incoming API         ║
# ║  request payloads and structure responses.                                ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  - Validates request data sent by the user/UI (type checking)              ║
# ║  - Returns automatic, clear error messages when invalid data is provided   ║
# ║  - Auto-generates FastAPI interactive documentation (Swagger UI at /docs)  ║
# ║                                                                            ║
# ║  Pydantic BaseModel explained:                                             ║
# ║  Python classes inherit from BaseModel and specify attribute types.        ║
# ║  FastAPI automatically maps JSON request bodies into these classes.       ║
# ║  If a value fails type validation, a 422 Unprocessable Entity error        ║
# ║  is returned automatically.                                                ║
# ║                                                                            ║
# ║  Example:                                                                  ║
# ║     class Record(BaseModel):                                               ║
# ║         name: str              # required string                           ║
# ║         age: int = 0           # optional int, defaults to 0               ║
# ║                                                                            ║
# ║     POST {"name": "Alice"}     → Record(name="Alice", age=0) [Valid]       ║
# ║     POST {"age": 25}           → 422 Error (missing 'name')  [Rejected]    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from pydantic import BaseModel


# ── Scenario 1: Data Quality Gate ────────────────────────────────────────────
# When a new column arrives in a data pipeline, the student posts column
# metadata (name, null percentage, sample values) to evaluate its ingestion safety.
#
# Jev evaluates this metadata:
#   - safe_to_use (noul) → probability 0.0 to 1.0 (is it safe for downstream consumers?)
#   - quality_issue (choice) → identifies defect: nulls, outliers, encoding, mixed_types
#   - severity (score) → rubric score: 1 (low), 2 (medium), 3 (critical)
class DataQualityRequest(BaseModel):
    column_name: str              # Name of the column (e.g., "customer_age")
    sample_values: list[str]      # List of representative sample values (e.g., ["25", "null", "-999"])
    null_pct: float               # Percentage of null records (0.0 to 100.0)
    description: str = ""         # Optional context or business definition for the column


# ── Scenario 2: Pipeline Step Router ────────────────────────────────────────
# Used to determine the next ETL/ELT transformation step dynamically.
# The student provides dataset characteristics, upstream step output, and end goal.
#
# Jev decides:
#   - next_step (choice) → join, aggregate, filter, normalize, enrich, or cache
#   - needs_partitioning (noul) → whether storage partitioning is necessary
#   - complexity (score) → implementation difficulty on a 1-3 rubric scale
class PipelineRouterRequest(BaseModel):
    dataset_description: str      # Description of the dataset (table schema, size, row count)
    current_step_output: str      # Summary of output from the preceding pipeline transformation
    goal: str                     # Target deliverable (e.g., "BI dashboard for revenue by region")


# ── Scenario 3: Anomaly Triage ──────────────────────────────────────────────
# When telemetry metrics deviate, this endpoint assesses whether the deviation
# is a real incident or normal operational noise.
#
# Jev triages:
#   - is_real_anomaly (noul) → probability that deviation represents a true defect
#   - anomaly_type (choice) → spike, drop, trend_shift, missing, or duplicate
#   - urgency (score) → 1 (monitor), 2 (investigate), 3 (page on-call immediately)
class AnomalyTriageRequest(BaseModel):
    metric_name: str              # Telemetry metric name (e.g., "daily_active_users")
    expected_value: float         # Historical expected / baseline metric value
    actual_value: float           # Observed telemetry metric value
    context: str = ""             # Optional operational context (e.g., "no marketing campaigns active")


# ── Scenario 4: Schema Advisor ──────────────────────────────────────────────
# Evaluates lakehouse storage formats, partitioning keys, and normalization
# strategy when designing tables for a data lake.
#
# Jev advises:
#   - storage_format (choice) → parquet, delta, iceberg, csv, or json
#   - needs_indexing (noul) → whether secondary indexing or Z-ordering is recommended
#   - normalisation (score) → 1 (denormalize), 2 (balanced), 3 (normalize further)
class SchemaRequest(BaseModel):
    table_name: str               # Target table identifier (e.g., "fact_orders")
    columns: list[dict]           # Column definitions: [{"name": "...", "dtype": "...", "nullable": bool}]
    row_count_estimate: int       # Estimated record volume (e.g., 500_000_000)


# ── Scenario 5: Mentor Chat ────────────────────────────────────────────────
# Free-form Data Engineering question handled directly by the DeepSeek LLM mentor.
# Does not invoke Jev structured decisions — acts as an interactive tutor.
class MentorChatRequest(BaseModel):
    question: str                 # Student's technical question (e.g., "What is dbt?")
    topic: str = "data engineering"  # Subject domain context used to tune prompt response


# ── Scenario 6: Jev vs Standard LLM Arena ──────────────────────────────────
# Executes the same data engineering evaluation simultaneously on both Jev
# (structured decision engine) and a standard LLM (generative chat completion)
# to benchmark latency, schema determinism, and streaming pipeline compatibility.
class CompareRequest(BaseModel):
    task_type: str = "data_quality"  # Scenario identifier: "data_quality", "pipeline_router", etc.
    column_name: str = "customer_age"
    null_pct: float = 42.0
    sample_values: list[str] = ["25", "31", "null", "-999", "150", "abc", "28", "null", "22", "null"]
    description: str = "Customer age in years from CRM system export"
    dataset_description: str = ""
    goal: str = ""
