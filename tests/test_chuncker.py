from sage.chunker import chunk_unit
from sage.ingest import RawUnit


def test_short_text_produces_single_chunk():
    unit = RawUnit("notes.txt", "whole file", "short text under the limit")
    chunks = chunk_unit(unit, chunk_words=180, overlap_words=40)
    assert len(chunks) == 1
    assert chunks[0].text == unit.text
    assert chunks[0].chunk_index == 0


def test_long_text_splits_with_overlap():
    words = [f"word{i}" for i in range(500)]
    unit = RawUnit("notes.txt", "whole file", " ".join(words))
    chunks = chunk_unit(unit, chunk_words=100, overlap_words=20)

    assert len(chunks) > 1
    # consecutive chunks should share overlapping words
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    assert first_words[-20:] == second_words[:20]


def test_empty_text_produces_no_chunks():
    unit = RawUnit("notes.txt", "whole file", "   ")
    assert chunk_unit(unit) == []
