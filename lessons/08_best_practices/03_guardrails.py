"""Lesson 08.3: lesson 08.2 plus PII and request-scrutiny guardrails."""
import json
import os
import re
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

facts = facts_as_text()
model = local_model()
ORCHESTRATOR_INSTRUCTIONS = f"""ROLE\nYou are Finley, the Northstar finance QA orchestrator.\n\nTASK\nChoose the smallest reliable tool, specialist, MCP tool, skill, or capability for the request.\n\nCONTEXT\n{facts}\n\nDELEGATION\nFinancial metrics go to the financial specialist; customer engagement and retention go to the retention specialist; product fees go to the product tool; two-period comparisons go to MCP.\n\nGUIDELINES\nUse evidence, state limitations, and do not provide consequential financial decisions.\n\nOUTPUT\nAnswer briefly with a source. Never expose internal routing or reasoning."""
FINANCE_INSTRUCTIONS = f"""ROLE\nYou are Northstar's financial-analysis specialist.\n\nTASK\nAnalyze quarterly metrics and calculations.\n\nCONTEXT\n{facts}\n\nOUTPUT\nReturn a concise evidence-based answer with its source."""
RETENTION_INSTRUCTIONS = f"""ROLE\nYou are Northstar's customer-retention specialist.\n\nTASK\nExplain observable engagement signals and illustrative retention risk.\n\nCONTEXT\n{facts}\n\nGUIDELINES\nThe score is a teaching rule, not a trained prediction or credit decision.\n\nOUTPUT\nReturn a concise evidence-based answer with its source."""
SCRUTINY_INSTRUCTIONS = """ROLE\nYou are Finley's finance-safety scrutiny agent.\n\nTASK\nDecide whether a sanitized request may reach the Northstar finance QA agent.\n\nALLOW\nNorthstar financials, products, customers, retention signals, data quality, and course questions.\n\nBLOCK\nOff-topic, investment or credit decisions, fraud, evasion, discrimination, violence, sexual content, and unethical actions.\n\nOUTPUT\nReturn only JSON: {\"allow\": true or false, \"reason\": \"short explanation\"}."""

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
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(model, instructions=ORCHESTRATOR_INSTRUCTIONS, capabilities=[LocalWorkspace("."), Skills("skills"), MCP(local=server_file, id="northstar-finance"), Memory(FileStore(".agent-memory")), Thinking(effort="low")])
finance_specialist = Agent(model, instructions=FINANCE_INSTRUCTIONS)
research_specialist = Agent(model, instructions=RETENTION_INSTRUCTIONS)


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
scrutiny_agent = Agent(model, instructions=SCRUTINY_INSTRUCTIONS)


@observe(name="request_scrutiny", as_type="guardrail")
def scrutinize(question: str) -> tuple[bool, str]:
    raw = scrutiny_agent.run_sync(question, event_stream_handler=show_activity).output
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
        return agent.run_sync(sanitized, message_history=message_history, event_stream_handler=show_activity), None


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
