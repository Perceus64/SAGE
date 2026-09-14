"""Turn retrieved chunks into an answer.

Two backends, chosen automatically:

1. "extractive" (always available, zero extra dependencies): stitches
   together the most relevant sentences from the retrieved chunks. No
   model, no download, works instantly on any machine.

2. "llama_cpp" (used automatically if `llama-cpp-python` is installed
   AND a local GGUF model path is configured): feeds the retrieved
   chunks to a small local LLM as context and asks it to write a real
   synthesized answer, fully offline.

This split is the whole point of the tool: it is genuinely useful with
zero setup, and gets better once you plug in a local model — never a
cloud API call either way.
"""

from __future__ import annotations

import os
import re
import textwrap

from sage.index import SearchResult

MODEL_PATH_ENV = "SAGE_MODEL_PATH"


def _llama_cpp_available() -> bool:
    if not os.environ.get(MODEL_PATH_ENV):
        return False
    try:
        import llama_cpp  # noqa: F401
    except ImportError:
        return False
    return os.path.exists(os.environ[MODEL_PATH_ENV])


def _extractive_answer(query: str, results: list[SearchResult]) -> str:
    query_terms = {w.lower() for w in re.findall(r"\w+", query) if len(w) > 2}

    scored_sentences: list[tuple[float, str, str]] = []
    for r in results:
        sentences = re.split(r"(?<=[.!?])\s+", r.text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) < 20:
                continue
            terms = {w.lower() for w in re.findall(r"\w+", s_clean)}
            overlap = len(terms & query_terms)
            if overlap:
                scored_sentences.append((overlap, s_clean, f"{r.source_path} ({r.location})"))

    if not scored_sentences:
        # nothing matched at the sentence level — fall back to top chunk
        top = results[0]
        snippet = textwrap.shorten(top.text, width=400, placeholder="...")
        return f"{snippet}\n\n(source: {top.source_path}, {top.location})"

    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    lines = []
    for _, sentence, cite in scored_sentences[:5]:
        if sentence in seen:
            continue
        seen.add(sentence)
        lines.append(f"- {sentence} [{cite}]")

    return "\n".join(lines)


def _llama_cpp_answer(query: str, results: list[SearchResult]) -> str:
    from llama_cpp import Llama

    model_path = os.environ[MODEL_PATH_ENV]
    llm = Llama(model_path=model_path, n_ctx=4096, verbose=False)

    context = "\n\n".join(
        f"[{r.source_path} ({r.location})]\n{r.text}" for r in results
    )
    prompt = (
        "You are a study assistant. Answer the question using ONLY the "
        "context below. Cite the source in brackets after each claim. "
        "If the context doesn't contain the answer, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    )
    out = llm(prompt, max_tokens=400, stop=["Question:"])
    return out["choices"][0]["text"].strip()


def generate_answer(query: str, results: list[SearchResult]) -> tuple[str, str]:
    """Returns (answer_text, backend_used)."""
    if not results:
        return (
            "Nothing in the index looks relevant to that question yet. "
            "Try `sage sync <folder>` to index more material, or rephrase."
        ), "none"

    if _llama_cpp_available():
        try:
            return _llama_cpp_answer(query, results), "llama.cpp (local model)"
        except Exception as e:  # model load/inference failure -> fall back
            print(f"  ! local model failed ({e}), falling back to extractive mode")

    return _extractive_answer(query, results), "extractive (no model)"
