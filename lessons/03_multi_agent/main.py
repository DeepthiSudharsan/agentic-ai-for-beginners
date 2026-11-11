from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, revenue_growth
from shared.model import local_model


# COPIED FROM LESSON 02: the original agent and deterministic tool remain.
agent = Agent(
    local_model(),
    instructions=f"You are Finley, a finance QA assistant. Use only these facts:\n{facts_as_text()}",
)


@agent.tool_plain
def calculate_revenue_growth(from_period: str, to_period: str) -> str:
    """Compare revenue between two periods."""
    return revenue_growth(from_period, to_period)


# NEW IN THIS LESSON: two specialist agents.
finance_specialist = Agent(
    local_model(),
    instructions="You are a finance specialist. Explain calculations and finance terms simply.",
)
research_specialist = Agent(
    local_model(),
    instructions="You are a research specialist. Summarize evidence and say when evidence is missing.",
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


if __name__ == "__main__":
    chat(agent)
