"""
Tests for Module 01: Tool Registry, Safe Execution & Sandboxed Bounds.
Grounded in mini-swe-agent and smolagents test patterns.
"""
import sys
from pathlib import Path
import pytest

# Add module's src and project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import ToolRegistry, calculate, run_command, read_file
from shared.config import settings, ProviderType


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


def test_read_file_truncation(tmp_path):
    test_file = tmp_path / "long_file.txt"
    test_file.write_text("\n".join([f"Line {i}" for i in range(100)]))
    
    content = read_file(str(test_file), max_lines=10)
    assert "Line 0" in content
    assert "Line 9" in content
    assert "[truncated: showing 10 of 100 lines]" in content


def test_run_command_safe_execution():
    output = run_command("echo 'hello agent'")
    assert "hello agent" in output.strip()


def test_settings_provider_resolution():
    cfg = settings.get_llm_config()
    assert cfg.provider in (
        ProviderType.GROQ,
        ProviderType.GEMINI,
        ProviderType.OPENROUTER,
        ProviderType.OLLAMA,
    )
