# Agentic AI for Beginners

A small, practical course for learning agentic AI with Python, [Pydantic AI](https://ai.pydantic.dev/), and an open-source Hugging Face model that runs locally on a CPU.

The course uses one simple story throughout: **Finley**, a finance question-answering assistant. Finley answers questions about a tiny fictional company dataset included in this repository. This is learning data, not investment advice and not real financial data.

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

A customer-support analyst needs quick answers from a small collection of quarterly finance facts. The assistant should:

1. answer only from the supplied data;
2. show the facts it used when possible;
3. calculate simple changes such as revenue growth;
4. route calculation questions to a finance specialist and general questions to a research specialist;
5. refuse to invent a number when the data does not contain it.

Try questions such as:

- `What was Northstar's revenue in Q2 2024?`
- `How much did revenue grow from Q1 to Q2 2024?`
- `What was the operating margin in Q2?`
- `Which source supports the Q2 revenue number?`
- `What was the share price?` (the data does not contain this)

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

These examples are intentionally separate so the core lessons stay uncluttered:

```bash
python lessons/08_best_practices/01_tracing.py
python lessons/08_best_practices/02_caching.py
python lessons/08_best_practices/03_guardrails.py
python lessons/08_best_practices/04_evals.py
python lessons/08_best_practices/05_llm_judge.py
python lessons/08_best_practices/06_monitoring.py
```

They use local files and standard Python by default. Langfuse integration is shown as an optional next step and is not required to run the course. Presidio is also optional; the guardrail lesson includes a small dependency-free baseline first.

## Design choices

- **CLI only:** less framework noise while students learn the agent loop.
- **One shared model helper:** lessons focus on agent concepts, not repeated model setup.
- **Small local model:** no paid service, API key, or GPU requirement.
- **Synthetic facts:** everyone gets the same data and can inspect it.
- **Typed boundaries:** Pydantic models make tool inputs and outputs easy to see.
- **No tests in the course:** students run each lesson directly and inspect the output.

## Suggested teaching rhythm

Read the lesson README, run the script, change one instruction or tool, and ask one new question. The comments marked `NEW IN THIS LESSON` identify the smallest new block compared with the previous lesson. Skills are real files under `skills/`; add a new skill by creating a directory with a `SKILL.md` file.

## Credits and further reading

The course is inspired by the structure of finance and churn case-study exercises, but its dataset and examples are intentionally self-contained. See the official [Pydantic AI documentation](https://ai.pydantic.dev/) and [MCP documentation](https://modelcontextprotocol.io/) for deeper reference material.
