"""CONCLAVE command-line interface."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="conclave",
    help="CONCLAVE — Calibrated Orchestrated Network of Criterion-level LLM Agents for Variant Evaluation",
    add_completion=False,
)
console = Console()


@app.command()
def interpret(
    variant_id: str = typer.Argument(..., help="Variant identifier, e.g. '13:32339461:A:-'"),
    genome_build: str = typer.Option("GRCh38", "--build", "-b", help="Genome build (GRCh37 or GRCh38)"),
    config: str = typer.Option("conf/config.yaml", "--config", "-c", help="Path to Hydra config"),
    output_format: str = typer.Option("json", "--format", "-f", help="Output format: json or text"),
) -> None:
    """Interpret a variant using CONCLAVE's multi-agent pipeline."""
    console.print(
        Panel(
            f"[bold green]CONCLAVE[/bold green] interpreting variant: [cyan]{variant_id}[/cyan]\n"
            f"Genome build: {genome_build} | Config: {config}",
            title="Variant Interpretation",
        )
    )
    console.print("[yellow]⚠ Full pipeline not yet implemented — scaffold only.[/yellow]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev mode)"),
) -> None:
    """Start the CONCLAVE FastAPI server."""
    import uvicorn
    console.print(f"[bold]Starting CONCLAVE server on {host}:{port}[/bold]")
    uvicorn.run("conclave.orchestrator.app:app", host=host, port=port, reload=reload)


@app.command()
def version() -> None:
    """Print the CONCLAVE version."""
    from conclave import __version__
    console.print(f"conclave {__version__}")


if __name__ == "__main__":
    app()
