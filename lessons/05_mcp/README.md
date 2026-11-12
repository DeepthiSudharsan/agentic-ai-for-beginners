# 05 — MCP

This lesson copies the capabilities lesson and adds financial-period comparison behind a separate MCP server. `server.py` contains the tool; `main.py` connects to it using Pydantic AI's native `MCP` capability. This local example has no network or credentials.

## Try these questions

```text
How did deposits change from Q1 2024 to Q4 2024?
How did loans change from Q2 2024 to Q4 2024?
Which customers have a high illustrative retention-risk score?
```

## What to expect

For period-comparison questions, the activity line should identify an MCP call, such as `[agent] invoking MCP: ...compare_financials`. The answer should include the change and cite the financial source. The other questions continue to use the Python tools from lesson 03.
