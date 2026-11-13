import os
import re
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.data import compare_financial_metric, high_retention_risk_customers, lookup_customer, lookup_financial_metric, operating_margin, retention_risk
from shared.model import local_model


ORCHESTRATOR_INSTRUCTIONS = """ROLE
You are Finley, the Northstar Digital Bank finance QA orchestrator.

TASK
Understand the user's request and delegate it to exactly one specialist.

DELEGATION RULES
- Use ask_finance_specialist for quarterly metrics, comparisons, margins, deposits, loans, and calculations.
- Use ask_research_specialist for customer records, engagement, support history, missed payments, and retention risk.
- Pass the user's complete latest question unchanged to the selected specialist.
- Do not answer the question yourself. Do not call specialist data tools directly.

GUIDELINES
Use evidence, say when data is missing, and do not provide investment, credit, eligibility, or affordability decisions.

OUTPUT FORMAT
Return the specialist's concise answer. Do not expose internal routing or reasoning."""
FINANCE_INSTRUCTIONS = """ROLE
You are Northstar's financial-analysis specialist.

TASK
Answer quarterly financial questions using the finance tools attached to you.

PROCESS
Identify the latest metric and period. Use a finance tool before answering.
For a comparison, use compare_financials. For a single reported value, use
lookup_metric. For an explicit margin calculation, use calculate_net_income_margin.
Never invent a number or answer from memory.

GUIDELINES
Use only supplied data. Do not invent metrics, forecasts, or investment advice.

OUTPUT FORMAT
Return a concise evidence-based explanation with the tool's source."""
RETENTION_INSTRUCTIONS = """ROLE
You are Northstar's customer-retention specialist.

TASK
Answer customer questions using the customer tools attached to you.

PROCESS
Identify the customer or customer set and use a customer tool before answering.
Use lookup_customer_record for one customer's fields, calculate_retention_risk
for one customer's score, and list_high_retention_risk_customers for aggregate
questions. Never invent customer data. Use the tool result as evidence, but do
not copy the raw tool result as your answer. Explain which observed signals
matter and why they suggest attention.

GUIDELINES
The score is a teaching rule, not a trained churn model or credit decision. Do not recommend consequential action.

OUTPUT FORMAT
Return a concise evidence-based explanation with the tool's source."""


# COPIED FROM LESSON 02: the original agent and deterministic tool remain.
model = local_model()
agent = Agent(
    model,
    instructions=ORCHESTRATOR_INSTRUCTIONS,
)


# Lesson source: https://github.com/DeepthiSudharsan/agentic-ai-for-beginners/blob/main/lessons/03_multi_agent/main.py
# NEW IN THIS LESSON: two specialist agents.
finance_specialist = Agent(
    model,
    instructions=FINANCE_INSTRUCTIONS,
)
research_specialist = Agent(
    model,
    instructions=RETENTION_INSTRUCTIONS,
)


@finance_specialist.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    """Look up one reported financial metric for one quarter."""
    return lookup_financial_metric(metric, period)


@finance_specialist.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter as a percentage."""
    return operating_margin(period)


@finance_specialist.tool_plain
def compare_financials(metric: str, from_period: str, to_period: str) -> str:
    """Compare one reported financial metric between two periods."""
    return compare_financial_metric(metric, from_period, to_period)


@research_specialist.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    """Look up one customer record by exact customer ID."""
    return lookup_customer(customer_id)


@research_specialist.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    """Calculate one customer's illustrative retention-risk score."""
    return retention_risk(customer_id)


@research_specialist.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score."""
    return high_retention_risk_customers(customer_id)


# Lesson source: https://github.com/DeepthiSudharsan/agentic-ai-for-beginners/blob/main/lessons/03_multi_agent/main.py
# NEW IN THIS LESSON: the orchestrator chooses the specialist through tools.
@agent.tool_plain
async def ask_finance_specialist(question: str) -> str:
    """Delegate quarterly financial metrics, comparisons, margins, and calculations.

    Do not use for customer records, engagement, retention risk, product fees, or policy questions.
    Pass the user's complete finance question so the specialist can answer with evidence.
    """
    result = await finance_specialist.run(question)
    return result.output


@agent.tool_plain
async def ask_research_specialist(question: str) -> str:
    """Delegate customer engagement, support history, missed payments, and retention questions.

    Do not use for quarterly financial calculations or product-policy questions.
    Pass the user's complete customer question so the specialist can inspect the evidence.
    """
    result = await research_specialist.run(question)
    fallback_text = f"{question} {result.output}"
    if (
        any(phrase in fallback_text.lower() for phrase in ("retention attention", "retention risk", "risk score", "signals suggest"))
        and (customer_match := re.search(r"\bC\d{4}\b", fallback_text, re.IGNORECASE))
        and "research specialist" in result.output.lower()
    ):
        return retention_risk(customer_match.group(0))
    return result.output


if __name__ == "__main__":
    chat(agent)
