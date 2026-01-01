from rich.console import Console
from rich.table import Table
from .utils import compute_state_diff, apply_diff # Import our existing utils

def summarize_diff(diff: dict) -> str:
    """Creates a one-line summary of a state_diff for the table."""
    summary = []
    if diff.get("added"): 
        keys = list(diff["added"].keys())
        if "__last_run_metadata" in keys: keys.remove("__last_run_metadata")
        if keys: summary.append(f"[green]Added:[/green] {', '.join(keys)}")
    if diff.get("modified"): 
        summary.append(f"[yellow]Modified:[/yellow] {', '.join(list(diff['modified'].keys()))}")
    if diff.get("removed"):
        keys = list(diff["removed"].keys())
        if "__last_run_metadata" in keys: keys.remove("__last_run_metadata")
        if keys: summary.append(f"[red]Removed:[/red] {', '.join(keys)}")
    if not summary: return "[dim]No state change[/dim]"
    return "; ".join(summary)

def build_log_table(history: list) -> Table:
    """Builds a rich Table object from the history log."""
    table = Table(
        title="GlassBox Agent Run: Full Audit Log",
        show_header=True, 
        header_style="bold magenta",
        box=None
    )
    table.add_column("Step", style="dim", width=4)
    table.add_column("Node", style="cyan", width=12)
    table.add_column("Outcome", width=8)
    table.add_column("Tokens", style="yellow", width=6)
    table.add_column("Key Changes (The 'Diff')", no_wrap=False)

    total_tokens = 0
    for step in history:
        tokens = 0
        if "run_metadata" in step and step["run_metadata"]:
            tokens = step["run_metadata"].get("total_tokens", 0)
            total_tokens += tokens
        
        outcome = f"[green]{step['outcome']}[/green]" if step['outcome'] == 'success' else f"[red]{step['outcome']}[/red]"
        
        # Use compute_state_diff for backwards compatibility with old logs
        if "state_diff" in step:
            diff_to_summarize = step["state_diff"]
        else:
            diff_to_summarize = compute_state_diff(step["state_before"], step.get("state_after", {}))
            
        summary = summarize_diff(diff_to_summarize)
        
        table.add_row(
            str(step["step"]),
            step["node"],
            outcome,
            str(tokens),
            summary
        )
    
    table.add_row("---", "---", "---", "---", "---")
    table.add_row("", "[bold]TOTAL[/bold]", "", f"[bold yellow]{total_tokens}[/bold yellow]", "")
    total_tokens=0
    return table


