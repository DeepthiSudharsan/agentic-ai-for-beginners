import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, Thinking
from pydantic_ai.mcp import MCPToolset
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import chat
from shared.data import facts_as_text, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model


# COPIED FROM LESSON 06: the final agent uses real Pydantic AI capabilities.
agent = Agent(
    local_model(),
    instructions=(
        "You are Finley, a finance QA assistant. Answer only from the supplied facts. "
        "If data is missing, say so. Keep answers short and cite the source when relevant.\n\n"
        f"Facts:\n{facts_as_text()}"
    ),
    capabilities=[
        LocalWorkspace("."),
        Skills("skills"),
        Memory(FileStore(".agent-memory")),
        Thinking(effort="low"),
    ],
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
    """Look up a reported bank metric for a quarter."""
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


server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
mcp_tools = MCPToolset(StdioTransport(command="python", args=[str(server_file)]))


if __name__ == "__main__":
    chat(agent, toolsets=[mcp_tools])
