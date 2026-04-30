"""Rich CLI output formatting."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from lmx.classifier import TaskType
from lmx.recommender import Recommendation

_console = Console()


def format_recommendation(
    recommendations: List[Recommendation],
    task_type: TaskType,
    verbose: bool = False,
) -> Panel:
    """Format primary recommendation as a Rich panel."""

    if not recommendations:
        return Panel("[red]No recommendations found[/red]")

    primary = recommendations[0]

    header = Text()
    header.append("Task: ", style="bold dim")
    header.append(f"{task_type.value}\n", style="cyan")
    header.append("Recommended: ", style="bold green")
    header.append(f"{primary.model_id}", style="bold white")
    header.append(f" ({primary.provider})", style="dim")

    details = Text()
    cost_str = f"${primary.estimated_cost:.4f}" if primary.estimated_cost > 0 else "Free"
    details.append(f"\n  Cost: ", style="dim")
    details.append(f"~{cost_str}", style="yellow")
    details.append(
        f" (est. {primary.estimated_input_tokens:,}->{primary.estimated_output_tokens:,} tokens)\n",
        style="dim"
    )

    details.append("  Context: ", style="dim")
    details.append(f"{primary.context_window:,} tokens ", style="green")
    ok = primary.context_window >= 128000
    details.append("OK\n" if ok else "Limited\n", style="green" if ok else "yellow")

    details.append("  Quality: ", style="dim")
    quality_color = "green" if primary.quality_score >= 0.90 else "yellow" if primary.quality_score >= 0.80 else "red"
    details.append(f"{primary.quality_score:.0%}\n", style=quality_color)

    details.append("  Speed: ", style="dim")
    speed_color = "green" if primary.speed_score >= 0.90 else "yellow"
    details.append(f"{primary.speed_score:.0%}\n", style=speed_color)

    if primary.fallback_for:
        details.append("\n  Fallback queued: ", style="dim")
        details.append("Yes (if primary fails)\n", style="green")

    tips = _get_tip(task_type, primary, recommendations)
    if tips:
        details.append(f"\n  [dim]Tip:[/dim] {tips}", style="italic")

    return Panel(
        header + details,
        title="[bold]lmx[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )


def print_alternatives(recommendations: List[Recommendation]):
    """Print alternative recommendations as a table."""
    if len(recommendations) <= 1:
        return

    _console.print("\n[bold dim]Alternatives:[/bold dim]")
    alt_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    alt_table.add_column("#", style="dim", width=3)
    alt_table.add_column("Model", style="cyan")
    alt_table.add_column("Provider", style="blue")
    alt_table.add_column("Cost", justify="right", style="yellow")
    alt_table.add_column("Quality", justify="right", style="green")

    for i, alt in enumerate(recommendations[1:3], 2):
        alt_table.add_row(
            str(i),
            alt.model_id,
            alt.provider,
            f"${alt.estimated_cost:.4f}",
            f"{alt.quality_score:.0%}",
        )
    _console.print(alt_table)


def _get_tip(
    task_type: TaskType,
    primary: Recommendation,
    alternatives: List[Recommendation],
) -> str:
    """Generate contextual tips."""

    if task_type == TaskType.SUMMARIZATION and alternatives:
        cheapest = min(alternatives, key=lambda r: r.estimated_cost)
        if cheapest.estimated_cost < primary.estimated_cost / 10:
            return (
                f"For non-critical summaries, {cheapest.model_id} is "
                f"{primary.estimated_cost/cheapest.estimated_cost:.0f}x cheaper."
            )

    if task_type == TaskType.CODE and primary.quality_score < 0.95:
        return "For production code, test with GPT-4o or Claude 3.5 Sonnet first, then optimize cost."

    if task_type == TaskType.BATCH:
        return "Batch jobs are perfect for cheaper models. Test 3 samples before full run."

    if primary.estimated_cost > 0.10:
        return "This is an expensive request. Consider chunking input or using a cheaper model for first draft."

    return ""