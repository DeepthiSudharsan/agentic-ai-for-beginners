import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, MCP
from pydantic_ai_harness import Skills

from shared.cli import chat
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model
from shared.prompts import finance_specialist_instructions, finley_instructions, retention_specialist_instructions


# COPIED FROM LESSON 04: the agent still has facts, specialists, Python tools,
# and Pydantic AI's native MCP capability.
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(
    local_model(),
    instructions=finley_instructions(facts_as_text()),
    capabilities=[
        # NEW IN THIS LESSON: the agent can discover skills/SKILL.md files.
        LocalWorkspace("."),
        Skills("skills"),
        MCP(local=server_file, id="northstar-finance"),
    ],
)
finance_specialist = Agent(local_model(), instructions=finance_specialist_instructions(facts_as_text()))
research_specialist = Agent(local_model(), instructions=retention_specialist_instructions(facts_as_text()))


@agent.tool_plain
async def ask_finance_specialist(question: str) -> str:
    result = await finance_specialist.run(question)
    return result.output


@agent.tool_plain
async def ask_research_specialist(question: str) -> str:
    result = await research_specialist.run(question)
    return result.output


@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    return lookup_product_policy(product)


@agent.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    return lookup_customer(customer_id)


@agent.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    return retention_risk(customer_id)


@agent.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score."""
    return high_retention_risk_customers(customer_id)


if __name__ == "__main__":
    chat(agent)
