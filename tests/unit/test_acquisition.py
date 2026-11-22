import hashlib
import zipfile
from pathlib import Path

import pytest

from predictive_maintenance.data.acquisition import AcquisitionError, extract_subset


def _make_archive(path: Path, subset: str = "FD001") -> dict[str, str]:
    members = {
        f"train_{subset}.txt": "1 1 " + " ".join(["0.0"] * 24) + "\n",
        f"test_{subset}.txt": "1 1 " + " ".join(["0.0"] * 24) + "\n",
        f"RUL_{subset}.txt": "5\n",
        "readme.txt": "synthetic readme\n",
        "Damage Propagation Modeling.pdf": b"%PDF synthetic".decode("latin1"),
    }
    hashes = {}
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            data = content.encode("latin1")
            archive.writestr(name, data)
            hashes[name] = hashlib.sha256(data).hexdigest()
    return hashes


def test_extract_subset_verifies_hashes(tmp_path: Path) -> None:
    archive_path = tmp_path / "CMAPSSData.zip"
    hashes = _make_archive(archive_path)
    config = {"paths": {"raw_dir": "data/raw/cmaps"}, "file_sha256": {"FD001": hashes}}
    records = extract_subset(config, tmp_path, "FD001", archive_path)
    assert len(records) == 5
    assert (tmp_path / "data/raw/cmaps/train_FD001.txt").is_file()


def test_extract_subset_rejects_hash_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "CMAPSSData.zip"
    hashes = _make_archive(archive_path)
    hashes["train_FD001.txt"] = "0" * 64
    config = {"paths": {"raw_dir": "data/raw/cmaps"}, "file_sha256": {"FD001": hashes}}
    with pytest.raises(AcquisitionError, match="SHA-256 mismatch"):
        extract_subset(config, tmp_path, "FD001", archive_path)
