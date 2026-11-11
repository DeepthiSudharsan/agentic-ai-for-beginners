from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model


# COPIED FROM LESSON 02: the original agent and deterministic tool remain.
agent = Agent(
    local_model(),
    instructions=f"You are Finley, a finance QA assistant. Use only these facts:\n{facts_as_text()}",
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


# NEW IN THIS LESSON: two specialist agents.
finance_specialist = Agent(
    local_model(),
    instructions=f"You are a bank financial analyst. Explain reported metrics and calculations simply. Use these facts:\n{facts_as_text()}",
)
research_specialist = Agent(
    local_model(),
    instructions=f"You are a customer-retention analyst. Explain observed engagement signals carefully. Use these facts:\n{facts_as_text()}",
)


# NEW IN THIS LESSON: the orchestrator chooses the specialist through tools.
@agent.tool_plain
def ask_finance_specialist(question: str) -> str:
    """Use for finance concepts and calculations."""
    return finance_specialist.run_sync(question).output


@agent.tool_plain
def ask_research_specialist(question: str) -> str:
    """Use for summaries and evidence questions."""
    return research_specialist.run_sync(question).output


# NEW IN THIS LESSON: customer tools support the retention specialist.
@agent.tool_plain
def lookup_customer_record(customer_id: str) -> str:
    """Look up one sample customer by ID."""
    return lookup_customer(customer_id)


@agent.tool_plain
def calculate_retention_risk(customer_id: str) -> str:
    """Explain the illustrative retention-risk rule for one sample customer."""
    return retention_risk(customer_id)


if __name__ == "__main__":
    chat(agent)
