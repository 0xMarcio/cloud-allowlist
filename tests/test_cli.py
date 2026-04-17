from __future__ import annotations

from pathlib import Path
import json

from cloud_allowlist.cli import main, run_update
from cloud_allowlist.io_utils import FixtureFetcher


def test_update_with_fixtures_generates_outputs(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    assert main(["update", "--use-fixtures"]) == 0
    assert (repo_root / "dist" / "manifest.json").exists()
    assert (repo_root / "dist" / "changes" / "latest.md").exists()
    assert (repo_root / "state" / "history" / "snapshots").exists()
    assert (repo_root / "dist" / "txt" / "vendors" / "m365-worldwide.txt").exists()
    assert main(["validate"]) == 0


def test_first_run_baseline_message(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    assert main(["update", "--use-fixtures"]) == 0
    latest_md = (repo_root / "dist" / "changes" / "latest.md").read_text(encoding="utf-8")
    assert "No prior baseline snapshot exists for comparison." in latest_md


def test_stale_fallback_uses_last_known_good_data(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    assert main(["update", "--use-fixtures"]) == 0

    class GithubFailingFixtureFetcher(FixtureFetcher):
        def __init__(self, fixture_root: Path) -> None:
            super().__init__(fixture_root, failing_patterns={"https://api.github.com/meta"})

    monkeypatch.setattr("cloud_allowlist.cli.FixtureFetcher", GithubFailingFixtureFetcher)
    assert run_update(repo_root, use_fixtures=True) == 0

    manifest = json.loads((repo_root / "dist" / "manifest.json").read_text(encoding="utf-8"))
    github_manifest = next(feed for feed in manifest["feeds"] if feed["vendor"] == "github")
    assert github_manifest["stale"] is True
    assert github_manifest["record_count"] > 0

    github_records = json.loads((repo_root / "dist" / "json" / "vendors" / "github.json").read_text(encoding="utf-8"))
    assert github_records
