"""CLI entrypoint for lmx."""

import asyncio
import json
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from lmx.classifier import classify_task
from lmx.pricing import PricingCache
from lmx.recommender import Recommender
from lmx.preferences import PreferenceManager
from lmx.formatter import format_recommendation, print_alternatives
from lmx.providers import get_available_providers

console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# Root group
# ─────────────────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """lmx -- The smart model picker for LLMs."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Core: lmx "task" or lmx pick "task"
# ─────────────────────────────────────────────────────────────────────────────

@cli.command("pick")
@click.argument('task', nargs=-1, required=False)
@click.option('--budget', '-b', type=float, help='Max cost in USD')
@click.option('--code', '-c', is_flag=True, help='Code-specific task')
@click.option('--batch', is_flag=True, help='Batch job optimization')
@click.option('--models', '-m', help='Comma-separated model list to consider')
@click.option('--json', '-j', 'json_output', is_flag=True, help='JSON output')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def pick_cmd(ctx, task, budget, code, batch, models, json_output, verbose):
    """Pick the best model for your task."""
    # If no task given and no subcommand triggered, enter interactive
    if not task:
        _interactive_mode()
        return

    task_str = ' '.join(task)
    asyncio.run(_pick(task_str, budget, code, batch, models, json_output, verbose))


# Bare lmx "task" — routed to pick
@cli.command("main", hidden=True)
@click.argument('task', nargs=-1, required=True)
@click.option('--budget', '-b', type=float)
@click.option('--code', '-c', is_flag=True)
@click.option('--batch', is_flag=True)
@click.option('--models', '-m')
@click.option('--json', '-j', 'json_output', is_flag=True)
@click.option('--verbose', '-v', is_flag=True)
def main_cmd(task, budget, code, batch, models, json_output, verbose):
    """Pick the best model for your task."""
    task_str = ' '.join(task)
    asyncio.run(_pick(task_str, budget, code, batch, models, json_output, verbose))


# Register main as the default (no subcommand needed for bare task)
cli.add_command(main_cmd, name=None)


# ─────────────────────────────────────────────────────────────────────────────
# Subcommands
# ─────────────────────────────────────────────────────────────────────────────

@cli.command("interactive")
def interactive_cmd():
    """Interactive REPL mode."""
    _interactive_mode()


@cli.command("providers")
def providers_cmd():
    """List configured providers."""
    _providers_cmd()


@cli.command("history")
@click.option('--period', '-p', default='this-month')
def history_cmd(period):
    """View your usage history and spend."""
    _history_cmd(period)


@cli.command("list-models")
def list_models_cmd():
    """List all available models."""
    _list_models_cmd()


@cli.command("config")
@click.option('--edit', '-e', is_flag=True)
def config_cmd(edit):
    """View or edit configuration."""
    _config_cmd(edit)


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

async def _pick(
    task: str,
    budget: Optional[float],
    code: bool,
    batch: bool,
    models: Optional[str],
    json_output: bool,
    verbose: bool,
):
    """Core pick logic."""
    task_type = classify_task(task, code=code, batch=batch)

    providers = get_available_providers()
    if not providers:
        console.print(Panel(
            "[red]No API keys found.[/red]\n\n"
            "Set at least one key in your environment:\n"
            "  export OPENAI_API_KEY='sk-...'\n"
            "  export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "  export GROQ_API_KEY='gsk_...'\n"
            "  export TOGETHER_API_KEY='...'\n"
            "  export CEREBRAS_API_KEY='...'",
            title="lmx",
            border_style="red",
        ))
        raise click.ClickException("No API keys found")

    pricing = PricingCache()
    await pricing.refresh()

    prefs = PreferenceManager()
    recommender = Recommender(pricing, prefs)

    recommendations = await recommender.recommend(
        task=task,
        task_type=task_type,
        budget=budget or prefs.default_budget,
        providers=providers,
        model_filter=models.split(",") if models else None,
    )

    if not recommendations:
        console.print("[red]No suitable models found for your task and budget.[/red]")
        raise click.ClickException("No suitable models found")

    if json_output:
        console.print(json.dumps([r.to_dict() for r in recommendations], indent=2))
    else:
        output = format_recommendation(recommendations, task_type, verbose)
        console.print(output)
        print_alternatives(recommendations)

    prefs.log_usage(
        task=task,
        task_type=task_type.value,
        provider=recommendations[0].provider,
        model_id=recommendations[0].model_id,
        estimated_cost=recommendations[0].estimated_cost,
    )


def _interactive_mode():
    """Interactive REPL mode."""
    console.print(Panel(
        "[bold cyan]lmx[/bold cyan] -- Interactive Mode\n"
        "[dim]Type a task, or 'quit' to exit[/dim]",
        title="Welcome",
        border_style="cyan",
    ))

    while True:
        try:
            task = console.input("\n[bold green]lmx>[/bold green] ")
        except (EOFError, KeyboardInterrupt):
            break

        if task.lower() in ("quit", "exit", "q"):
            break

        if task.strip():
            asyncio.run(_pick(task, None, False, False, None, False, False))

    console.print("[dim]Goodbye![/dim]")


def _providers_cmd():
    providers = get_available_providers()
    table = Table(title="Configured Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Models", style="yellow")

    if not providers:
        console.print("[yellow]No providers configured.[/yellow]")
        console.print("[dim]Set API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, etc.[/dim]")
        return

    for name, provider in providers.items():
        table.add_row(name, "Active", str(len(provider.available_models)))

    console.print(table)


def _history_cmd(period: str):
    prefs = PreferenceManager()
    rows = prefs.get_history(limit=20)

    if not rows:
        console.print("[yellow]No usage history yet.[/yellow]")
        console.print("[dim]Run 'lmx pick \"your task\"' to get recommendations and build history.[/dim]")
        return

    table = Table(title=f"Usage History -- {period}")
    table.add_column("Date", style="dim")
    table.add_column("Task", style="cyan", max_width=40)
    table.add_column("Model", style="green")
    table.add_column("Cost", justify="right", style="yellow")

    for row in rows:
        table.add_row(
            row[0][:10] if row[0] else "—",
            row[1][:40] if row[1] else "—",
            row[4] or "—",
            f"${row[5]:.4f}" if row[5] else "—",
        )

    console.print(table)

    total = prefs.get_total_spend()
    savings = prefs.get_savings()
    if total > 0:
        console.print(f"\n[bold]Total spend:[/bold] ${total:.4f}")
        if savings > 0:
            console.print(f"[bold green]Potential savings tracked:[/bold green] ${savings:.4f}")


def _list_models_cmd():
    providers = get_available_providers()
    if not providers:
        console.print("[yellow]No providers configured.[/yellow]")
        return

    from lmx.pricing import PricingCache
    pricing = PricingCache()

    table = Table(title="Available Models")
    table.add_column("Model", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Input $/MTok", style="yellow")
    table.add_column("Output $/MTok", style="yellow")
    table.add_column("Context", style="magenta")

    for name, provider in providers.items():
        for model_id in provider.available_models:
            p = pricing.get_model(model_id)
            if p:
                cost_in = f"${p.input_price * 1000:.2f}" if p.input_price > 0 else "Free"
                cost_out = f"${p.output_price * 1000:.2f}" if p.output_price > 0 else "Free"
                table.add_row(model_id, name, cost_in, cost_out, f"{p.context_window:,}")

    console.print(table)


def _config_cmd(edit: bool):
    prefs = PreferenceManager()
    if edit:
        import os, subprocess
        subprocess.run([os.environ.get("EDITOR", "nano"), str(prefs.config_path)])
    else:
        console.print(prefs.display_config())


app = cli

if __name__ == "__main__":
    cli()