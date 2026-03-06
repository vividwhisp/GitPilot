from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from core.ai_client import FreeAIClient
from core.diff_parser import infer_project_type, summarize_diff
from core.executor import SafeExecutor
from core.git_handler import GitCommandError, GitHandler
from core.intent_parser import IntentParser
from core.risk_analyzer import RiskAnalyzer


console = Console()


def _show_file_table(file_stats) -> None:
    table = Table(title="Changed Files")
    table.add_column("Path", style="cyan")
    table.add_column("+", justify="right", style="green")
    table.add_column("-", justify="right", style="red")

    for item in file_stats:
        table.add_row(item.path, str(item.added), str(item.removed))

    console.print(table)


def smart_commit_flow(git: GitHandler, ai: FreeAIClient, risk_analyzer: RiskAnalyzer) -> None:
    status = git.status_short()
    if not status.strip():
        console.print("[yellow]No changes detected.[/yellow]")
        return

    file_stats = git.diff_numstat()
    diff_text = git.diff()
    project_type = infer_project_type(file_stats)
    summary_points = summarize_diff(file_stats, diff_text)

    suggestion = ai.generate_commit_suggestion(
        project_type=project_type,
        file_stats=file_stats,
        summary_points=summary_points,
        diff_excerpt=diff_text,
    )

    risk = risk_analyzer.analyze(file_stats, diff_text)

    _show_file_table(file_stats)

    preview_body = (
        f"[bold]{suggestion.title}[/bold]\n\n"
        f"{suggestion.description}\n\n"
        + "\n".join(f"- {b}" for b in suggestion.bullets)
    )
    console.print(Panel(preview_body, title="Smart Commit Suggestion"))

    warning_text = "\n".join(f"- {w}" for w in risk.warnings) if risk.warnings else "- No specific high-risk patterns found"
    console.print(Panel(f"Risk Level: [bold]{risk.level}[/bold]\n{warning_text}", title="Commit Risk"))

    if not Confirm.ask("Commit and push using this suggestion?", default=False):
        console.print("[yellow]Commit cancelled.[/yellow]")
        return

    body = suggestion.description
    if suggestion.bullets:
        body += "\n\n" + "\n".join(f"- {b}" for b in suggestion.bullets)

    git.stage_all()
    git.commit(suggestion.title, body)
    git.push()
    console.print("[green]Commit and push completed.[/green]")


def intent_flow(git: GitHandler, parser: IntentParser, executor: SafeExecutor) -> None:
    intent = Prompt.ask("Describe your Git intent")
    plan = parser.parse(intent)

    cmd_lines = "\n".join(f"git {' '.join(cmd)}" for cmd in plan.commands)
    console.print(Panel(f"{plan.description}\n\n{cmd_lines}\n\nRisk: {plan.risk}", title="Intent Plan"))

    if not Confirm.ask("Execute these commands?", default=False):
        console.print("[yellow]Execution cancelled.[/yellow]")
        return

    outputs = executor.execute_git(plan.commands)
    for out in outputs:
        if out:
            console.print(out)

    console.print("[green]Intent commands executed.[/green]")


def main() -> None:
    git = GitHandler(".")
    ai = FreeAIClient()
    parser = IntentParser()
    risk_analyzer = RiskAnalyzer()
    executor = SafeExecutor(git)

    try:
        git.ensure_repo()
    except GitCommandError as exc:
        console.print(f"[red]Git setup error:[/red] {exc}")
        return

    while True:
        console.print("\n[bold]Git Workflow Intelligence MVP[/bold]")
        console.print("1. Smart Commit")
        console.print("2. Intent to Git Command")
        console.print("3. Exit")

        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")

        try:
            if choice == "1":
                smart_commit_flow(git, ai, risk_analyzer)
            elif choice == "2":
                intent_flow(git, parser, executor)
            else:
                break
        except (GitCommandError, ValueError) as exc:
            console.print(f"[red]Error:[/red] {exc}")


if __name__ == "__main__":
    main()
