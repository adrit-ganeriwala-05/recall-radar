"""A0: snapshot lock/verify on a synthetic raw dir (synthetic_fixture) and on the real snapshot."""

import json
import os
import shutil
from pathlib import Path

import pytest

from recall_radar.data import snapshot as snap

SOURCES = (
    snap.Source("A.zip", "https://example.invalid/A.zip", "2026-10-10T05:00:00-04:00"),
    snap.Source("B.txt", "https://example.invalid/B.txt", "2026-10-09T00:00:00-04:00"),
)


@pytest.fixture
def raw(tmp_path: Path) -> Path:
    d = tmp_path / "raw"
    d.mkdir()
    (d / "A.zip").write_bytes(b"synthetic_fixture zip bytes " * 100)
    (d / "B.txt").write_text("ODINO\tMFR_NAME\n", encoding="utf-8")
    return d


@pytest.fixture
def lock(raw: Path, tmp_path: Path) -> Path:
    p = tmp_path / "SNAPSHOT.lock.json"
    snap.write_lock(snap.build_lock(raw, SOURCES), p)
    return p


def test_lock_records_every_field(raw: Path, lock: Path):
    entries = json.loads(lock.read_text())["files"]
    assert [e["file"] for e in entries] == ["A.zip", "B.txt"]
    a = entries[0]
    assert a["bytes"] == len(b"synthetic_fixture zip bytes " * 100)
    assert a["sha256"] == snap.sha256_file(raw / "A.zip")
    assert a["url"] == "https://example.invalid/A.zip"
    assert a["nhtsa_updated"] == "2026-10-10T05:00:00-04:00"
    assert a["retrieved_at"].endswith("Z")


def test_verify_passes_on_identical_copy(raw: Path, lock: Path):
    assert snap.verify(raw, lock) == []
    assert snap.main(["verify", "--raw", str(raw), "--lock", str(lock)]) == 0


def test_verify_fails_on_corrupted_copy(raw: Path, lock: Path, tmp_path: Path):
    copy = tmp_path / "copy"
    shutil.copytree(raw, copy)
    data = bytearray((copy / "A.zip").read_bytes())
    data[10] ^= 0xFF  # same size, different content
    (copy / "A.zip").write_bytes(bytes(data))
    assert snap.verify(copy, lock) == ["A.zip: sha256 mismatch"]
    assert snap.main(["verify", "--raw", str(copy), "--lock", str(lock)]) == 1


def test_verify_fails_on_missing_or_truncated_file(raw: Path, lock: Path):
    (raw / "B.txt").unlink()
    (raw / "A.zip").write_bytes(b"short")
    problems = snap.verify(raw, lock)
    assert problems[0].startswith("A.zip: bytes 5 != ")
    assert problems[1] == "B.txt: missing"


def test_lock_refuses_incomplete_raw_dir(raw: Path):
    (raw / "B.txt").unlink()
    with pytest.raises(FileNotFoundError, match="B.txt"):
        snap.build_lock(raw, SOURCES)


def test_snapshot_id_is_lock_file_hash_prefix(lock: Path):
    sid = snap.snapshot_id(lock)
    assert len(sid) == 12 and sid == snap.sha256_file(lock)[:12]


@pytest.mark.real_data
def test_real_raw_dir_matches_committed_lock():
    raw = Path(os.environ.get("RR_RAW_DIR", "data/raw")).expanduser()
    assert snap.verify(raw, snap.DEFAULT_LOCK) == []
