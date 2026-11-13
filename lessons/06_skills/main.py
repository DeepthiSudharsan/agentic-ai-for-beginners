import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import LocalWorkspace, MCP
from pydantic_ai.capabilities import Thinking
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import chat, show_activity
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, quarterly_performance_summary, retention_risk
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

PROCESS
Load the financial-analysis skill before answering. Then use the appropriate
financial tool for evidence. Use the quarterly-summary tool for broad summary
requests; use the single-metric tool only when both a metric and period are
specified. Never invent figures from memory.

CONTEXT
{facts}

OUTPUT FORMAT
Explain the result, calculation, and source briefly. Never invent missing data or advice."""
RETENTION_INSTRUCTIONS = f"""ROLE
You are Northstar's customer-retention specialist.

TASK
Explain customer engagement signals and illustrative retention risk.

PROCESS
Load the customer-retention skill before answering. Then use the appropriate
customer tool for evidence. Never invent customer data from memory.

CONTEXT
{facts}

OUTPUT FORMAT
Report observable signals and sources. Call the score a teaching rule, not a trained prediction or decision."""

model = local_model()


# COPIED FROM LESSON 05: Python tools, capabilities, and MCP remain.
# Lesson source: https://github.com/DeepthiSudharsan/agentic-ai-for-beginners/blob/main/lessons/06_skills/main.py
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
finance_specialist = Agent(
    model,
    instructions=FINANCE_INSTRUCTIONS,
    capabilities=[LocalWorkspace("."), Thinking(effort="low"), Skills("skills")],
)
research_specialist = Agent(
    model,
    instructions=RETENTION_INSTRUCTIONS,
    capabilities=[LocalWorkspace("."), Thinking(effort="low"), Skills("skills")],
)


@finance_specialist.tool
async def finance_quarterly_summary(ctx: RunContext, question: str = "") -> str:
    """Summarize the reported quarterly financial sample for broad summary requests."""
    ctx.load_capability("financial-analysis")
    return quarterly_performance_summary()


@finance_specialist.tool
async def finance_lookup_metric(ctx: RunContext, metric: str, period: str) -> str:
    """Look up one reported metric for one specified quarter; do not use for broad summaries."""
    ctx.load_capability("financial-analysis")
    return lookup_financial_metric(metric, period)


@finance_specialist.tool
async def finance_calculate_net_income_margin(ctx: RunContext, period: str) -> str:
    """Calculate net income divided by revenue for one quarter."""
    ctx.load_capability("financial-analysis")
    return operating_margin(period)


@research_specialist.tool
async def research_lookup_customer(ctx: RunContext, customer_id: str) -> str:
    """Look up one customer record by exact customer ID."""
    ctx.load_capability("customer-retention")
    return lookup_customer(customer_id)


@research_specialist.tool
async def research_calculate_retention_risk(ctx: RunContext, customer_id: str) -> str:
    """Calculate one customer's illustrative retention-risk score."""
    ctx.load_capability("customer-retention")
    return retention_risk(customer_id)


@agent.tool_plain
async def ask_finance_specialist(question: str) -> str:
    """Delegate quarterly financial metrics and calculations, not customer or policy questions."""
    result = await finance_specialist.run(question, event_stream_handler=show_activity)
    return result.output


@agent.tool_plain
async def ask_research_specialist(question: str) -> str:
    """Delegate customer engagement and retention questions, not financial calculations."""
    result = await research_specialist.run(question, event_stream_handler=show_activity)
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
