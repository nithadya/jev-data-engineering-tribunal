# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  jev_questions.py — Jev Question Definitions for Each Scenario            ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This file defines typed questions passed to the Jev Decisions API.       ║
# ║  Each engineering scenario (data quality, pipeline router, etc.)           ║
# ║  features a specialized, calibrated question suite.                         ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  Jev requires questions in a strictly typed format rather than open text:   ║
# ║    1. type: "noul" | "choice" | "score"                                    ║
# ║    2. instructions: Prompt query evaluated by Jev against provided state   ║
# ║    3. criteria: Defined answer space / rubric dictionary or list           ║
# ║                                                                            ║
# ║  UNDERSTANDING JEV QUESTION TYPES:                                         ║
# ║                                                                            ║
# ║  ┌──────────┬─────────────────────────────────────┬─────────────────────┐  ║
# ║  │ Type     │ Description                         │ Output              │  ║
# ║  ├──────────┼─────────────────────────────────────┼─────────────────────┤  ║
# ║  │ noul     │ Binary condition — calibrated prob  │ float 0.0 → 1.0     │  ║
# ║  │          │ "Is condition X true?"              │ e.g., 0.87 = 87%    │  ║
# ║  ├──────────┼─────────────────────────────────────┼─────────────────────┤  ║
# ║  │ choice   │ Selects optimal class from candidates│ best + full dist    │  ║
# ║  │          │ "Which is best: A, B, or C?"        │ e.g., "join": 0.65  │  ║
# ║  ├──────────┼─────────────────────────────────────┼─────────────────────┤  ║
# ║  │ score    │ Position on ordered rubric (1,2,3…) │ float on scale      │  ║
# ║  │          │ "How severe is this? Low/Med/High"  │ e.g., 2.4 (of 3.0)  │  ║
# ║  └──────────┴─────────────────────────────────────┴─────────────────────┘  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 1 — Data Quality Gate
# ═══════════════════════════════════════════════════════════════════════════════
# Real-world use case:
# When ingesting new data columns into a pipeline, automated gates verify
# quality programmatically. Instead of brittle hardcoded rules ("if nulls > 50%"),
# Jev evaluates context (sample distribution, descriptions) to make calibrated decisions.

DATA_QUALITY_QUESTIONS = {
    # noul question: "Is this column safe to use as-is?"
    # Output: probability 0.0 (definitely unsafe) → 1.0 (definitely safe)
    "safe_to_use": {
        "type": "noul",
        "instructions": "Is this column safe to use as-is in a downstream data pipeline without any cleaning?",
        "criteria": {
            "true": "Column values are clean, consistent, low nulls, ready for analysis",
            "false": "Column has significant quality problems (high nulls, outliers, type mismatches)",
        },
    },
    # choice question: "What is the main data quality problem?"
    # Output: best option + probability distribution across all options
    "quality_issue": {
        "type": "choice",
        "instructions": "What is the primary data quality problem with this column?",
        "criteria": {
            "none": "No significant issue",
            "nulls": "Too many null or missing values",
            "outliers": "Statistical outliers present",
            "encoding": "Text encoding problems",
            "mixed_types": "Multiple data types mixed",
        },
    },
    # score question: "How severe is the quality problem?"
    # Output: float position on 1-2-3 rubric
    "severity": {
        "type": "score",
        "instructions": "How severe is the data quality issue for a production pipeline?",
        "criteria": [
            "Low: minor cosmetic issues, safe to proceed",
            "Medium: requires cleaning before use",
            "High: blocks downstream processing",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 2 — Pipeline Step Router
# ═══════════════════════════════════════════════════════════════════════════════
# Real-world use case:
# Dynamically selects next transformation stage in an ETL/ELT pipeline.
# Rather than static branch heuristics, Jev evaluates dataset profile and
# consumer goals to select the optimal transformation strategy.

PIPELINE_ROUTER_QUESTIONS = {
    # choice question: "What transformation should come next?"
    # Output: best step name + probability distribution
    "next_step": {
        "type": "choice",
        "instructions": "What is the most appropriate next transformation step for this data pipeline?",
        "criteria": {
            "join": "Combine with another dataset",
            "aggregate": "Group by and compute summary statistics",
            "filter": "Remove rows not meeting criteria",
            "normalize": "Standardise formats/types/ranges",
            "enrich": "Add new derived columns",
            "cache": "Materialise intermediate results",
        },
    },
    # noul question: "Does this step need data partitioning?"
    # Output: probability that partitioning is needed
    "needs_partitioning": {
        "type": "noul",
        "instructions": "Does this pipeline step require data partitioning for performance or scalability?",
        "criteria": {
            "true": "Data volume suggests partitioning is needed",
            "false": "Dataset is small or patterns do not benefit from partitioning",
        },
    },
    # score question: "How complex is this step?"
    # Output: complexity level 1-3
    "complexity": {
        "type": "score",
        "instructions": "How complex is this pipeline step to implement correctly?",
        "criteria": [
            "Simple: standard Pandas/SQL, 30 minutes",
            "Moderate: joins, window functions, or distributed logic",
            "Complex: advanced optimisation, distributed processing",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 3 — Anomaly Triage
# ═══════════════════════════════════════════════════════════════════════════════
# Real-world use case:
# Reduces alert fatigue for on-call data engineers by evaluating whether
# metric deviations represent genuine system defects or expected seasonal variance.

ANOMALY_TRIAGE_QUESTIONS = {
    # noul question: "Is this a genuine anomaly worth investigating?"
    "is_real_anomaly": {
        "type": "noul",
        "instructions": "Is this a genuine data anomaly that requires action, rather than expected variance?",
        "criteria": {
            "true": "The deviation is significant and unexplained",
            "false": "Within normal variance or a known pattern",
        },
    },
    # choice question: "What type of anomaly is this?"
    "anomaly_type": {
        "type": "choice",
        "instructions": "What type of data anomaly is this most likely?",
        "criteria": {
            "spike": "Sudden sharp increase",
            "drop": "Sudden sharp decrease",
            "trend_shift": "Gradual persistent shift",
            "missing": "Data absent or zero",
            "duplicate": "Values duplicated inflating metric",
        },
    },
    # score question: "How urgently must this be addressed?"
    "urgency": {
        "type": "score",
        "instructions": "How urgently does this anomaly need to be addressed?",
        "criteria": [
            "Monitor: log it and check next cycle",
            "Investigate: someone should look within the hour",
            "Page: immediate action, SLA at risk",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Scenario 4 — Schema Advisor
# ═══════════════════════════════════════════════════════════════════════════════
# Real-world use case:
# Data Lakehouse table architecture — recommends optimal storage format (Delta Lake,
# Parquet, Iceberg), Z-order indexing necessity, and normalization level.

SCHEMA_ADVISOR_QUESTIONS = {
    # choice question: "What storage format fits this table best?"
    "storage_format": {
        "type": "choice",
        "instructions": "What is the most appropriate storage format for this table in a modern data lake?",
        "criteria": {
            "parquet": "Columnar, efficient for analytics, good default",
            "delta": "Delta Lake — ACID transactions, time travel",
            "iceberg": "Apache Iceberg — very large tables with schema evolution",
            "csv": "Plain CSV — consumer cannot handle binary",
            "json": "JSON/JSONL — schema is dynamic or nested",
        },
    },
    # noul question: "Does this table need indexing or Z-ordering?"
    "needs_indexing": {
        "type": "noul",
        "instructions": "Does this table need indexing or Z-ordering for query performance?",
        "criteria": {
            "true": "Large table with high-cardinality filter columns in hot paths",
            "false": "Small, rarely queried, or always fully scanned",
        },
    },
    # score question: "How normalised should this table be?"
    "normalisation": {
        "type": "score",
        "instructions": "How normalised should this table design be for analytical workloads?",
        "criteria": [
            "Denormalise: flatten/pre-join for query speed",
            "Balanced: some denormalisation, keep entities separate",
            "Normalise more: too much duplication currently",
        ],
    },
}
