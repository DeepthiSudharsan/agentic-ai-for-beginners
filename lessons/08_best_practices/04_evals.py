"""Lesson 08.4: lesson 08.3 plus trajectory-aware evaluations."""
import json
import os
import re
from pathlib import Path

os.environ["LANGFUSE_TRACE_GENERATION"] = "1"

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


# COPIED FROM LESSON 08.3: the complete guarded assistant remains.
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
scrutiny_agent = Agent(local_model(), instructions="You are a finance safety reviewer. Return JSON only with allow and reason. Allow Northstar finance, product, retention, and data-quality questions. Block off-topic, unethical, fraudulent, discriminatory, violent, or investment-advice requests.")


def redact_pii(question: str) -> str:
    if AnalyzerEngine is not None:
        results = AnalyzerEngine().analyze(text=question, language="en")
        return AnonymizerEngine().anonymize(text=question, analyzer_results=results).text
    question = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", question)
    return re.sub(r"\b\d{10}\b", "[PHONE]", question)


@observe(name="request_scrutiny", as_type="guardrail")
def scrutinize(question: str) -> tuple[bool, str]:
    try:
        result = json.loads(scrutiny_agent.run_sync(question).output)
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
        return agent.run_sync(sanitized, message_history=message_history, toolsets=[mcp_tools]), None


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
