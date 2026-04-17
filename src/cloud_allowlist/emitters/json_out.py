from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from cloud_allowlist.emitters.txt_out import build_text_collections
from cloud_allowlist.io_utils import atomic_write_json, ensure_directory
from cloud_allowlist.model import Snapshot, output_name


def _build_index(snapshot: Snapshot) -> dict[str, Any]:
    collections = build_text_collections(snapshot.records)
    vendor_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in snapshot.records:
        vendor_records[output_name(record.vendor, record.feed, record.instance)].append(record.to_dict())

    return {
        "snapshot_date": snapshot.snapshot_date,
        "record_count": len(snapshot.records),
        "cidr_count": len(collections["all"]),
        "vendors": {
            name: {
                "record_count": len(items),
                "cidrs": collections["vendors"][name],
            }
            for name, items in sorted(vendor_records.items())
        },
    }


def emit_json_outputs(dist_dir: Path, snapshot: Snapshot, manifest_payload: dict[str, Any]) -> None:
    ensure_directory(dist_dir / "json" / "vendors")
    atomic_write_json(dist_dir / "manifest.json", manifest_payload)
    atomic_write_json(dist_dir / "json" / "all.json", [record.to_dict() for record in snapshot.records])
    atomic_write_json(dist_dir / "json" / "index.json", _build_index(snapshot))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in snapshot.records:
        grouped[output_name(record.vendor, record.feed, record.instance)].append(record.to_dict())

    for name, records in sorted(grouped.items()):
        atomic_write_json(dist_dir / "json" / "vendors" / f"{name}.json", records)
