from __future__ import annotations

from pathlib import Path
from typing import Any

from cloud_allowlist.io_utils import atomic_write_text


RAW_BASE = "https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def emit_readme(root: Path, manifest_payload: dict[str, Any]) -> None:
    snapshot_rows = [
        ["snapshot_date", f"`{manifest_payload['snapshot_date']}`"],
        ["record_count", str(manifest_payload["record_count"])],
        ["unique_cidrs", str(manifest_payload["cidr_count"])],
        ["feed_count", str(manifest_payload["feed_count"])],
        ["stale_feed_count", str(manifest_payload["stale_feed_count"])],
    ]

    feed_rows: list[list[str]] = []
    for feed in manifest_payload["feeds"]:
        feed_rows.append(
            [
                f"`{feed['vendor']}`",
                f"`{feed['feed']}`",
                f"`{feed.get('instance') or '-'}`",
                str(feed["record_count"]),
                str(feed["unique_cidr_count"]),
                f"`{feed.get('source_published_at') or '-'}`",
                f"`{feed.get('source_version') or '-'}`",
                f"`{feed['fetch_status']}`",
            ]
        )

    file_rows = [
        ["manifest", "`dist/manifest.json`"],
        ["all_json", "`dist/json/all.json`"],
        ["all_csv", "`dist/csv/all.csv`"],
        ["all_txt", "`dist/txt/all.txt`"],
        ["all_txt_ipv4", "`dist/txt/all-ipv4.txt`"],
        ["all_txt_ipv6", "`dist/txt/all-ipv6.txt`"],
        ["terraform", "`dist/terraform/cloud_allowlist.auto.tfvars.json`"],
        ["paloalto", "`dist/paloalto/ip/all.txt`"],
        ["pfsense", "`dist/pfsense/urltable/all.txt`"],
        ["latest_changes_md", "`dist/changes/latest.md`"],
        ["latest_changes_json", "`dist/changes/latest.json`"],
        ["snapshot_history", "`state/history/snapshots/`"],
    ]

    raw_rows = [
        ["all_txt", f"`{RAW_BASE}/dist/txt/all.txt`"],
        ["github_paloalto", f"`{RAW_BASE}/dist/paloalto/ip/vendors/github.txt`"],
        ["aws_pfsense", f"`{RAW_BASE}/dist/pfsense/urltable/vendors/aws.txt`"],
    ]

    content = "\n\n".join(
        [
            "# cloud-allowlist",
            "## Snapshot",
            _table(["field", "value"], snapshot_rows),
            "## Feeds",
            _table(
                ["vendor", "feed", "instance", "records", "unique_cidrs", "published", "version", "status"],
                feed_rows,
            ),
            "## Files",
            _table(["dataset", "path"], file_rows),
            "## Raw URLs",
            _table(["dataset", "url"], raw_rows),
        ]
    )
    atomic_write_text(root / "README.md", f"{content}\n")
