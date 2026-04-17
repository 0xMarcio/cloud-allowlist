from __future__ import annotations

from pathlib import Path

from cloud_allowlist.emitters.txt_out import build_text_collections, write_text_collection
from cloud_allowlist.model import NormalizedRecord


def emit_paloalto_outputs(dist_dir: Path, records: list[NormalizedRecord]) -> None:
    collections = build_text_collections(records)
    write_text_collection(dist_dir / "paloalto" / "ip", collections)
