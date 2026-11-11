"""Lesson 08.6: monitor the evaluated assistant and publish trace scores."""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

previous = importlib.import_module("lessons.08_best_practices.05_llm_judge")

try:
    from langfuse import get_client, propagate_attributes
except ImportError:
    get_client = None
    def propagate_attributes(**kwargs):
        from contextlib import nullcontext
        return nullcontext()


# COPIED/REUSED FROM LESSON 08.5: the same cases and judge results are monitored.
def monitor_results(results: list[dict]) -> dict:
    total = len(results)
    summary = {
        "cases": total,
        "answer_correctness": sum(item["llm_judge"].get("correct", 0) for item in results) / total,
        "groundedness": sum(item["llm_judge"].get("grounded", 0) for item in results) / total,
        "tool_choice": sum(item["llm_judge"].get("tool_choice", 0) for item in results) / total,
        "skill_choice": sum(item["llm_judge"].get("skill_choice", 0) for item in results) / total,
        "safety": sum(item["llm_judge"].get("safety", 0) for item in results) / total,
    }
    return summary


def run_monitoring() -> None:
    cases = json.loads((Path(__file__).parents[2] / "data" / "eval_cases.json").read_text())
    results = [previous.judge_case(case, previous.run_agent_case(case)[0]) for case in cases]
    summary = monitor_results(results)
    Path("agent_eval_results.json").write_text(json.dumps({"summary": summary, "cases": results}, indent=2))
    print(json.dumps(summary, indent=2))

    if get_client is not None:
        langfuse = get_client()
        with propagate_attributes(session_id="evaluation-monitoring", tags=["agentic-ai-course", "finance-qa-evals"], metadata={"lesson": "08.6"}):
            with langfuse.start_as_current_observation(as_type="evaluator", name="finance-qa-evaluation"):
                for name, value in summary.items():
                    if name != "cases":
                        langfuse.score_current_trace(name=name, value=float(value), data_type="NUMERIC")
                print("Langfuse trace:", langfuse.get_trace_url())
        langfuse.flush()
    else:
        print("Install langfuse and configure its environment variables to publish this evaluation trace.")


if __name__ == "__main__":
    run_monitoring()
