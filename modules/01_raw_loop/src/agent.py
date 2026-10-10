"""
Module 01: Raw ReAct Agent Loop
Write your own implementation here following modules/01_raw_loop/README.md.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from shared.console import agent_console
from .tools import registry, ToolRegistry

load_dotenv()


class RawAgent:
    def __init__(
        self,
        model: str = None,
        base_url: str = "https://api.groq.com/openai/v1",
        api_key: str = None,
        tools: ToolRegistry = None,
        max_turns: int = 10,
        verbose: bool = True,
    ):
        self.model = model or os.getenv("GROQ_MODEL")
        self.tools = tools or registry
        self.max_turns = max_turns
        self.verbose = verbose
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or os.getenv("GROQ_API_KEY"),
        )

    def run(self, user_prompt: str) -> str:
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

            # No tool calls means the LLM has synthesized its final answer
            if not message.tool_calls:
                if self.verbose:
                    agent_console.print_completed()
                return message.content or "[Empty response]"

            # Run each requested tool and append observation
            for call in message.tool_calls:
                func_name = call.function.name
                if self.verbose:
                    agent_console.print_tool_call(func_name, call.function.arguments)

                try:
                    args = json.loads(call.function.arguments)
                except json.JSONDecodeError as err:
                    result = f"Error: Arguments were not valid JSON: {err}"
                else:
                    result = self.tools.execute(func_name, args)

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