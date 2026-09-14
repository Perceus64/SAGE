"""Command-line interface for Sage."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from sage.index import SageIndex
from sage.llm import generate_answer
from sage.sync import sync_folder, watch_folder

console = Console()
DEFAULT_DB_NAME = ".sage_index.db"


def _open_index(db: str | None, folder: Path | None = None) -> SageIndex:
    if db:
        db_path = Path(db)
    elif folder:
        db_path = folder / DEFAULT_DB_NAME
    else:
        db_path = Path.cwd() / DEFAULT_DB_NAME
    return SageIndex(db_path)


@click.group()
@click.version_option()
def main():
    """Sage — an offline-first AI study assistant.

    Index your course material once, then ask questions with zero
    internet connection and zero cloud API calls.
    """


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--db", default=None, help="Path to the index database file.")
def sync(folder: Path, db: str | None):
    """Index (or re-index) all supported files under FOLDER."""
    index = _open_index(db, folder)
    console.print(f"[bold]Syncing[/bold] {folder} ...")
    summary = sync_folder(index, folder)
    n_files, n_chunks = index.stats()
    index.close()

    table = Table(show_header=False, box=None)
    table.add_row("Added", str(summary["added"]))
    table.add_row("Updated", str(summary["updated"]))
    table.add_row("Removed", str(summary["removed"]))
    table.add_row("Unchanged", str(summary["unchanged"]))
    if summary["skipped"]:
        table.add_row("Skipped (no text)", str(summary["skipped"]))
    console.print(table)
    console.print(f"[green]Index now covers {n_files} files, {n_chunks} chunks.[/green]")


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--db", default=None, help="Path to the index database file.")
@click.option("--interval", default=5, help="Seconds between change checks.")
def watch(folder: Path, db: str | None, interval: int):
    """Continuously watch FOLDER and re-sync whenever files change."""
    index = _open_index(db, folder)
    try:
        watch_folder(index, folder, interval_seconds=interval)
    finally:
        index.close()


@main.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--db", default=None, help="Path to the index database file.")
@click.option("--top-k", default=5, help="How many chunks to retrieve.")
def ask(question: tuple[str, ...], db: str | None, top_k: int):
    """Ask QUESTION against the local index. Works fully offline."""
    query = " ".join(question)
    index = _open_index(db)
    n_files, n_chunks = index.stats()
    if n_chunks == 0:
        console.print(
            "[yellow]Index is empty. Run `sage sync <folder>` first.[/yellow]"
        )
        index.close()
        return

    results = index.search(query, top_k=top_k)
    index.close()

    answer, backend = generate_answer(query, results)
    console.print(
        Panel(escape(answer), title=f"Answer — {backend}", border_style="cyan")
    )

    if results:
        console.print("\n[dim]Top sources:[/dim]")
        for r in results:
            console.print(
                f"  [dim]•[/dim] {Path(r.source_path).name} ({r.location})  "
                f"[dim]score={r.score:.2f}[/dim]"
            )


@main.command()
@click.option("--db", default=None, help="Path to the index database file.")
def stats(db: str | None):
    """Show how many files/chunks are currently indexed."""
    index = _open_index(db)
    n_files, n_chunks = index.stats()
    index.close()
    console.print(f"Files indexed:  {n_files}")
    console.print(f"Chunks indexed: {n_chunks}")


if __name__ == "__main__":
    main()
