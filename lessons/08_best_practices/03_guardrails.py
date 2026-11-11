"""Lesson 08.3: lesson 08.2 plus PII and request-scrutiny guardrails."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

os.environ["LANGFUSE_TRACE_GENERATION"] = "1"
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace, Thinking
from pydantic_ai.mcp import MCPToolset
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

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:
    AnalyzerEngine = AnonymizerEngine = None


# COPIED FROM LESSON 08.2: the complete traced and cached assistant remains.
agent = Agent(local_model(), instructions=f"You are Finley, a finance QA assistant. Answer only from these facts. If data is missing, say so.\n\n{facts_as_text()}", capabilities=[LocalWorkspace("."), Skills("skills"), Memory(FileStore(".agent-memory")), Thinking(effort="low")])
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


server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
mcp_tools = MCPToolset(StdioTransport(command="python", args=[str(server_file)]))


# NEW IN THIS LESSON: PII is redacted before any LLM scrutiny or agent call.
@observe(name="pii_redaction", as_type="guardrail")
def redact_pii(question: str) -> tuple[str, list[str]]:
    if AnalyzerEngine is not None:
        results = AnalyzerEngine().analyze(text=question, language="en")
        redacted = AnonymizerEngine().anonymize(text=question, analyzer_results=results).text
        return redacted, [item.entity_type for item in results]
    redacted = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", question)
    redacted = re.sub(r"\b\d{10}\b", "[PHONE]", redacted)
    return redacted, []


# NEW IN THIS LESSON: a second local agent scrutinizes the sanitized request.
scrutiny_agent = Agent(local_model(), instructions=(
    "You are Finley's request-safety reviewer. Return JSON only: "
    '{"allow": true or false, "reason": "short reason"}. '
    "Allow questions about Northstar bank financials, products, customer retention signals, and data quality. "
    "Block off-topic requests, investment or credit decisions, fraud/evasion, discrimination, violence, sexual content, and requests for unethical actions."
))


@observe(name="request_scrutiny", as_type="guardrail")
def scrutinize(question: str) -> tuple[bool, str]:
    raw = scrutiny_agent.run_sync(question).output
    try:
        decision = json.loads(raw)
        return bool(decision.get("allow")), str(decision.get("reason", "No reason supplied."))
    except json.JSONDecodeError:
        return False, "The scrutiny agent did not return a valid safety decision."


@observe(name="finley_agent", as_type="agent")
def run_guarded_agent(question: str, message_history: list):
    sanitized, entities = redact_pii(question)
    allowed, reason = scrutinize(sanitized)
    if not allowed:
        return None, f"Request blocked by the finance safety reviewer: {reason}"
    with propagate_attributes(session_id="beginner-finance-cli", user_id="course-student", tags=["agentic-ai-course", "finance-qa"], metadata={"lesson": "08.3", "pii_entities_redacted": entities}):
        return agent.run_sync(sanitized, message_history=message_history, toolsets=[mcp_tools]), None


def chat() -> None:
    message_history = []
    print("Type a question, or type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            result, blocked_message = run_guarded_agent(question, message_history)
            if result is None:
                print(f"Assistant: {blocked_message}\n")
            else:
                message_history = result.all_messages()
                print(f"Assistant: {result.output}\n")
    if get_client is not None:
        get_client().flush()


if __name__ == "__main__":
    chat()
