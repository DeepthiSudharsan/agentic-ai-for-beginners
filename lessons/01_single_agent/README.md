# 01 — One agent

This is the smallest useful agent: one `Agent`, one instruction block, and one local model. It has no tools and cannot look up facts, so its main job is to explain why agents need access to reliable context.

The terminal loop is in `shared/cli.py`; the input is entered at runtime. Ask a question followed by a follow-up to see multi-turn history.

## Try these question(s)

```text
What can you help me with?
What is Northstar Digital Bank's revenue in Q2 2024?

```

## What to expect

There are no tools yet, so Finley can explain its role but cannot look up the bank's facts. The third question demonstrates multi-turn history; it does not yet provide persistent memory or factual retrieval.
