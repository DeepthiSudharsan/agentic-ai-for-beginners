from pydantic_ai import Agent

from shared.cli import chat
from shared.data import facts_as_text, revenue_growth
from shared.model import local_model


# COPIED FROM LESSON 01: one agent and one instruction.
agent = Agent(
    local_model(),
    instructions=f"You are Finley, a finance QA assistant. Use only these facts:\n{facts_as_text()}",
)


# NEW IN THIS LESSON: a typed Python function becomes an agent tool.
@agent.tool_plain
def calculate_revenue_growth(from_period: str, to_period: str) -> str:
    """Compare revenue between two periods, such as Q1 2024 and Q2 2024."""
    return revenue_growth(from_period, to_period)


if __name__ == "__main__":
    chat(agent)
