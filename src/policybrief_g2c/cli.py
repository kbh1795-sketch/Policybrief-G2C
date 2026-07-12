from __future__ import annotations

import http.server
import socketserver
from functools import partial
from pathlib import Path

import typer

from policybrief_g2c.config import AppSettings, load_source_configs
from policybrief_g2c.logging_config import configure_logging
from policybrief_g2c.newsletter.sender import EmailSender
from policybrief_g2c.pipeline import PolicyPipeline
from policybrief_g2c.storage.repository import PolicyRepository

app = typer.Typer(help="PolicyBrief G2C 정책 뉴스레터 CLI")


def _pipeline() -> PolicyPipeline:
    settings = AppSettings()
    configure_logging(settings.log_level)
    return PolicyPipeline(settings)


@app.command()
def collect() -> None:
    pipeline = _pipeline()
    documents = pipeline.collect()
    typer.echo(f"Collected {len(documents)} documents")


@app.command()
def process() -> None:
    pipeline = _pipeline()
    documents = pipeline.process()
    typer.echo(f"Processed {len(documents)} unique documents")


@app.command()
def summarize() -> None:
    pipeline = _pipeline()
    documents = pipeline.summarize()
    typer.echo(f"Summarized {len(documents)} documents")


@app.command("build-newsletter")
def build_newsletter() -> None:
    pipeline = _pipeline()
    _, html_path, text_path = pipeline.build_newsletter()
    typer.echo(f"HTML: {html_path}")
    typer.echo(f"Text: {text_path}")


@app.command()
def preview(path: Path | None = None, port: int = 8000) -> None:
    settings = AppSettings()
    output_dir = settings.output_dir
    if path:
        typer.echo(path)
        return
    typer.echo(f"Serving {output_dir.resolve()} at http://127.0.0.1:{port}")
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(output_dir))
    with socketserver.TCPServer(("127.0.0.1", port), handler) as server:
        server.serve_forever()


@app.command()
def send(dry_run: bool = True, confirm_send: bool = False, issue_id: str | None = None) -> None:
    settings = AppSettings()
    repository = PolicyRepository(settings.database_path)
    repository.initialize()
    issue = repository.get_issue(issue_id) if issue_id else None
    if issue is None:
        raise typer.BadParameter("issue_id is required for sending in this MVP")
    result = EmailSender(settings).send(issue, dry_run=dry_run, confirm_send=confirm_send)
    typer.echo(result)


@app.command()
def run(demo: bool = False) -> None:
    pipeline = _pipeline()
    _, html_path, text_path = pipeline.run(demo=demo)
    typer.echo(f"Generated newsletter HTML: {html_path}")
    typer.echo(f"Generated newsletter text: {text_path}")


@app.command("validate-config")
def validate_config() -> None:
    settings = AppSettings()
    sources = load_source_configs(settings.source_config_path)
    typer.echo(f"Configuration OK. Sources: {len(sources)}")


@app.command("show-stats")
def show_stats() -> None:
    settings = AppSettings()
    repository = PolicyRepository(settings.database_path)
    repository.initialize()
    typer.echo(repository.stats())


if __name__ == "__main__":
    app()
