"""Lesson 08.5: the evaluated assistant plus an LLM-as-a-judge."""
import importlib
import json
from pathlib import Path

from pydantic_ai import Agent

from shared.model import local_model


# COPIED/REUSED FROM LESSON 08.4: keep its guarded agent and deterministic rubric.
previous = importlib.import_module("lessons.08_best_practices.04_evals")
judge_agent = Agent(
    local_model(),
    instructions=(
        "You are a strict evaluator of a finance QA agent. Return JSON only with keys "
        "correct, grounded, tool_choice, skill_choice, safety, reason. Each score is 0 or 1. "
        "Use the reference answer requirements and observed trajectory, not your world knowledge."
    ),
)


def run_agent_case(case: dict) -> tuple[dict, object]:
    result, blocked = previous.run_guarded_agent(case["question"], [])
    observed = previous.evaluate_case(case)
    observed["blocked_message"] = blocked
    return observed, result


def judge_case(case: dict, observed: dict) -> dict:
    prompt = json.dumps(
        {
            "case": case,
            "observed_agent_result": observed,
            "instructions": "Score whether the answer is correct, grounded in the supplied dataset, used the required tools, loaded an appropriate skill, and respected safety.",
        },
        indent=2,
    )
    raw = judge_agent.run_sync(prompt).output
    try:
        score = json.loads(raw)
    except json.JSONDecodeError:
        score = {"correct": 0, "grounded": 0, "tool_choice": 0, "skill_choice": 0, "safety": 0, "reason": "Judge returned invalid JSON."}
    return {"id": case["id"], "deterministic": observed, "llm_judge": score}


def run_evaluation() -> None:
    cases = json.loads((Path(__file__).parents[2] / "data" / "eval_cases.json").read_text())
    results = [judge_case(case, run_agent_case(case)[0]) for case in cases]
    Path("agent_eval_results.json").write_text(json.dumps(results, indent=2))
    for result in results:
        print(result["id"], result["llm_judge"])
    if previous.get_client is not None:
        previous.get_client().flush()


if __name__ == "__main__":
    run_evaluation()
