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
import uuid
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
PERIOD_PATTERN = re.compile(r"\b(Q[1-4])(?:\s*(20\d{2}))?\b", re.IGNORECASE)


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
                if part_kind == "user-prompt":
                    parts.append("USER: " + str(content))
                elif part_kind in {"tool-return", "builtin-tool-return"}:
                    parts.append("TOOL RESULT: " + str(content))
                else:
                    parts.append("ASSISTANT: " + str(content))
            if hasattr(part, "tool_name"):
                parts.append(f"TOOL CALL: {part.tool_name} {getattr(part, 'args', '')}")
    return "\n".join(parts)


def _latest_user_prompt(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        for part in reversed(message.parts):
            if getattr(part, "part_kind", "") == "user-prompt":
                return str(getattr(part, "content", ""))
    return ""


def _period_from_conversation(messages: list[ModelMessage]) -> str | None:
    """Ground a tool period in the latest quarter mentioned by the user.

    This is deliberately open-ended: it does not enumerate valid dates. It only
    preserves an explicit year or inherits the year for a quarter-only follow-up.
    """
    user_prompts = [
        str(getattr(part, "content", ""))
        for message in messages
        for part in message.parts
        if getattr(part, "part_kind", "") == "user-prompt"
    ]
    if not user_prompts:
        return None

    latest_matches = list(PERIOD_PATTERN.finditer(user_prompts[-1]))
    if latest_matches:
        # In corrections such as "the previous quarter was Q2 2024; you are
        # giving Q3 2024", the first period is the requested one and the later
        # period is the value being corrected.
        latest = latest_matches[0]
        quarter, year = latest.group(1).upper(), latest.group(2)
    elif re.search(r"\b(previous|prior|last)\s+quarter\b", user_prompts[-1], re.IGNORECASE):
        previous_period = None
        for prompt in reversed(user_prompts[:-1]):
            matches = list(PERIOD_PATTERN.finditer(prompt))
            if matches and matches[-1].group(2):
                previous_period = matches[-1]
                break
        if previous_period is None:
            return None
        quarter_number = int(previous_period.group(1)[1:])
        year_number = int(previous_period.group(2))
        if quarter_number == 1:
            quarter_number, year_number = 4, year_number - 1
        else:
            quarter_number -= 1
        return f"Q{quarter_number} {year_number}"
    else:
        return None
    if year is None:
        for prompt in reversed(user_prompts[:-1]):
            previous_matches = list(PERIOD_PATTERN.finditer(prompt))
            if previous_matches and previous_matches[-1].group(2):
                year = previous_matches[-1].group(2)
                break
    return f"{quarter} {year}" if year else quarter


def _ground_period_argument(messages: list[ModelMessage], args: dict) -> dict:
    """Use the user's latest period when a tool call contains a period field."""
    if "period" not in args:
        return args
    period = _period_from_conversation(messages)
    if period is None:
        return args
    grounded_args = dict(args)
    grounded_args["period"] = period
    return grounded_args


def _correct_stale_finance_tool(messages: list[ModelMessage], tool_name: str, args: dict, tool_names: set[str]) -> tuple[str, dict]:
    """Prevent a stale finance tool from answering a different request."""
    latest_request = _latest_user_prompt(messages).lower()
    asks_for_revenue = "revenue" in latest_request
    asks_for_margin = "margin" in latest_request
    if asks_for_margin and "lookup_metric" in tool_name.lower():
        margin_tool = next((name for name in tool_names if "margin" in name.lower()), None)
        if margin_tool is not None:
            return margin_tool, {"period": args.get("period", "")}
    if asks_for_revenue and not asks_for_margin and "margin" in tool_name.lower():
        metric_tool = next((name for name in tool_names if name == "lookup_metric"), None)
        if metric_tool is not None:
            corrected_args = {"metric": "revenue", "period": args.get("period", "")}
            return metric_tool, corrected_args
    return tool_name, args


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

def _previous_result_for_current_turn(messages: list[ModelMessage], tool_name: str) -> str | None:
    """Return a tool result if this same tool already ran during this user turn."""
    latest_user_index = -1
    for index, message in enumerate(messages):
        if any(getattr(part, "part_kind", "") == "user-prompt" for part in message.parts):
            latest_user_index = index

    for message in messages[latest_user_index + 1:]:
        for part in message.parts:
            if (
                getattr(part, "part_kind", "") in {"tool-return", "builtin-tool-return"}
                and (getattr(part, "tool_name", "") == tool_name or not getattr(part, "tool_name", ""))
            ):
                return str(getattr(part, "content", ""))

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
        "CONVERSATION\n"
        "Read the transcript in order. The latest user message is the current request. "
        "Preserve explicit values from that latest request, including corrections.\n"
        f"{_message_text(messages)}\n\n"
        f"LATEST USER REQUEST\n{_latest_user_prompt(messages)}\n\n"
        "OUTPUT FORMAT\nReturn one concise natural-language answer, or exactly one tool-call JSON object when a function is needed. Do not output special end markers such as [END_OF_CONVERSATION], <|endoftext|>, or <|im_end|>.\n\n"
        "ANSWER\n"
    )
    result = _pipeline()(prompt, max_new_tokens=180, do_sample=False, return_full_text=False)[0]["generated_text"].strip()
    call = _extract_json(result)
    tool_names = {tool.name for tool in info.function_tools}
    for tool_name in tool_names:
        previous_result = _previous_result_for_current_turn(messages, tool_name)
        if previous_result is not None and tool_name in result:
            return ModelResponse(parts=[TextPart(previous_result)])
    # Some very small models emit only the selected function name. Treat that
    # as a valid no-argument tool request instead of showing it to the learner.
    bare_tool_name = result.strip().strip("` .")
    if bare_tool_name in tool_names:
        previous_result = _previous_result_for_current_turn(messages, bare_tool_name)
        if previous_result is not None:
            return ModelResponse(parts=[TextPart(previous_result)])
        return ModelResponse(parts=[ToolCallPart(tool_name=bare_tool_name, args={}, tool_call_id=f"local_{uuid.uuid4().hex}")])
    if call and call.get("tool") in tool_names:
        tool_name, args = _correct_stale_finance_tool(messages, call["tool"], call.get("args", {}), tool_names)
        previous_result = _previous_result_for_current_turn(messages, tool_name)
        if previous_result is not None:
            return ModelResponse(parts=[TextPart(previous_result)])
        args = _ground_period_argument(messages, args)
        return ModelResponse(parts=[ToolCallPart(tool_name=tool_name, args=args, tool_call_id=f"local_{uuid.uuid4().hex}")])
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
    for marker in ("Tool call:", '{"tool"', "```json", "[END_OF_CONVERSATION]", "<|endoftext|>", "<|im_end|>"):
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
