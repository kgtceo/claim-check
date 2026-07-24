"""claim-check CLI — lint a patent claim set for structural defects."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .data.sample_claims import DEFAULT_SAMPLE, SAMPLE_CLAIMS
from .explainer import ClaimChecker
from .models import CheckResult

app = typer.Typer(add_completion=False, help="Lint patent claims (antecedent basis, dependencies, formalities).")
console = Console()

_SEV = {"error": "[bold red]✗ ERROR[/]", "advisory": "[yellow]⚠ ADVISORY[/]"}


def _render(result: CheckResult) -> None:
    console.print(
        f"\n[bold]Parsed {len(result.claims)} claim(s)[/] — "
        f"[red]{result.error_count} error(s)[/], [yellow]{result.advisory_count} advisory[/]\n"
    )
    if not result.findings:
        console.print("[green]No structural issues found.[/]")
    for f in result.findings:
        console.print(f"{_SEV[f.severity]} [bold]claim {f.claim_number}[/] · {f.kind}")
        console.print(f"    {f.message}")
        if f.explanation:
            console.print(f"    [dim]why:[/] {f.explanation}")
        if f.suggested_fix:
            console.print(f"    [dim]fix:[/] {f.suggested_fix}")
        console.print()
    if result.summary:
        console.print(f"[italic]{result.summary}[/]")


def _run(text: str, use_llm: bool) -> None:
    client = None
    if use_llm:
        from .client import LLMClient
        from .config import Settings

        client = LLMClient(Settings.from_env())
    _render(ClaimChecker(client).check(text))


@app.command()
def check(
    text: str = typer.Argument(None, help="Claim text. Omit to read --file or stdin."),
    file: Path = typer.Option(None, "--file", "-f", help="Read claims from a file."),
    no_llm: bool = typer.Option(False, "--no-llm", help="Deterministic engine only (no API key)."),
) -> None:
    """Lint a claim set."""
    if file:
        text = file.read_text()
    if not text:
        text = typer.get_text_stream("stdin").read()
    if not text or not text.strip():
        raise typer.BadParameter("No claim text provided.")
    _run(text, use_llm=not no_llm)


@app.command()
def demo(
    sample: str = typer.Argument(DEFAULT_SAMPLE, help=f"One of: {', '.join(SAMPLE_CLAIMS)}"),
    no_llm: bool = typer.Option(False, "--no-llm"),
) -> None:
    """Run on a built-in sample claim set."""
    if sample not in SAMPLE_CLAIMS:
        raise typer.BadParameter(f"Unknown sample. Choose from: {', '.join(SAMPLE_CLAIMS)}")
    console.print(f"[dim]{SAMPLE_CLAIMS[sample]}[/]")
    _run(SAMPLE_CLAIMS[sample], use_llm=not no_llm)


if __name__ == "__main__":
    app()
