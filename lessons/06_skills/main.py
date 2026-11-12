import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, MCP
from pydantic_ai.capabilities import Thinking
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import chat
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model


facts = facts_as_text()
ORCHESTRATOR_INSTRUCTIONS = f"""ROLE
You are Finley, the Northstar Digital Bank finance QA orchestrator.

TASK
Choose the smallest reliable tool, specialist, MCP tool, skill, or capability needed for the user's request.

CONTEXT
{facts}

DELEGATION RULES
- Financial metrics and calculations go to the financial specialist or matching financial tool.
- Customer engagement and retention questions go to the retention specialist or customer tool.
- Product fees and APR go to the product-policy skill and tool.
- Comparisons between two financial periods go to the MCP comparison tool.
- Use the data-quality skill when the requested evidence is absent or insufficient.

OUTPUT FORMAT
Answer briefly with evidence and source. Never invent facts or expose internal routing."""
FINANCE_INSTRUCTIONS = f"""ROLE
You are Northstar's financial-analysis specialist.

TASK
Analyze quarterly metrics and calculations using the supplied evidence.

CONTEXT
{facts}

OUTPUT FORMAT
Explain the result, calculation, and source briefly. Never invent missing data or advice."""
RETENTION_INSTRUCTIONS = f"""ROLE
You are Northstar's customer-retention specialist.

TASK
Explain customer engagement signals and illustrative retention risk.

CONTEXT
{facts}

OUTPUT FORMAT
Report observable signals and sources. Call the score a teaching rule, not a trained prediction or decision."""

model = local_model()


# COPIED FROM LESSON 05: Python tools, capabilities, and MCP remain.
# NEW IN THIS LESSON: Skills discovers and loads the appropriate SKILL.md file.
server_file = Path(__file__).parents[1] / "05_mcp" / "server.py"
agent = Agent(
    model,
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    capabilities=[
        LocalWorkspace("."),
        Memory(FileStore(".agent-memory")),
        Thinking(effort="low"),
        MCP(local=server_file, id="northstar-finance"),
        Skills("skills"),
    ],
)
finance_specialist = Agent(model, instructions=FINANCE_INSTRUCTIONS)
research_specialist = Agent(model, instructions=RETENTION_INSTRUCTIONS)


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


@agent.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    """Look up one customer record by exact ID; do not use for aggregate lists."""
    return lookup_customer(customer_id)


@agent.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    """Calculate one customer's illustrative retention-risk rule, not a trained prediction."""
    return retention_risk(customer_id)


@agent.tool_plain
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score; use for aggregate questions."""
    return high_retention_risk_customers(customer_id)


if __name__ == "__main__":
    chat(agent)
