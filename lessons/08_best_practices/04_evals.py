"""Lesson 08.4: lesson 08.3 plus trajectory-aware evaluations."""
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
from shared.prompts import finance_specialist_instructions, finley_instructions, retention_specialist_instructions, scrutiny_instructions

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


# COPIED FROM LESSON 08.3: the complete guarded assistant remains.
server_file = Path(__file__).parents[1] / "04_mcp" / "server.py"
agent = Agent(local_model(), instructions=finley_instructions(facts_as_text(), end_to_end=True), capabilities=[LocalWorkspace("."), Skills("skills"), MCP(local=server_file, id="northstar-finance"), Memory(FileStore(".agent-memory")), Thinking(effort="low")])
finance_specialist = Agent(local_model(), instructions=finance_specialist_instructions(facts_as_text()))
research_specialist = Agent(local_model(), instructions=retention_specialist_instructions(facts_as_text()))


@agent.tool_plain
@observe(name="ask_finance_specialist", as_type="tool")
async def ask_finance_specialist(question: str) -> str:
    result = await finance_specialist.run(question)
    return result.output


@agent.tool_plain
@observe(name="ask_research_specialist", as_type="tool")
async def ask_research_specialist(question: str) -> str:
    result = await research_specialist.run(question)
    return result.output


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


@agent.tool_plain
@observe(name="list_high_retention_risk_customers", as_type="tool")
def list_high_retention_risk_customers(customer_id: str = "") -> str:
    """List all sample customers with a high illustrative retention-risk score."""
    return high_retention_risk_customers(customer_id)


scrutiny_agent = Agent(local_model(), instructions=scrutiny_instructions())


def redact_pii(question: str) -> str:
    if AnalyzerEngine is not None:
        results = AnalyzerEngine().analyze(text=question, language="en")
        return AnonymizerEngine().anonymize(text=question, analyzer_results=results).text
    question = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", question)
    return re.sub(r"\b\d{10}\b", "[PHONE]", question)


@observe(name="request_scrutiny", as_type="guardrail")
def scrutinize(question: str) -> tuple[bool, str]:
    try:
        result = json.loads(scrutiny_agent.run_sync(question, event_stream_handler=show_activity).output)
        return bool(result.get("allow")), str(result.get("reason", ""))
    except json.JSONDecodeError:
        return False, "Safety reviewer returned invalid JSON."


@observe(name="finley_agent", as_type="agent")
def run_guarded_agent(question: str, message_history: list):
    sanitized = redact_pii(question)
    allowed, reason = scrutinize(sanitized)
    if not allowed:
        return None, f"Request blocked by the finance safety reviewer: {reason}"
    with propagate_attributes(session_id="evaluation-run", tags=["agentic-ai-course", "evaluation"], metadata={"lesson": "08.4"}):
        return agent.run_sync(sanitized, message_history=message_history, event_stream_handler=show_activity), None


def tool_names(result) -> list[str]:
    names = []
    for message in result.all_messages():
        for part in message.parts:
            if hasattr(part, "tool_name"):
                names.append(part.tool_name)
    return names


def skill_names(result) -> list[str]:
    names = []
    for message in result.all_messages():
        for part in message.parts:
            if getattr(part, "tool_name", None) != "load_capability":
                continue
            args = getattr(part, "args", {})
            if isinstance(args, dict):
                name = args.get("name") or args.get("capability")
                if name:
                    names.append(str(name))
    return names


def evaluate_case(case: dict) -> dict:
    result, blocked = run_guarded_agent(case["question"], [])
    if result is None:
        answer = blocked or ""
        actual_tools = []
        actual_skills = []
    else:
        answer = str(result.output)
        actual_tools = tool_names(result)
        actual_skills = skill_names(result)
    answer_lower = answer.lower()
    contains_expected = all(item.lower() in answer_lower for item in case["expected_answer_contains"])
    tools_ok = all(tool in actual_tools for tool in case["required_tools"])
    blocked_ok = (result is None) == case["should_be_blocked"]
    return {
        "id": case["id"],
        "correctness": int(contains_expected),
        "grounded": int(contains_expected or result is None),
        "tool_choice": int(tools_ok),
        "skill_choice": int(all(skill in actual_skills for skill in case["required_skills"])),
        "safety": int(blocked_ok),
        "tools_seen": actual_tools,
        "skills_seen": actual_skills,
        "answer": answer,
    }


def run_evaluation() -> None:
    cases = json.loads((Path(__file__).parents[2] / "data" / "eval_cases.json").read_text())
    results = [evaluate_case(case) for case in cases]
    Path("agent_eval_results.json").write_text(json.dumps(results, indent=2))
    for result in results:
        print(result["id"], result["correctness"], result["grounded"], result["tool_choice"], result["safety"])
    if get_client is not None:
        get_client().flush()


if __name__ == "__main__":
    run_evaluation()
