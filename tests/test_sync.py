from sage.index import SageIndex
from sage.sync import sync_folder


def test_sync_adds_new_files(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("Alpha content about biology.")

    idx = SageIndex(tmp_path / "index.db")
    summary = sync_folder(idx, folder, quiet=True)

    assert summary["added"] == 1
    assert summary["updated"] == 0
    n_files, _ = idx.stats()
    assert n_files == 1
    idx.close()


def test_sync_skips_unchanged_files(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("Alpha content.")

    idx = SageIndex(tmp_path / "index.db")
    sync_folder(idx, folder, quiet=True)
    summary = sync_folder(idx, folder, quiet=True)

    assert summary["added"] == 0
    assert summary["unchanged"] == 1
    idx.close()


def test_sync_reindexes_modified_files(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    f = folder / "a.txt"
    f.write_text("Original content.")

    idx = SageIndex(tmp_path / "index.db")
    sync_folder(idx, folder, quiet=True)

    f.write_text("Totally different updated content.")
    summary = sync_folder(idx, folder, quiet=True)

    assert summary["updated"] == 1
    idx.close()


def test_sync_removes_deleted_files(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    f = folder / "a.txt"
    f.write_text("Some content.")

    idx = SageIndex(tmp_path / "index.db")
    sync_folder(idx, folder, quiet=True)

    f.unlink()
    summary = sync_folder(idx, folder, quiet=True)

    assert summary["removed"] == 1
    n_files, _ = idx.stats()
    assert n_files == 0
    idx.close()
