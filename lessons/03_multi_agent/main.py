import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model


facts = facts_as_text()
ORCHESTRATOR_INSTRUCTIONS = f"""ROLE
You are Finley, the Northstar Digital Bank finance QA orchestrator.

TASK
Understand the user's request and choose the smallest reliable tool or specialist needed to answer it.

CONTEXT
{facts}

DELEGATION RULES
- Use the financial specialist for quarterly metrics, growth, margins, deposits, loans, and calculations.
- Use the retention specialist for customer records, engagement, support history, missed payments, and retention risk.
- Use the aggregate retention tool for questions asking which or all customers are high risk.
- Do not use a financial tool for customer-retention questions.

GUIDELINES
Use evidence, say when data is missing, and do not provide investment, credit, eligibility, or affordability decisions.

OUTPUT FORMAT
Return a concise answer with the relevant source. Do not expose internal routing or reasoning."""
FINANCE_INSTRUCTIONS = f"""ROLE
You are Northstar's financial-analysis specialist.

TASK
Analyze quarterly financial performance and explain calculations simply.

CONTEXT
{facts}

PROCESS
Identify the metric and period, use the relevant tool, then explain the result and source.

GUIDELINES
Use only supplied data. Do not invent metrics, forecasts, or investment advice.

OUTPUT FORMAT
Return a concise evidence-based explanation."""
RETENTION_INSTRUCTIONS = f"""ROLE
You are Northstar's customer-retention specialist.

TASK
Explain observable customer engagement signals and illustrative retention risk.

CONTEXT
{facts}

PROCESS
Identify the customer or customer set, use the relevant customer tool, and report the signals behind the result.

GUIDELINES
The score is a teaching rule, not a trained churn model or credit decision. Do not recommend consequential action.

OUTPUT FORMAT
Return a concise evidence-based explanation with its source."""


# COPIED FROM LESSON 02: the original agent and deterministic tool remain.
model = local_model()
agent = Agent(
    model,
    instructions=ORCHESTRATOR_INSTRUCTIONS,
)


@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    return lookup_product_policy(product)


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
    return result.output


# Lesson source: https://github.com/DeepthiSudharsan/agentic-ai-for-beginners/blob/main/lessons/03_multi_agent/main.py
# NEW IN THIS LESSON: customer tools support the retention specialist.
@agent.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    """Look up one customer record by exact ID, such as C1004.

    Use this for a specific customer's segment, products, balance, activity, or support fields.
    Do not use this to list all high-risk customers; use the aggregate risk tool for that.
    """
    return lookup_customer(customer_id)


@agent.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    """Calculate the illustrative retention-risk score for one exact customer ID.

    Use this only when the question concerns one customer. The score is a transparent teaching rule,
    not a trained churn model, credit decision, or recommendation.
    """
    return retention_risk(customer_id)


@agent.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List every sample customer whose illustrative retention-risk score is high.

    Use this for questions asking which or all customers meet the high-risk rule. The optional
    argument is ignored so the tool remains tolerant of an unnecessary model-supplied ID.
    """
    return high_retention_risk_customers(customer_id)


if __name__ == "__main__":
    chat(agent)
