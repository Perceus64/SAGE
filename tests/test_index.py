from sage.chunker import Chunk
from sage.index import SageIndex


def make_index(tmp_path):
    return SageIndex(tmp_path / "test.db")


def test_upsert_and_search(tmp_path):
    idx = make_index(tmp_path)
    chunks = [
        Chunk("bio.txt", "whole file", 0, "Mitochondria are the powerhouse of the cell."),
        Chunk("bio.txt", "whole file", 1, "Ribosomes synthesize proteins in the cell."),
    ]
    idx.upsert_file("bio.txt", "hash1", chunks, "2026-01-01T00:00:00")

    n_files, n_chunks = idx.stats()
    assert n_files == 1
    assert n_chunks == 2

    results = idx.search("powerhouse of the cell", top_k=1)
    assert len(results) == 1
    assert "Mitochondria" in results[0].text
    idx.close()


def test_upsert_replaces_old_chunks_for_same_file(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert_file(
        "bio.txt", "hash1", [Chunk("bio.txt", "whole file", 0, "old content")], "t1"
    )
    idx.upsert_file(
        "bio.txt", "hash2", [Chunk("bio.txt", "whole file", 0, "new content")], "t2"
    )
    n_files, n_chunks = idx.stats()
    assert n_files == 1
    assert n_chunks == 1
    assert idx.known_file_hash("bio.txt") == "hash2"
    idx.close()


def test_remove_file(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert_file(
        "bio.txt", "hash1", [Chunk("bio.txt", "whole file", 0, "content")], "t1"
    )
    idx.remove_file("bio.txt")
    n_files, n_chunks = idx.stats()
    assert n_files == 0
    assert n_chunks == 0
    idx.close()


def test_search_on_empty_index_returns_empty(tmp_path):
    idx = make_index(tmp_path)
    assert idx.search("anything") == []
    idx.close()


def test_search_works_with_single_chunk_corpus(tmp_path):
    """Regression test: TF-IDF max_df settings must not break on tiny corpora."""
    idx = make_index(tmp_path)
    idx.upsert_file(
        "solo.txt",
        "hash1",
        [Chunk("solo.txt", "whole file", 0, "Photosynthesis converts light into energy.")],
        "t1",
    )
    results = idx.search("photosynthesis")
    assert len(results) == 1
    idx.close()
