# 08 — Best practices, built cumulatively

Every script in this folder starts from the complete assistant in lesson 07. Run them in order:

1. `01_tracing.py` adds Langfuse observations for the agent run, local-model generation, specialist calls, data tools, MCP work, and guardrails. A trace contains inputs, outputs, nesting, tags, session metadata, and model/tool boundaries.
2. `02_caching.py` adds a bounded cache for deterministic financial lookups and records the cache version in trace metadata.
3. `03_guardrails.py` adds PII redaction followed by a separate local scrutiny agent. Only requests about the bank, its products, its customers, or data quality reach Finley.
4. `04_evals.py` runs `data/eval_cases.json` and checks correctness, groundedness, required tools, required skills, and safety behavior from the actual trajectory.
5. `05_llm_judge.py` adds a local LLM judge on top of the deterministic checks.
6. `06_monitoring.py` aggregates the judge scores and publishes them as Langfuse trace scores when Langfuse credentials are configured.

The local model and all data remain key-free. Langfuse is optional for local execution; credentials are needed only to publish traces and scores to a Langfuse project.
