from __future__ import annotations

from pathlib import Path
import shutil

import pytest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


def prepare_repo(destination: Path) -> Path:
    for relative in ("config", "tests/fixtures"):
        shutil.copytree(SOURCE_ROOT / relative, destination / relative)

    for relative in (
        "state/latest/raw",
        "state/latest/feeds",
        "state/history/snapshots",
        "state/history/changes",
        "dist",
    ):
        (destination / relative).mkdir(parents=True, exist_ok=True)

    (destination / "state" / "m365_client_ids.json").write_text("{}\n", encoding="utf-8")
    return destination


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    return prepare_repo(tmp_path)
