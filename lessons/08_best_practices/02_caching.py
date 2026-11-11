"""Lesson 08.2: lesson 08.1 plus safe tool-result caching."""
import os
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

os.environ["LANGFUSE_TRACE_GENERATION"] = "1"
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, MCP, Thinking
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from shared.data import facts_as_text, lookup_customer, lookup_financial_metric, lookup_product_policy, operating_margin, retention_risk
from shared.model import local_model

try:
    from langfuse import get_client, observe, propagate_attributes
except ImportError:
    get_client = None
    def observe(*args, **kwargs):
        return lambda function: function
    def propagate_attributes(**kwargs):
        from contextlib import nullcontext
        return nullcontext()


# COPIED FROM LESSON 07 and LESSON 08.1: the full traced assistant remains.
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(local_model(), instructions=f"You are Finley, a finance QA assistant. Answer only from these facts. If data is missing, say so.\n\n{facts_as_text()}", capabilities=[LocalWorkspace("."), Skills("skills"), MCP(local=server_file, id="northstar-finance"), Memory(FileStore(".agent-memory")), Thinking(effort="low")])
finance_specialist = Agent(local_model(), instructions=f"You are a bank financial analyst. Use these facts:\n{facts_as_text()}")
research_specialist = Agent(local_model(), instructions=f"You are a customer-retention analyst. Use these facts:\n{facts_as_text()}")


@agent.tool_plain
@observe(name="ask_finance_specialist", as_type="tool")
def ask_finance_specialist(question: str) -> str:
    return finance_specialist.run_sync(question).output


@agent.tool_plain
@observe(name="ask_research_specialist", as_type="tool")
def ask_research_specialist(question: str) -> str:
    return research_specialist.run_sync(question).output


@agent.tool_plain
@observe(name="lookup_metric", as_type="tool")
def lookup_metric(metric: str, period: str) -> str:
    return cached_metric(metric, period)


@lru_cache(maxsize=64)
def cached_metric(metric: str, period: str) -> str:
    """Cache deterministic read-only lookups using metric and period as the key."""
    return lookup_financial_metric(metric, period)


@agent.tool_plain
@observe(name="calculate_net_income_margin", as_type="tool")
def calculate_net_income_margin(period: str) -> str:
    return operating_margin(period)


@agent.tool_plain
@observe(name="lookup_product", as_type="tool")
def lookup_product(product: str) -> str:
    return lookup_product_policy(product)


@agent.tool_plain
@observe(name="lookup_customer_record", as_type="tool")
def lookup_customer_record(customer_id: str) -> str:
    return lookup_customer(customer_id)


@agent.tool_plain
@observe(name="calculate_retention_risk", as_type="tool")
def calculate_retention_risk(customer_id: str) -> str:
    return retention_risk(customer_id)


@observe(name="finley_agent", as_type="agent")
def run_agent(question: str, message_history: list):
    with propagate_attributes(session_id="beginner-finance-cli", user_id="course-student", tags=["agentic-ai-course", "finance-qa"], metadata={"lesson": "08.2", "cache_version": "finance-v1"}):
        return agent.run_sync(question, message_history=message_history)


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
    print(f"Metric cache: {cached_metric.cache_info()}")


if __name__ == "__main__":
    chat()
