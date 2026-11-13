"""A tiny local Hugging Face adapter for Pydantic AI.

It uses FunctionModel so students can see that Pydantic AI separates the
agent loop from the model provider. The model is downloaded once and then
runs locally. It is intentionally small, not production-grade.
"""

from __future__ import annotations

import json
import io
import os
import re
from contextlib import redirect_stderr
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TORCH_CPP_LOG_LEVEL", "ERROR")

import torch
from pydantic_ai import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, FunctionModel

MODEL_NAME = os.getenv("AGENT_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


def _model_is_cached() -> bool:
    """Use the local snapshot after the first successful Hugging Face download."""
    cache_root = os.getenv("HF_HUB_CACHE")
    if cache_root is None:
        cache_root = str(Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub")
    model_cache = Path(cache_root) / f"models--{MODEL_NAME.replace('/', '--')}" / "snapshots"
    return any(
        (snapshot / "config.json").exists()
        and any((snapshot / filename).exists() for filename in ("model.safetensors", "pytorch_model.bin"))
        for snapshot in model_cache.glob("*")
    )


@lru_cache(maxsize=1)
def _pipeline():
    cached = _model_is_cached()
    if cached:
        # Once the complete snapshot exists, avoid metadata checks and network
        # retries on every lesson run.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    with redirect_stderr(io.StringIO()):
        from transformers import pipeline

        return pipeline("text-generation", model=MODEL_NAME, device=-1, dtype=torch.float32)


def _message_text(messages: list[ModelMessage]) -> str:
    parts = []
    for message in messages:
        for part in message.parts:
            part_kind = getattr(part, "part_kind", "")
            if part_kind == "system-prompt":
                continue
            content = getattr(part, "content", None)
            if content:
                prefix = "TOOL RESULT: " if part_kind == "tool-return" else ""
                parts.append(prefix + str(content))
            if hasattr(part, "tool_name"):
                parts.append(f"Tool call: {part.tool_name} {getattr(part, 'args', '')}")
    return "\n".join(parts)


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tools = [
        {"name": tool.name, "description": tool.description, "parameters": tool.parameters_json_schema}
        for tool in info.function_tools
    ]
    if tools:
        tool_instruction = (
            "If a listed function is useful, output ONLY one JSON object in this exact shape: "
            '{"tool": "function_name", "args": {"argument": "value"}}. '
            "Otherwise answer in one or two short sentences."
        )
    else:
        tool_instruction = "There are no functions available. Answer the user directly in one or two short sentences. Do not output JSON, tool names, or analysis."
    prompt = (
        "ROLE\nYou are the local language model inside a Pydantic AI finance agent.\n\n"
        "TASK\nAnswer the user's latest request using only the conversation and available tool results.\n\n"
        "TOOL DECISION\n"
        f"{tool_instruction}\n"
        "After a function returns, answer the original request directly; never repeat tool calls or JSON.\n\n"
        f"AVAILABLE FUNCTIONS\n{json.dumps(tools)}\n\n"
        f"CONVERSATION\n{_message_text(messages)}\n\n"
        "OUTPUT FORMAT\nReturn one concise natural-language answer, or exactly one tool-call JSON object when a function is needed.\n\n"
        "ANSWER\n"
    )
    result = _pipeline()(prompt, max_new_tokens=180, do_sample=False, return_full_text=False)[0]["generated_text"].strip()
    call = _extract_json(result)
    tool_names = {tool.name for tool in info.function_tools}
    # Some very small models emit only the selected function name. Treat that
    # as a valid no-argument tool request instead of showing it to the learner.
    bare_tool_name = result.strip().strip("` .")
    if bare_tool_name in tool_names:
        return ModelResponse(parts=[ToolCallPart(tool_name=bare_tool_name, args={})])
    if call and call.get("tool") in tool_names:
        return ModelResponse(parts=[ToolCallPart(tool_name=call["tool"], args=call.get("args", {}))])
    tool_results = [
        str(getattr(part, "content", ""))
        for message in messages
        for part in message.parts
        if getattr(part, "part_kind", "") == "tool-return" and getattr(part, "content", "")
    ]
    if tool_results and re.search(r"no results|need more parameters|additional information|not enough", result, re.IGNORECASE):
        result = tool_results[-1]
    # Tiny instruction models sometimes echo a tool-shaped object even when no
    # tool is available. Keep that protocol noise out of the student-facing CLI.
    # The small model can append a second, malformed protocol attempt after a
    # useful sentence. Keep the natural-language answer and hide that protocol.
    for marker in ("Tool call:", '{"tool"', "```json"):
        if marker in result:
            result = result.split(marker, 1)[0]
    result = re.sub(r'\s*\{"tool".*', " ", result, flags=re.DOTALL)
    result = re.sub(r"\s+", " ", result).strip()
    return ModelResponse(parts=[TextPart(result)])


async def _stream_respond(messages: list[ModelMessage], info: AgentInfo):
    """Adapt the same local response for Pydantic AI's streamed event API."""
    response = _respond(messages, info)
    for index, part in enumerate(response.parts):
        if isinstance(part, TextPart):
            yield part.content
        elif isinstance(part, ToolCallPart):
            yield {
                index: DeltaToolCall(
                    name=part.tool_name,
                    json_args=part.args_as_json_str(),
                    tool_call_id=part.tool_call_id,
                )
            }

def local_model() -> FunctionModel:
    """Return the shared Pydantic AI model used in every lesson."""
    return FunctionModel(_respond, stream_function=_stream_respond, model_name=MODEL_NAME)
