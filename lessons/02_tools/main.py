import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, lookup_financial_metric, lookup_product_policy, operating_margin
from shared.model import local_model
from shared.prompts import finley_instructions


# COPIED FROM LESSON 01: one agent and one instruction.
agent = Agent(
    local_model(),
    instructions=finley_instructions(facts_as_text()),
)


# NEW IN THIS LESSON: typed Python functions become agent tools.
@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    """Look up a reported bank metric for a quarter."""
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income as a percentage of revenue for a quarter."""
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    """Look up fees and APR for one bank product."""
    return lookup_product_policy(product)


if __name__ == "__main__":
    chat(agent)
