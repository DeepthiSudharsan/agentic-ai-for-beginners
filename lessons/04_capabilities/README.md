# 04 — Capabilities

This lesson copies the multi-agent lesson and adds native Pydantic AI capabilities. `Memory` gives Finley a persistent notebook for customer or analyst preferences, while `Thinking` enables provider-adaptive reasoning settings where the model supports them. `LocalWorkspace` gives the agent a bounded workspace reference. These are passed through the real `capabilities=[...]` parameter; there is no custom capability wrapper.

## Try these questions

```text
Remember that I prefer concise answers with the source on the final line.
What was Northstar's revenue in Q2 2024?
What preference did I give you earlier?
Which customers have a high illustrative retention-risk score?
```

## What to expect

The first and third questions demonstrate the local memory capability across turns. Tool activity should be visible, but MCP and Skills have not been added yet. Thinking is provider-adaptive, so it may not produce a separate visible message with this local model.
