"""
Module 01: Tool Registry & Safe Execution Engine
Write your own implementation here following modules/01_raw_loop/README.md.
"""

# TODO: Implement ToolRegistry and tools (calculate, run_command, read_file)

import inspect 
import re
import subprocess
from typing import Callable, get_type_hints 


TYPE_MAP = {
    str: "string", 
    int: "integer",
    float: "number", 
    bool: "boolean",
}

# Sandboxed execution boundaries (mini-swe-agent standard)
DEFAULT_MAX_LINES: int = 50
COMMAND_TIMEOUT_SECONDS: int = 10
MAX_OUTPUT_CHARS: int = 2000

class ToolRegistry:
    def __init__(self): 
        self._tools: dict[str, Callable] = {} 
    
    def register(self, func: Callable) -> None:
        self._tools[func.__name__] = func
        return func
    
    def get_schemas(self) -> list[dict]:
        schemas = []
        for name, func in self._tools.items():
            hints = get_type_hints(func)
            props, required = {}, []
            for pname, param in inspect.signature(func).parameters.items():
                p_type = TYPE_MAP.get(hints.get(pname), "string")
                props[pname] = {
                    "type": p_type,
                    "description": f"Parameter: {pname}",
                }
                if param.default is inspect.Parameter.empty:
                    required.append(pname)

            # OpenAI / Groq / Gemini / Ollama wire format:
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": inspect.getdoc(func) or f"Tool: {name}",
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required,
                    },
                },
            })
        return schemas

    def execute(self, tool_name: str, arguments: dict) -> str:
        if tool_name not in self._tools:
            return f"ERROR: Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}"
        
        try:
            return str(self._tools[tool_name](**arguments))
        except Exception as e:
            return f"ERROR executing {tool_name}: {type(e).__name__} - {e}"


# Shared registry instance
registry = ToolRegistry()


@registry.register
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression. Example: '144 * 12 + 5'."""
    # Only allow digits, spaces, and basic math symbols
    if not re.fullmatch(r"[0-9+\-*/().% ]+", expression):
        return "Error: only numbers and + - * / ( ) . % are allowed"
    return str(eval(expression, {"__builtins__": {}}))


@registry.register
def read_file(filepath: str, max_lines: int = DEFAULT_MAX_LINES) -> str:
    """Read the contents of a local file with line-based truncation."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"Error: file not found: {filepath}"

    result = "".join(lines[:max_lines])
    if len(lines) > max_lines:
        result += f"\n... [truncated: showing {max_lines} of {len(lines)} lines]"
    return result


@registry.register
def run_command(command: str) -> str:
    """Run a shell command locally with timeout and output truncation."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {COMMAND_TIMEOUT_SECONDS} seconds"

    output = proc.stdout + proc.stderr
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n... [truncated]"
    return output
