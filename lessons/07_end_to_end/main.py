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


facts = facts_as_text()
ORCHESTRATOR_INSTRUCTIONS = f"""ROLE
You are Finley, the Northstar Digital Bank finance QA orchestrator.

TASK
Understand the user's request and choose the smallest reliable tool, specialist, MCP tool, skill, or capability needed to answer it.

CONTEXT
{facts}

DELEGATION RULES
- Delegate quarterly metrics, growth, margins, deposits, loans, and financial calculations to the financial specialist or matching financial tool.
- Delegate customer records, engagement, support history, missed payments, and retention risk to the retention specialist or matching customer tool.
- Use the aggregate retention tool only when the user asks which or all customers are high risk.
- Use the product-policy tool for fees, APRs, and opening-deposit questions.
- Use the MCP comparison tool for comparisons between two financial periods.
- Use the data-quality skill when the requested evidence is absent or insufficient.

GUIDELINES
Use only the supplied evidence. Separate facts from interpretation. Treat retention scores as teaching rules, not predictions or credit decisions. Do not provide investment, eligibility, affordability, or suitability advice.

OUTPUT FORMAT
Answer concisely in plain language and include the relevant source. Never expose internal routing, tool arguments, or reasoning."""
FINANCE_INSTRUCTIONS = f"""ROLE
You are Northstar's financial-analysis specialist.

TASK
Analyze quarterly metrics and calculations using the supplied evidence.

CONTEXT
{facts}

PROCESS
Identify the metric and period, use the relevant tool, then explain the result and source.

OUTPUT FORMAT
Return a concise evidence-based explanation. Never invent missing data, forecasts, or advice."""
RETENTION_INSTRUCTIONS = f"""ROLE
You are Northstar's customer-retention specialist.

TASK
Explain customer engagement signals and illustrative retention risk.

CONTEXT
{facts}

PROCESS
Identify the customer or customer set, use the relevant customer tool, and report the signals behind the result.

OUTPUT FORMAT
Return a concise evidence-based explanation with its source. Call the score a teaching rule, not a trained prediction or decision."""

model = local_model()


# COPIED FROM LESSON 06: the final agent uses native Pydantic AI capabilities.
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(
    model,
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    capabilities=[
        LocalWorkspace("."),
        Skills("skills"),
        MCP(local=server_file, id="northstar-finance"),
        Memory(FileStore(".agent-memory")),
        Thinking(effort="low"),
    ],
)
finance_specialist = Agent(model, instructions=FINANCE_INSTRUCTIONS)
research_specialist = Agent(model, instructions=RETENTION_INSTRUCTIONS)


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
