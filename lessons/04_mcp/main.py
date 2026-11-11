import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP

from shared.cli import chat
from shared.data import facts_as_text, lookup_financial_metric, lookup_product_policy, operating_margin
from shared.model import local_model


# NEW IN THIS LESSON: Pydantic AI's native MCP capability connects to the local server.
server_file = Path(__file__).with_name("server.py")
agent = Agent(
    local_model(),
    instructions=f"You are Finley, a finance QA assistant. Use only these facts:\n{facts_as_text()}",
    capabilities=[MCP(local=server_file, id="northstar-finance")],
)
finance_specialist = Agent(local_model(), instructions=f"You are a bank financial analyst. Use these facts:\n{facts_as_text()}")
research_specialist = Agent(local_model(), instructions=f"You are a customer-retention analyst. Use these facts:\n{facts_as_text()}")


@agent.tool_plain
def ask_finance_specialist(question: str) -> str:
    return finance_specialist.run_sync(question).output


@agent.tool_plain
def ask_research_specialist(question: str) -> str:
    return research_specialist.run_sync(question).output


@agent.tool_plain
def lookup_metric(metric: str, period: str) -> str:
    return lookup_financial_metric(metric, period)


@agent.tool_plain
def calculate_net_income_margin(period: str) -> str:
    return operating_margin(period)


@agent.tool_plain
def lookup_product(product: str) -> str:
    return lookup_product_policy(product)


if __name__ == "__main__":
    chat(agent)
