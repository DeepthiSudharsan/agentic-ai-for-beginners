# 02 — Tools

This lesson copies the single-agent lesson and adds typed Python tools for looking up a bank metric and calculating net-income margin. The model can decide when to call deterministic code instead of inventing or doing arithmetic itself.

## Try these questions

```text
What was Northstar's revenue in Q2 2024?
What was Northstar's net-income margin in Q3 2024?
What are the annual fee and APR for the Northstar Rewards Card?
What was Northstar's share price?
```

## What to expect

Supported questions should show an activity line such as `[agent] invoking tool: lookup_metric`, followed by an answer with a source. The share-price question is intentionally missing from the dataset, so the assistant should say that it cannot find the information.
