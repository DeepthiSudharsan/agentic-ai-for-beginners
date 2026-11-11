from __future__ import annotations

import json
from pathlib import Path

DATA_FILE = Path(__file__).parents[1] / "data" / "finance_facts.json"


def load_facts() -> dict:
    """Load the facts students can inspect and ask questions about."""
    return json.loads(DATA_FILE.read_text())


def facts_as_text() -> str:
    """Create a compact context block for a prompt."""
    data = load_facts()
    lines = [f"Company: {data['company']}"]
    for fact in data["facts"]:
        lines.append(
            f"{fact['period']}: revenue ${fact['revenue_million_usd']}m; "
            f"operating income ${fact['operating_income_million_usd']}m; "
            f"customers {fact['customers']}; source: {fact['source']}"
        )
    return "\n".join(lines)


def revenue_growth(from_period: str, to_period: str) -> str:
    facts = {item["period"]: item for item in load_facts()["facts"]}
    if from_period not in facts or to_period not in facts:
        return "I can only compare periods present in the finance facts."
    old = facts[from_period]["revenue_million_usd"]
    new = facts[to_period]["revenue_million_usd"]
    change = new - old
    percent = change / old * 100
    return f"Revenue changed by ${change:.1f}m ({percent:.1f}%) from {from_period} to {to_period}."
