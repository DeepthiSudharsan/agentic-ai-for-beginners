import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, MCP, Thinking
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import chat
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model
from shared.prompts import finance_specialist_instructions, finley_instructions, retention_specialist_instructions


# COPIED FROM LESSON 06: the final agent uses native Pydantic AI capabilities.
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(
    local_model(),
    instructions=finley_instructions(facts_as_text(), end_to_end=True),
    capabilities=[
        LocalWorkspace("."),
        Skills("skills"),
        MCP(local=server_file, id="northstar-finance"),
        Memory(FileStore(".agent-memory")),
        Thinking(effort="low"),
    ],
)
finance_specialist = Agent(local_model(), instructions=finance_specialist_instructions(facts_as_text()))
research_specialist = Agent(local_model(), instructions=retention_specialist_instructions(facts_as_text()))


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


@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    """Look up one reported financial metric for one quarter, such as revenue for Q2 2024.

    Use for a single metric and period. Use the MCP comparison tool when comparing two periods.
    """
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter as a percentage."""
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    """Look up exact product-policy fields such as annual fee, APR, and opening deposit.

    Use for policy information only; do not infer eligibility, approval, affordability, or suitability.
    """
    return lookup_product_policy(product)


@agent.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    """Look up one customer record by exact ID, such as C1004.

    Use for one customer's fields. Do not use for an aggregate customer list.
    """
    return lookup_customer(customer_id)


@agent.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    """Calculate the illustrative retention-risk score for one exact customer ID.

    This is a transparent teaching rule, not a trained churn model, credit decision, or recommendation.
    """
    return retention_risk(customer_id)


@agent.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List every sample customer whose illustrative retention-risk score is high.

    Use for questions asking which or all customers meet the high-risk rule.
    """
    return high_retention_risk_customers(customer_id)


if __name__ == "__main__":
    chat(agent)
