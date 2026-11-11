from pydantic_ai import Agent


def chat(agent: Agent, toolsets: list | None = None) -> None:
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
                result = agent.run_sync(
                    question,
                    message_history=message_history,
                    toolsets=toolsets,
                )
                message_history = result.all_messages()
                print(f"Assistant: {result.output}\n")
            except Exception as error:
                print(f"The lesson could not complete the run: {error}\n")
