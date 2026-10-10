"""
Tests for Module 01: Tool Registry & Safe Execution
"""
import sys
from pathlib import Path
import pytest

# Add module's src directory to sys.path (since '01_raw_loop' starts with a digit)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import ToolRegistry, calculate, run_command


def test_tool_registration():
    reg = ToolRegistry()

    @reg.register
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    schemas = reg.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "add"
    assert "a" in schemas[0]["function"]["parameters"]["properties"]
    assert "b" in schemas[0]["function"]["parameters"]["properties"]


def test_calculate_tool():
    assert calculate("2 + 2") == "4"
    assert "Error:" in calculate("import os; os.system('echo hi')")


def test_safe_execution_catches_errors():
    reg = ToolRegistry()

    @reg.register
    def flaky_tool(x: int):
        if x == 0:
            raise ZeroDivisionError("division by zero")
        return 100 // x

    res = reg.execute("flaky_tool", {"x": 0})
    assert "ERROR executing flaky_tool: ZeroDivisionError" in res


def test_nonexistent_tool_returns_error():
    reg = ToolRegistry()
    res = reg.execute("unknown_tool", {})
    assert "not found" in res

