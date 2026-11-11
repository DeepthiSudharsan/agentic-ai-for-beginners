# 08 — Best practices, built cumulatively

Every script in this folder starts from the complete assistant in lesson 07. Run them in order:

1. `01_tracing.py` adds Langfuse observations for the agent run, local-model generation, specialist calls, data tools, MCP work, and guardrails. A trace contains inputs, outputs, nesting, tags, session metadata, and model/tool boundaries.
2. `02_caching.py` adds a bounded cache for deterministic financial lookups and records the cache version in trace metadata.
3. `03_guardrails.py` adds PII redaction followed by a separate local scrutiny agent. Only requests about the bank, its products, its customers, or data quality reach Finley.
4. `04_evals.py` runs `data/eval_cases.json` and checks correctness, groundedness, required tools, required skills, and safety behavior from the actual trajectory.
5. `05_llm_judge.py` adds a local LLM judge on top of the deterministic checks.
6. `06_monitoring.py` aggregates the judge scores and publishes them as Langfuse trace scores when Langfuse credentials are configured.

The local model and all data remain key-free. Langfuse is optional for local execution; credentials are needed only to publish traces and scores to a Langfuse project.

## Try these questions

For `01_tracing.py` and `02_caching.py`:

```text
What was Northstar's revenue in Q2 2024?
What was Northstar's revenue in Q2 2024?
```

The second identical question lets you observe the deterministic metric cache in `02_caching.py`.

For `03_guardrails.py`:

```text
What was Northstar's revenue in Q2 2024? My email is student@example.com.
What is Northstar's APR for the Rewards Card?
Write a political campaign speech.
```

The first request should redact the email before scrutiny, the second should pass, and the unrelated request should be blocked by the scrutiny agent.

For `04_evals.py`, `05_llm_judge.py`, and `06_monitoring.py`, run the scripts without chat input. They read `data/eval_cases.json`, write `agent_eval_results.json`, and print correctness, groundedness, tool-choice, skill-choice, and safety scores. Langfuse publishing is optional.
