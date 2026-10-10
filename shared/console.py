"""
Unified Terminal Formatting & Tracing UI for Agentic Systems.
Reused across Module 01 through Module 08.
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from typing import Any

# Custom high-contrast theme
custom_theme = Theme({
    "turn": "bold cyan",
    "tool_name": "bold yellow",
    "tool_args": "dim",
    "obs": "bold green",
    "error": "bold red",
    "completed": "bold green",
})


class AgentConsole:
    """Production-grade terminal presentation layer for agent traces and outputs."""

    def __init__(self):
        self._console = Console(theme=custom_theme)

    def print_task(self, task: str, title: str = "User Task") -> None:
        """Display the initial incoming prompt inside a styled panel."""
        self._console.print(Panel(task, title=f"[bold blue]{title}[/bold blue]", border_style="blue"))

    def print_turn_start(self, turn: int, max_turns: int) -> None:
        """Log turn progression."""
        self._console.print(f"\n[turn][Turn {turn}/{max_turns}][/turn] [dim]Waiting for model...[/dim]")

    def print_tool_call(self, tool_name: str, arguments: Any) -> None:
        """Log tool invocation."""
        self._console.print(f"  [tool_name]-> Tool Call:[/tool_name] [yellow]{tool_name}[/yellow]([tool_args]{arguments}[/tool_args])")

    def print_observation(self, observation: str, max_chars: int = 150) -> None:
        """Log tool observation with single-line truncation."""
        single_line = observation.replace("\n", " ").strip()
        if len(single_line) > max_chars:
            single_line = single_line[:max_chars] + "..."
        self._console.print(f"  [obs]<- Observation:[/obs] [dim]{single_line}[/dim]")

    def print_completed(self) -> None:
        """Log agent completion event."""
        self._console.print("[completed][Completed][/completed] [dim]Final answer generated.[/dim]")

    def print_solution(self, markdown_text: str, title: str = "Agent Solution") -> None:
        """Render final markdown answer inside an aligned terminal box."""
        self._console.print(
            Panel(
                Markdown(markdown_text),
                title=f"[bold green]{title}[/bold green]",
                border_style="green",
            )
        )

    def print_error(self, message: str, title: str = "Error") -> None:
        """Render error message inside a red panel."""
        self._console.print(Panel(message, title=f"[bold red]{title}[/bold red]", border_style="red"))


# Global singleton instance
agent_console = AgentConsole()
