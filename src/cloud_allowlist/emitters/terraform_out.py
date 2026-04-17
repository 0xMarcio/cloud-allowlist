from __future__ import annotations

from pathlib import Path

from cloud_allowlist.emitters.txt_out import build_text_collections
from cloud_allowlist.io_utils import atomic_write_json, atomic_write_text, ensure_directory
from cloud_allowlist.model import NormalizedRecord, terraform_vendor_key
from cloud_allowlist.sorting import cidr_sort_key


def emit_terraform_outputs(dist_dir: Path, records: list[NormalizedRecord]) -> None:
    ensure_directory(dist_dir / "terraform")
    collections = build_text_collections(records)
    vendors = {}
    for record in records:
        key = terraform_vendor_key(record.vendor, record.feed, record.instance)
        vendors.setdefault(key, [])

    for record in records:
        key = terraform_vendor_key(record.vendor, record.feed, record.instance)
        vendors[key].append(record.cidr)

    payload = {
        "cloud_allowlist": {
            "all": collections["all"],
            "all_ipv4": collections["all_ipv4"],
            "all_ipv6": collections["all_ipv6"],
            "vendors": {key: sorted(set(value), key=cidr_sort_key) for key, value in sorted(vendors.items())},
        }
    }
    atomic_write_json(dist_dir / "terraform" / "cloud_allowlist.auto.tfvars.json", payload)
    atomic_write_text(
        dist_dir / "terraform" / "README.md",
        "\n".join(
            [
                "# Terraform Outputs",
                "",
                "Use `cloud_allowlist.auto.tfvars.json` directly with Terraform or OpenTofu.",
                "The `cloud_allowlist` object exposes aggregate lists and vendor-specific CIDR lists.",
                "",
            ]
        ),
    )
