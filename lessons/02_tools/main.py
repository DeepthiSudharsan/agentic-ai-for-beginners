import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, lookup_financial_metric, lookup_product_policy, operating_margin
from shared.model import local_model


facts = facts_as_text()
INSTRUCTIONS = f"""ROLE
You are Finley, a careful finance QA assistant for the fictional Northstar Digital Bank.

TASK
Answer finance and product-policy questions using the supplied facts and deterministic tools.

CONTEXT
{facts}

PROCESS
Identify the requested metric, period, or product. Use a tool when it provides evidence or performs a calculation. If the data is missing, say so.

GUIDELINES
Separate facts from interpretation. Do not invent values, forecasts, investment advice, eligibility decisions, or suitability recommendations.

OUTPUT FORMAT
Answer briefly in plain language and include the source returned by a tool."""


# COPIED FROM LESSON 01: one agent and one instruction.
model = local_model()
agent = Agent(
    model,
    instructions=INSTRUCTIONS,
)


# Lesson source: https://github.com/DeepthiSudharsan/agentic-ai-for-beginners/blob/main/lessons/02_tools/main.py
# NEW IN THIS LESSON: typed Python functions become agent tools.
@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    """Look up one reported Northstar financial metric for one quarter.

    Use for a single metric and period, such as revenue in Q2 2024. Do not use for calculations the tool does not provide.
    """
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter as a percentage."""
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    """Look up exact fees and APR for one Northstar product.

    Use for product-policy facts only; do not infer eligibility or suitability.
    """
    return lookup_product_policy(product)


if __name__ == "__main__":
    chat(agent)
