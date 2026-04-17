from __future__ import annotations

from pathlib import Path
import csv
import json

from cloud_allowlist.io_utils import ensure_directory
from cloud_allowlist.model import NormalizedRecord


CSV_COLUMNS = [
    "record_id",
    "vendor",
    "feed",
    "instance",
    "section",
    "service",
    "product",
    "category",
    "direction",
    "region",
    "network_border_group",
    "family",
    "cidr",
    "source_url",
    "source_version",
    "source_published_at",
    "fetched_at",
    "required",
    "express_route",
    "tcp_ports",
    "udp_ports",
    "stale",
    "extra",
]


def emit_csv_outputs(dist_dir: Path, records: list[NormalizedRecord]) -> None:
    ensure_directory(dist_dir / "csv")
    path = dist_dir / "csv" / "all.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            payload = record.to_dict()
            payload["extra"] = json.dumps(payload.get("extra", {}), sort_keys=True, separators=(",", ":"))
            writer.writerow({column: payload.get(column) for column in CSV_COLUMNS})
