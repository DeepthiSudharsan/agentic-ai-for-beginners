"""A dependency-free trace: record what happened in a JSONL file."""
import json
from datetime import datetime, timezone
from pathlib import Path

def trace(event: str, **details: object) -> None:
    record = {"time": datetime.now(timezone.utc).isoformat(), "event": event, **details}
    with Path("agent_trace.jsonl").open("a") as file:
        file.write(json.dumps(record) + "\n")
    print(record)

if __name__ == "__main__":
    trace("agent_started", lesson="best_practices")
    trace("tool_called", tool="compare_financials", metric="deposits", from_period="Q1 2024", to_period="Q4 2024")
    print("Trace written to agent_trace.jsonl. Langfuse can replace this local sink later.")
