import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP

from shared.cli import chat
from shared.data import facts_as_text, high_retention_risk_customers, lookup_financial_metric, lookup_product_policy, operating_margin
from shared.model import local_model
from shared.prompts import finance_specialist_instructions, finley_instructions, retention_specialist_instructions


# NEW IN THIS LESSON: Pydantic AI's native MCP capability connects to the local server.
server_file = Path(__file__).with_name("server.py")
agent = Agent(
    local_model(),
    instructions=finley_instructions(facts_as_text()),
    capabilities=[MCP(local=server_file, id="northstar-finance")],
)
finance_specialist = Agent(local_model(), instructions=finance_specialist_instructions(facts_as_text()))
research_specialist = Agent(local_model(), instructions=retention_specialist_instructions(facts_as_text()))


@agent.tool_plain
async def ask_finance_specialist(question: str) -> str:
    """Delegate quarterly financial metrics and calculations, not customer or policy questions."""
    result = await finance_specialist.run(question)
    return result.output


@agent.tool_plain
async def ask_research_specialist(question: str) -> str:
    """Delegate customer engagement and retention questions, not financial calculations."""
    result = await research_specialist.run(question)
    return result.output


@agent.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score; use for aggregate questions."""
    return high_retention_risk_customers(customer_id)


@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    """Look up one reported metric for one quarter; use MCP for period comparisons."""
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter."""
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    """Look up exact product fees, APR, and opening-deposit policy fields."""
    return lookup_product_policy(product)


if __name__ == "__main__":
    chat(agent)
