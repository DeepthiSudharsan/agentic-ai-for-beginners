import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.data import lookup_financial_metric, lookup_product_policy, operating_margin
from shared.model import local_model


INSTRUCTIONS = """ROLE
You are Finley, a careful finance QA assistant for the fictional Northstar Digital Bank.

TASK
Answer finance and product-policy questions using the deterministic tools provided below.

CONTEXT
The tools are the source of truth for Northstar data. This lesson is teaching tool use;
do not answer a reported financial or product-policy fact from memory.

PROCESS
1. Identify the user's latest metric, period, or product request.
2. Resolve follow-ups from the conversation. If the user gives a correction,
   the latest user message overrides earlier messages. If a follow-up says only
   a quarter, carry forward the year from the latest explicit period.
3. For reported revenue, deposits, loans, net income, NIM, or charge-off rate,
   call lookup_metric. This is the only tool for reported financial values.
4. Call calculate_net_income_margin only when the user explicitly asks for a
   net-income margin or margin calculation. Never use it for a revenue question.
5. For every fee or APR question, call lookup_product before answering.
6. Use the returned tool result as the factual answer. If the tool says data is missing, say so.

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

    This is the only tool for reported revenue, deposits, loans, net income, NIM,
    or charge-off rate. Use it for a single metric and period. Do not use the
    margin tool for revenue questions.
    """
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter as a percentage.

    Use only when the user explicitly asks for net-income margin. Never use this
    tool to look up reported revenue.
    """
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    """Look up exact fees and APR for one Northstar product.

    Use for product-policy facts only; do not infer eligibility or suitability.
    """
    return lookup_product_policy(product)


if __name__ == "__main__":
    chat(agent)
