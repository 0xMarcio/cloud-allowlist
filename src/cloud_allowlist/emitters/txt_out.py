from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from cloud_allowlist.io_utils import atomic_write_text, ensure_directory
from cloud_allowlist.model import NormalizedRecord, output_name
from cloud_allowlist.sorting import cidr_sort_key


def unique_sorted_cidrs(records: list[NormalizedRecord]) -> list[str]:
    return sorted({record.cidr for record in records}, key=cidr_sort_key)


def build_text_collections(records: list[NormalizedRecord]) -> dict[str, list[str] | dict[str, list[str]]]:
    vendors: dict[str, list[NormalizedRecord]] = defaultdict(list)
    for record in records:
        vendors[output_name(record.vendor, record.feed, record.instance)].append(record)

    return {
        "all": unique_sorted_cidrs(records),
        "all_ipv4": unique_sorted_cidrs([record for record in records if record.family == 4]),
        "all_ipv6": unique_sorted_cidrs([record for record in records if record.family == 6]),
        "vendors": {
            name: unique_sorted_cidrs(items)
            for name, items in sorted(vendors.items())
        },
    }


def write_text_collection(base_dir: Path, collections: dict[str, list[str] | dict[str, list[str]]]) -> None:
    ensure_directory(base_dir)
    atomic_write_text(base_dir / "all.txt", "\n".join(collections["all"]) + "\n")
    atomic_write_text(base_dir / "all-ipv4.txt", "\n".join(collections["all_ipv4"]) + "\n")
    atomic_write_text(base_dir / "all-ipv6.txt", "\n".join(collections["all_ipv6"]) + "\n")

    vendor_dir = base_dir / "vendors"
    ensure_directory(vendor_dir)
    for name, cidrs in collections["vendors"].items():
        atomic_write_text(vendor_dir / f"{name}.txt", "\n".join(cidrs) + "\n")


def emit_txt_outputs(dist_dir: Path, records: list[NormalizedRecord]) -> dict[str, list[str] | dict[str, list[str]]]:
    collections = build_text_collections(records)
    write_text_collection(dist_dir / "txt", collections)
    return collections
