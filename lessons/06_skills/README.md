# 06 — Skills

This lesson copies the MCP and capabilities lesson and adds Pydantic AI Harness `Skills`. The agent discovers the real files under `skills/`, shows their names and descriptions to the model, and loads a skill on demand. There is no Python skill dictionary or hardcoded skill-selection branch.

Inspect `skills/financial-analysis/SKILL.md`, `skills/customer-retention/SKILL.md`, `skills/product-policy/SKILL.md`, and `skills/data-quality-review/SKILL.md` before running this lesson.

## Try these questions

```text
Give me a concise quarterly performance summary for Northstar.
What retention signals should I review for C1004?
What are the annual fee and APR for the Northstar Rewards Card?
Does the supplied data contain Northstar's share price?
```

## What to expect

The model should load a relevant `SKILL.md` file before answering. Watch for an activity line mentioning `skill/capability` and compare the answer with the instructions in the skill file. The skills provide analysis guidance; the data tools still provide the evidence.
