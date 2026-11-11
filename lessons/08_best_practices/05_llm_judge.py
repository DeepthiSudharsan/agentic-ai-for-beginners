"""A local-model judge for a single answer.

This is deliberately small: the rubric is visible, and the judge returns a
short JSON-like score that a human can inspect. For a serious evaluator, keep
the reference answers and tool traces beside each sample.
"""
import json

from shared.model import local_model
from pydantic_ai import Agent

judge = Agent(local_model(), instructions="You are an evaluator. Return JSON only with keys correct, grounded, reason. Score correct and grounded from 0 to 1.")

def judge_answer(question: str, answer: str, evidence: str) -> str:
    prompt = f"Question: {question}\nAnswer: {answer}\nEvidence: {evidence}"
    return judge.run_sync(prompt).output

if __name__ == "__main__":
    result = judge_answer("What was Q2 revenue?", "$12.5m", "Q2 2024 revenue was $12.5m")
    print(result)
    try:
        print("Parsed judge result:", json.loads(result))
    except json.JSONDecodeError:
        print("The local model did not return valid JSON; inspect the raw answer and retry.")
