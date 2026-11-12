"""Lesson 08.1: the complete assistant plus real Langfuse observations."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

os.environ["LANGFUSE_TRACE_GENERATION"] = "1"
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, MCP, Thinking
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.cli import show_activity
from shared.data import facts_as_text, high_retention_risk_customers, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model
from shared.prompts import finance_specialist_instructions, finley_instructions, retention_specialist_instructions

try:
    from langfuse import get_client, observe, propagate_attributes
except ImportError:
    get_client = None

    def observe(*args, **kwargs):
        def decorator(function):
            return function
        return decorator

    class _NoTraceContext:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def propagate_attributes(**kwargs):
        return _NoTraceContext()


server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
# COPIED FROM LESSON 07: the complete Finley assistant remains here.
agent = Agent(
    local_model(),
    instructions=finley_instructions(facts_as_text(), end_to_end=True),
    capabilities=[LocalWorkspace("."), Skills("skills"), MCP(local=server_file, id="northstar-finance"), Memory(FileStore(".agent-memory")), Thinking(effort="low")],
)
finance_specialist = Agent(local_model(), instructions=finance_specialist_instructions(facts_as_text()))
research_specialist = Agent(local_model(), instructions=retention_specialist_instructions(facts_as_text()))


@agent.tool_plain
@observe(name="ask_finance_specialist", as_type="tool")
async def ask_finance_specialist(question: str) -> str:
    """Delegate quarterly financial metrics and calculations, not customer or policy questions."""
    result = await finance_specialist.run(question)
    return result.output


@agent.tool_plain
@observe(name="ask_research_specialist", as_type="tool")
async def ask_research_specialist(question: str) -> str:
    """Delegate customer engagement and retention questions, not financial calculations."""
    result = await research_specialist.run(question)
    return result.output


@agent.tool_plain
@observe(name="lookup_metric", as_type="tool")
def lookup_metric(metric: str, period: str) -> str:
    """Look up one reported metric for one quarter; use MCP for period comparisons."""
    return lookup_financial_metric(metric, period)


@agent.tool_plain
@observe(name="calculate_net_income_margin", as_type="tool")
def calculate_net_income_margin(period: str) -> str:
    """Calculate net income divided by revenue for one quarter."""
    return operating_margin(period)


@agent.tool_plain
@observe(name="lookup_product", as_type="tool")
def lookup_product(product: str) -> str:
    """Look up exact product fees, APR, and opening-deposit policy fields."""
    return lookup_product_policy(product)


@agent.tool_plain
@observe(name="lookup_customer_record", as_type="tool")
def lookup_customer_record(customer_id: str) -> str:
    """Look up one customer record by exact ID; do not use for aggregate lists."""
    return lookup_customer(customer_id)


@agent.tool_plain
@observe(name="calculate_retention_risk", as_type="tool")
def calculate_retention_risk(customer_id: str) -> str:
    """Calculate one customer's illustrative retention-risk rule, not a trained prediction."""
    return retention_risk(customer_id)


@agent.tool_plain
@observe(name="list_high_retention_risk_customers", as_type="tool")
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score; use for aggregate questions."""
    return high_retention_risk_customers(customer_id)


# NEW IN THIS LESSON: an agent observation is the parent of model/tool work.
@observe(name="finley_agent", as_type="agent")
def run_agent(question: str, message_history: list):
    with propagate_attributes(session_id="beginner-finance-cli", user_id="course-student", tags=["agentic-ai-course", "finance-qa"], metadata={"lesson": "08.1", "model": "local-huggingface"}):
        return agent.run_sync(question, message_history=message_history, event_stream_handler=show_activity)


def chat() -> None:
    message_history = []
    print("Type a question, or type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            result = run_agent(question, message_history)
            message_history = result.all_messages()
            print(f"Assistant: {result.output}\n")
    if get_client is not None:
        get_client().flush()


if __name__ == "__main__":
    chat()
