"""Incremental sync: index only what changed since last time.

The intended workflow is: whenever you briefly have internet/power and
fresh course material lands in a folder (synced from Drive, a USB drive,
whatever), run `sage sync`. It hashes every supported file, skips
anything unchanged, re-indexes anything new or modified, and drops
anything that was deleted. Everything after that (`sage ask`) works
fully offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sage.chunker import chunk_units
from sage.index import SageIndex
from sage.ingest import discover_files, file_hash, ingest_file


def sync_folder(index: SageIndex, folder: Path, quiet: bool = False) -> dict:
    """One-shot sync of `folder` into `index`. Returns a summary dict."""
    now = datetime.now(timezone.utc).isoformat()

    on_disk = discover_files(folder)
    on_disk_paths = {str(p) for p in on_disk}
    known = index.known_files()

    added, updated, removed, unchanged, skipped = 0, 0, 0, 0, 0

    for path in on_disk:
        path_str = str(path)
        try:
            h = file_hash(path)
        except Exception as e:
            if not quiet:
                print(f"  ! could not read {path.name}: {e}")
            skipped += 1
            continue

        existing_hash = index.known_file_hash(path_str)
        if existing_hash == h:
            unchanged += 1
            continue

        units = ingest_file(path)
        chunks = chunk_units(units)
        if not chunks:
            skipped += 1
            if not quiet:
                print(f"  ! no extractable text in {path.name}")
            continue

        index.upsert_file(path_str, h, chunks, now)
        if existing_hash is None:
            added += 1
            if not quiet:
                print(f"  + indexed {path.name} ({len(chunks)} chunks)")
        else:
            updated += 1
            if not quiet:
                print(f"  ~ re-indexed {path.name} ({len(chunks)} chunks, changed)")

    for gone_path in known - on_disk_paths:
        index.remove_file(gone_path)
        removed += 1
        if not quiet:
            print(f"  - removed {Path(gone_path).name} (no longer in folder)")

    return {
        "added": added,
        "updated": updated,
        "removed": removed,
        "unchanged": unchanged,
        "skipped": skipped,
    }


def watch_folder(index: SageIndex, folder: Path, interval_seconds: int = 5) -> None:
    """Continuously re-sync `folder` whenever files change, until Ctrl+C."""
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    print(f"Watching {folder} for changes (Ctrl+C to stop)...")
    sync_folder(index, folder)

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            sync_folder(index, folder)

    observer = Observer()
    observer.schedule(Handler(), str(folder), recursive=True)
    observer.start()
    try:
        import time

        while True:
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
