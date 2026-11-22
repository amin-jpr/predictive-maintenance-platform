import pytest
from scripts.verify_artifacts import verify

from predictive_maintenance.config import find_project_root
from predictive_maintenance.preprocessing.artifacts import verify_artifact_manifest


@pytest.mark.data_required
@pytest.mark.integration
def test_real_fd001_artifacts_verify() -> None:
    root = find_project_root()
    if not (root / "data/metadata/artifact_manifest.json").is_file():
        pytest.skip("Run preprocessing and build_features first")
    report = verify(root, "FD001")
    assert report["status"] == "PASS"
    results = verify_artifact_manifest(root, root / "data/metadata/artifact_manifest.json")
    assert all(item["passed"] for item in results)
