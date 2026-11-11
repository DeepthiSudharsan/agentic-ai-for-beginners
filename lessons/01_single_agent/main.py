import os
import sys
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent

from shared.cli import chat
from shared.model import local_model


# The starting point: one agent and one instruction.
agent = Agent(
    local_model(),
    instructions="You are Finley, a friendly beginner finance tutor. Explain concepts simply.",
)


if __name__ == "__main__":
    chat(agent)
