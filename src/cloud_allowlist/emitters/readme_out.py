from __future__ import annotations

from pathlib import Path
from typing import Any

from cloud_allowlist.io_utils import atomic_write_text


def _fmt(value: int) -> str:
    return f"{value:,}"


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
        ["cidrs", _fmt(manifest_payload["cidr_count"])],
        ["ipv4_cidrs", _fmt(manifest_payload["ipv4_cidr_count"])],
        ["ipv6_cidrs", _fmt(manifest_payload["ipv6_cidr_count"])],
        ["ipv4_addrs", _fmt(manifest_payload["ipv4_address_count"])],
    ]

    feed_rows: list[list[str]] = []
    for feed in manifest_payload["feeds"]:
        dataset = feed["dataset"]
        json_link = f"[json](dist/json/vendors/{dataset}.json)"
        txt_link = f"[txt](dist/txt/vendors/{dataset}.txt)"
        pa_link = f"[pa](dist/paloalto/ip/vendors/{dataset}.txt)"
        pf_link = f"[pf](dist/pfsense/urltable/vendors/{dataset}.txt)"
        src_link = f"[src]({feed['upstream_url']})"
        feed_rows.append(
            [
                f"`{dataset}`",
                _fmt(feed["unique_cidr_count"]),
                _fmt(feed["ipv4_cidr_count"]),
                _fmt(feed["ipv6_cidr_count"]),
                _fmt(feed["ipv4_address_count"]),
                f"`{feed['updated_at']}`",
                f"{json_link} {txt_link} {pa_link} {pf_link} {src_link}",
            ]
        )

    output_rows = [
        [
            "`all`",
            _fmt(manifest_payload["cidr_count"]),
            f"[json](dist/json/all.json) [csv](dist/csv/all.csv) [txt](dist/txt/all.txt)",
        ],
        [
            "`all-ipv4`",
            _fmt(manifest_payload["ipv4_cidr_count"]),
            f"[txt](dist/txt/all-ipv4.txt) [pa](dist/paloalto/ip/all-ipv4.txt) [pf](dist/pfsense/urltable/all-ipv4.txt)",
        ],
        [
            "`all-ipv6`",
            _fmt(manifest_payload["ipv6_cidr_count"]),
            f"[txt](dist/txt/all-ipv6.txt) [pa](dist/paloalto/ip/all-ipv6.txt) [pf](dist/pfsense/urltable/all-ipv6.txt)",
        ],
        [
            "`meta`",
            "-",
            f"[manifest](dist/manifest.json) [changes-md](dist/changes/latest.md) [changes-json](dist/changes/latest.json) [tf](dist/terraform/cloud_allowlist.auto.tfvars.json)",
        ],
    ]

    content = "\n\n".join(
        [
            "# cloud-allowlist",
            "## Snapshot",
            _table(["field", "value"], snapshot_rows),
            "## Feeds",
            _table(
                ["dataset", "cidrs", "v4", "v6", "ipv4_addrs", "updated", "links"],
                feed_rows,
            ),
            "## Outputs",
            _table(["dataset", "cidrs", "links"], output_rows),
        ]
    )
    atomic_write_text(root / "README.md", f"{content}\n")
