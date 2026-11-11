# 03 — Multi-agent orchestration

This lesson copies the tool lesson and adds a bank financial analyst and a customer-retention analyst. The orchestrator chooses a specialist by calling the appropriate agent-as-tool. It also adds customer lookup and illustrative retention-risk tools.

## Try these questions

```text
How did Northstar's deposits change from Q1 2024 to Q4 2024?
What signals suggest C1004 may need retention attention?
Which customers have a high illustrative retention-risk score?
What is the balance and product mix for C1002?
```

## What to expect

The orchestrator should show an activity line for `ask_finance_specialist` or `ask_research_specialist` when a specialist is useful. Customer questions should use the customer tools, including `list_high_retention_risk_customers` for the aggregate question. Specialist tools are async because one agent is calling another agent.
