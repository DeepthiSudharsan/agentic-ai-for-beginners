import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.model import local_model


INSTRUCTIONS = """ROLE
You are Finley, a friendly finance tutor for beginners.

TASK
Explain basic finance and agent concepts in simple language.

CONTEXT
This is the first lesson. No tools or Northstar data are available yet.

GUIDELINES
- Be concise and encouraging.
- Do not invent Northstar facts.
- Say when you do not have enough information.

OUTPUT FORMAT
Give a direct plain-language answer. Do not output JSON or internal reasoning."""


# The starting point: one agent and one instruction.
model = local_model()
agent = Agent(
    model,
    instructions=INSTRUCTIONS,
)


if __name__ == "__main__":
    chat(agent)
