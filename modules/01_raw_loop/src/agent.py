"""
Module 01: The Raw Loop (Zero-Framework ReAct).
Grounded in open-source reference implementations:
- SWE-agent/mini-swe-agent (Minimal stateful loop, output truncation, safety boundaries)
- huggingface/smolagents (Dynamic tool schema discovery & serialization)
- anthropics/claude-cookbooks (Closed-loop tool error observations and recovery)
"""
from __future__ import annotations

import os
import json
from typing import Any, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from shared.console import agent_console
from shared.config import settings
from .tools import registry, ToolRegistry

load_dotenv()

DEFAULT_MAX_TURNS: int = 10


class RawAgent:
    """
    Pure Python ReAct agent without external framework abstractions.
    Enforces turn budgets, schema casting, repetitive loop detection,
    and closed-loop observation recovery.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        tools: Optional[ToolRegistry] = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        verbose: bool = True,
        provider: Optional[str] = None,
    ):
        self.tools = tools or registry
        self.max_turns = max_turns
        self.verbose = verbose

        # Resolve client and model strictly from environment variables via Settings
        if base_url and api_key:
            self.model = model or os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL")
            self.client = OpenAI(base_url=base_url, api_key=api_key)
            return

        client, cfg = settings.get_client(preferred_provider=provider)
        self.client = client
        self.model = model or cfg.model

    def _dispatch_tool(self, call: Any, is_loop: bool) -> str:
        """
        Execute single tool call with loop guard and closed-loop JSON recovery.
        Flattens execution into linear guard clauses.
        """
        func_name = call.function.name
        func_args_raw = call.function.arguments

        if is_loop:
            return (
                f"WARNING: Identical tool call '{func_name}' repeated with arguments {func_args_raw}. "
                "You appear to be in a loop. Re-evaluate your strategy or choose an alternate tool."
            )

        try:
            args = json.loads(func_args_raw)
        except json.JSONDecodeError as err:
            return f"Error: Arguments were not valid JSON: {err}"

        return self.tools.execute(func_name, args)

    def run(self, user_prompt: str) -> str:
        """Execute the stateful ReAct while-loop until completion or turn exhaustion."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior systems engineer. "
                    "Use tools to discover facts and execute tasks.\n\n"
                    "Output Rules:\n"
                    "- Be concise, direct, and strictly factual.\n"
                    "- Never use emojis, cheerleading, or conversational filler.\n"
                    "- Present final results in structured technical markdown."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        schemas = self.tools.get_schemas()
        last_tool_call: Optional[Tuple[str, str]] = None

        for turn in range(1, self.max_turns + 1):
            if self.verbose:
                agent_console.print_turn_start(turn, self.max_turns)

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=schemas if schemas else None,
                )
            except Exception as e:
                err_msg = f"Model API Error: {type(e).__name__} - {e}"
                if self.verbose:
                    agent_console.print_error(err_msg)
                return err_msg

            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))

            # Guard clause: no tool calls indicates final answer generated
            if not message.tool_calls:
                if self.verbose:
                    agent_console.print_completed()
                return message.content or "[Empty response]"

            # Execute tool invocations
            for call in message.tool_calls:
                func_name = call.function.name
                func_args_raw = call.function.arguments

                if self.verbose:
                    agent_console.print_tool_call(func_name, func_args_raw)

                # Repetitive loop detection (mini-swe-agent pattern)
                current_call = (func_name, func_args_raw.strip())
                is_loop = (current_call == last_tool_call)
                last_tool_call = current_call

                result = self._dispatch_tool(call, is_loop=is_loop)

                if self.verbose:
                    agent_console.print_observation(result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

        return "Error: max turns reached without a final answer"


if __name__ == "__main__":
    agent = RawAgent()
    task = "Calculate 144 * 12 + 55, and check what folders exist in the current directory."
    agent_console.print_task(task)
    answer = agent.run(task)
    agent_console.print_solution(answer)