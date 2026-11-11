# Agentic AI for Beginners

A small, practical course for learning agentic AI with Python, [Pydantic AI](https://ai.pydantic.dev/), and an open-source Hugging Face model that runs locally on a CPU.

The course uses one simple story throughout: **Finley**, an internal assistant for a fictional digital bank. Finley answers questions about quarterly performance, customer-retention signals, and product policies. This is learning data, not investment advice, credit advice, or real customer data.

## What you will learn

Each lesson starts from the previous idea and adds one concept:

| Lesson | New idea | Run |
| --- | --- | --- |
| 01 | One agent and one prompt | `python lessons/01_single_agent/main.py` |
| 02 | Tools that let an agent use Python functions | `python lessons/02_tools/main.py` |
| 03 | An orchestrator choosing between specialist agents | `python lessons/03_multi_agent/main.py` |
| 04 | MCP: putting tools behind a standard server boundary | `python lessons/04_mcp/main.py` |
| 05 | Skills loaded from `SKILL.md` files | `python lessons/05_skills/main.py` |
| 06 | Native Pydantic AI capabilities: memory and thinking | `python lessons/06_capabilities/main.py` |
| 07 | A complete finance QA assistant | `python lessons/07_end_to_end/main.py` |
| 08 | Best practices: tracing, caching, guardrails, and evaluation | see below |

The model decides whether to call a specialist or tool from the task description. There are no hard-coded `if question == ...` handoffs in the agent lessons.

## Problem statement

A bank operations analyst needs quick, evidence-based answers from three small sources: quarterly financials, a customer-retention sample, and product policies. The assistant should:

1. answer only from the supplied data;
2. cite the source row or page when possible;
3. calculate metrics such as quarter-over-quarter growth and net-income margin;
4. investigate customer engagement without pretending a small rule is a trained churn model;
5. answer product-fee questions without making eligibility or financial recommendations;
6. refuse to invent a number when the data does not contain it.

Try questions such as:

- `What was Northstar's revenue in Q2 2024, and what source supports it?`
- `How did deposits change from Q1 to Q4 2024?`
- `What was Q3 net-income margin?`
- `What signals suggest C1004 may need retention attention?`
- `What are the annual fee and APR for the Northstar Rewards Card?`
- `Which customers have a high illustrative retention-risk score?`
- `What was Northstar's share price?` (the data does not contain this)

## Setup

Python 3.11 or newer is required by current Pydantic AI releases.

### 1. Create and activate a virtual environment with uv

Install uv from <https://docs.astral.sh/uv/getting-started/installation/> if you do not have it.

```bash
uv venv
source .venv/bin/activate       # macOS/Linux
# .venv\\Scripts\\activate      # Windows PowerShell
```

### 2. Install the course dependencies

```bash
uv pip install -r requirements.txt
```

The first model run downloads the small `Qwen/Qwen2.5-0.5B-Instruct` model from Hugging Face. No Hugging Face access token, API key, or GPU is required. The download is cached locally; CPU generation can take a little while.

Hugging Face stores the downloaded model in its local cache (usually `~/.cache/huggingface/hub`). Later runs reuse those files and do not download the model again. Set `HF_HOME` if you want the cache in another location. An `HF_TOKEN` is optional; it only helps with Hugging Face rate limits and is not required for this public model.

### 3. Run a lesson

Run commands from the repository root:

```bash
python lessons/01_single_agent/main.py
```

Type a question, press Enter, and type `exit` to stop. Start with lesson 01 and move forward in order. Each lesson has a short README explaining what was added.

## Repository map

```text
shared/                 shared model, data loading, CLI, and finance functions
data/                   tiny fictional finance dataset
data/sources/           inspectable PDF, XLSX, DOCX, CSV, and Markdown sources
lessons/01_single_agent one agent
lessons/02_tools        tools and tool arguments
lessons/03_multi_agent  model-selected subagents
lessons/04_mcp          local MCP server and client
skills/                 Agent Skills stored as SKILL.md files
lessons/05_skills       discover and load skills on demand
lessons/06_capabilities native Pydantic AI capabilities
lessons/07_end_to_end   complete assistant
lessons/08_best_practices
```

## Best-practice lessons

These are cumulative lessons. Every script starts from the end-to-end assistant in lesson 07 and adds one concern:

```bash
python lessons/08_best_practices/01_tracing.py
python lessons/08_best_practices/02_caching.py
python lessons/08_best_practices/03_guardrails.py
python lessons/08_best_practices/04_evals.py
python lessons/08_best_practices/05_llm_judge.py
python lessons/08_best_practices/06_monitoring.py
```

`01_tracing.py` adds Langfuse agent, generation, tool, and guardrail observations. Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and optionally `LANGFUSE_BASE_URL` when you want to publish traces; without them, the local agent still runs. `02_caching.py` adds deterministic lookup caching. `03_guardrails.py` redacts PII before a separate scrutiny agent checks scope and safety. `04_evals.py` runs the dataset in `data/eval_cases.json` and checks the answer plus tool trajectory. `05_llm_judge.py` adds a local-model judge. `06_monitoring.py` aggregates scores and publishes them as Langfuse trace scores.

## Design choices

- **CLI only:** less framework noise while students learn the agent loop.
- **One shared model helper:** lessons focus on agent concepts, not repeated model setup.
- **Small local model:** no paid service, API key, or GPU requirement.
- **Synthetic facts:** everyone gets the same data and can inspect it.
- **Real source artifacts:** tools return evidence locations that point to files students can open, not invented source labels.
- **Multiple source formats:** the shared data layer reads the PDF, both CSVs, Excel workbook, Word guide, Markdown policy mirror, and JSON index; later lessons expose those same sources through tools.
- **Typed boundaries:** Pydantic models make tool inputs and outputs easy to see.
- **No tests in the course:** students run each lesson directly and inspect the output.

## Suggested teaching rhythm

Read the lesson README, run the script, change one instruction or tool, and ask one new question. The comments marked `NEW IN THIS LESSON` identify the smallest new block compared with the previous lesson. Skills are real files under `skills/`; add a new skill by creating a directory with a `SKILL.md` file.

## Credits and further reading

The course is inspired by the structure of finance and churn case-study exercises, but its dataset and examples are intentionally self-contained. See the official [Pydantic AI documentation](https://ai.pydantic.dev/) and [MCP documentation](https://modelcontextprotocol.io/) for deeper reference material.
