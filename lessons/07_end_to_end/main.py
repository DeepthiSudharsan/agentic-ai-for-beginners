from pathlib import Path

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, Thinking
from pydantic_ai.mcp import MCPToolset
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import chat
from shared.data import facts_as_text, revenue_growth
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
finance_specialist = Agent(local_model(), instructions="Explain finance calculations simply.")
research_specialist = Agent(local_model(), instructions="Summarize evidence and say when evidence is missing.")


@agent.tool_plain
def ask_finance_specialist(question: str) -> str:
    return finance_specialist.run_sync(question).output


@agent.tool_plain
def ask_research_specialist(question: str) -> str:
    return research_specialist.run_sync(question).output


@agent.tool_plain
def calculate_revenue_growth(from_period: str, to_period: str) -> str:
    """Calculate revenue change between two periods."""
    return revenue_growth(from_period, to_period)


server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
mcp_tools = MCPToolset(StdioTransport(command="python", args=[str(server_file)]))


if __name__ == "__main__":
    chat(agent, toolsets=[mcp_tools])
