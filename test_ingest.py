from sage.ingest import discover_files, file_hash, ingest_file


def test_ingest_text_file(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("Hello world, this is a note.")
    units = ingest_file(p)
    assert len(units) == 1
    assert units[0].location == "whole file"
    assert "Hello world" in units[0].text


def test_ingest_markdown_file(tmp_path):
    p = tmp_path / "note.md"
    p.write_text("# Title\n\nSome content.")
    units = ingest_file(p)
    assert len(units) == 1
    assert "Title" in units[0].text


def test_ingest_unsupported_extension_returns_empty(tmp_path):
    p = tmp_path / "image.png"
    p.write_bytes(b"\x89PNG\r\n")
    assert ingest_file(p) == []


def test_discover_files_finds_supported_recursively(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub" / "b.md").write_text("b")
    (tmp_path / "ignore.png").write_bytes(b"x")

    found = discover_files(tmp_path)
    names = {f.name for f in found}
    assert names == {"a.txt", "b.md"}


def test_file_hash_changes_when_content_changes(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("version one")
    h1 = file_hash(p)
    p.write_text("version two")
    h2 = file_hash(p)
    assert h1 != h2
