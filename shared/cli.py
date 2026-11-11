import logging
import warnings

warnings.filterwarnings("ignore", message="authlib.jose module is deprecated")
logging.getLogger("fastmcp").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)

from pydantic_ai import Agent


async def show_activity(_context, events) -> None:
    """Print only useful live events while Pydantic AI runs the agent."""
    async for event in events:
        if not event.__class__.__name__.endswith("ToolCallEvent"):
            continue
        if event.__class__.__name__ == "OutputToolCallEvent":
            continue
        part = getattr(event, "part", None)
        name = getattr(part, "tool_name", "unknown tool")
        kind = getattr(part, "tool_kind", None)
        if kind == "mcp_server" or str(name).startswith("mcp_server:"):
            label = "MCP"
        elif name == "load_capability" or "skill" in str(name).lower() or "capability" in str(name).lower():
            label = "skill/capability"
        else:
            label = "tool"
        print(f"  [agent] invoking {label}: {name}", flush=True)


def chat(agent: Agent, toolsets: list | None = None, runner=None) -> None:
    """Run a real multi-turn terminal chat.

    Pydantic AI returns the complete conversation for a run. We pass that
    history into the next run so the next question can refer to earlier turns.
    """
    message_history = []
    print("Type a question, or type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return
        if question:
            try:
                if runner is None:
                    result = agent.run_sync(
                        question,
                        message_history=message_history,
                        toolsets=toolsets,
                        event_stream_handler=show_activity,
                    )
                else:
                    result = runner(question, message_history)
                message_history = result.all_messages()
                print(f"Assistant: {result.output}\n")
            except Exception as error:
                print(f"The lesson could not complete the run: {error}\n")
