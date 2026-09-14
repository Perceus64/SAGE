# Sage — an offline-first AI study assistant

Index your lecture notes, slides, and PDFs once. Ask questions about them
with **zero internet connection and zero cloud API calls**, forever after.

Every "chat with your PDFs" tool assumes a constant connection and an API
key. Sage doesn't. It's built for the very ordinary situation of having
unreliable power or internet but still needing to study *right now*.

```bash
$ sage sync ~/university/biology
Syncing ~/university/biology ...
  + indexed lecture4_photosynthesis.pdf (6 chunks)
  + indexed genetics_slides.pptx (14 chunks)
Index now covers 12 files, 83 chunks.

$ sage ask "where does the calvin cycle take place"
╭─────────────── Answer — extractive (no model) ───────────────╮
│ - The Calvin cycle takes place in the stroma and uses ATP    │
│   and NADPH to fix carbon dioxide into glucose.               │
│   [lecture4_photosynthesis.pdf (page 2)]                      │
╰────────────────────────────────────────────────────────────────╯
```

## Why this exists

- **Works with zero setup.** No API key, no signup, no GPU required.
  `pip install` and go.
- **Actually offline.** The default answer backend does pure local
  retrieval + extraction — no model weights to download, nothing
  phones home.
- **Gets smarter if you want it to.** Point `SAGE_MODEL_PATH` at a
  local GGUF model (with `llama-cpp-python` installed) and Sage
  automatically switches to generating real synthesized answers from a
  small local LLM — still fully offline.
- **Built for spotty connectivity, not just laptops with infinite
  bandwidth.** The `sync` step is incremental: it hashes every file, so
  re-running it after a brief burst of internet only re-indexes what
  actually changed.

## Install

```bash
git clone https://github.com/Perceus64/SAGE
cd sage
pip install -e .
```

Requires Python 3.9+. Everything needed for indexing and asking
questions (`click`, `rich`, `scikit-learn`, `pypdf`, `python-pptx`,
`watchdog`) installs with the package — no separate model download.

## Usage

```bash
# Index a folder of course material (PDF, PPTX, TXT, MD — recursive)
sage sync ~/university/biology

# Ask a question — works with the network off
sage ask "what are the three stages of cellular respiration"

# See what's currently indexed
sage stats

# Keep indexing automatically whenever files in the folder change
sage watch ~/university/biology
```

By default the index lives at `<folder>/.sage_index.db` (plain SQLite —
delete it any time to start fresh). Pass `--db path/to/index.db` to any
command to use a specific index file, e.g. if you keep your index
somewhere other than the material folder itself.

## Optional: a real local LLM instead of extractive answers

Extractive mode (the default) surfaces the most relevant sentences
verbatim with citations — genuinely useful, zero dependencies. If you
want Sage to *write* an answer instead of quoting one:

```bash
pip install -e ".[llm]"          # installs llama-cpp-python
export SAGE_MODEL_PATH=/path/to/a-small-model.gguf
sage ask "explain the krebs cycle in simple terms"
```

Any small GGUF chat model works (something in the 1–4B range keeps this
usable on modest hardware). Sage detects the model automatically and
switches backends — no flag needed.

## How it works

```
 course files (pdf/pptx/txt/md)
        │  sage sync
        ▼
   ingest.py  → extract text per page/slide, hash file for change detection
        │
        ▼
   chunker.py → split into overlapping ~180-word chunks
        │
        ▼
   index.py   → store chunks in SQLite; TF-IDF vector search at query time
        │
        ▼  sage ask "..."
   llm.py     → extractive answer (default) OR local llama.cpp generation
```

No component requires a network call at any point after the files are
on disk. Retrieval quality can be swapped later for real embeddings
(sentence-transformers, a local embedding GGUF, etc.) without changing
anything else — `index.py` is the one place that would need to change.

## Recording a demo GIF

`demo.sh` is a scripted walkthrough (fake-typing + realistic pauses) meant
to be recorded with [asciinema](https://asciinema.org) and converted to a
GIF for the top of this README:

```bash
pip install asciinema
asciinema rec demo.cast -c "./demo.sh"
agg demo.cast demo.gif   # or upload demo.cast and embed the player
```

## Continuous integration

Every push and PR runs lint (`ruff`) and the full test suite across
Python 3.9–3.12 via GitHub Actions (`.github/workflows/ci.yml`), plus an
end-to-end smoke test of `sync` → `ask` → `stats`.

## Roadmap / ideas

- [ ] Swap TF-IDF for local sentence-embedding retrieval (still offline)
- [ ] Simple TUI browser for search results instead of raw CLI output
- [ ] "Study mode": auto-generate flashcards/quiz questions from indexed
      material
- [ ] Sync from a watched cloud folder (Drive/Dropbox local sync
      client) so re-indexing happens the moment connectivity returns

Contributions and issues welcome.

## License

MIT — see [LICENSE](LICENSE).
