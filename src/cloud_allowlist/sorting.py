from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any

from cloud_allowlist.model import NormalizedRecord


def canonicalize_cidr(value: str) -> str:
    network_value = value.strip()
    if "/" not in network_value:
        address = ip_address(network_value)
        suffix = 32 if address.version == 4 else 128
        network_value = f"{network_value}/{suffix}"
    return str(ip_network(network_value, strict=False))


def cidr_family(value: str) -> int:
    return ip_network(value, strict=False).version


def cidr_sort_key(value: str) -> tuple[int, int, int]:
    network = ip_network(value, strict=False)
    return (network.version, int(network.network_address), network.prefixlen)


def record_sort_key(record: NormalizedRecord) -> tuple[Any, ...]:
    return (
        record.vendor,
        record.feed,
        record.instance or "",
        record.section or "",
        record.service or "",
        record.product or "",
        record.category or "",
        record.family,
        int(ip_network(record.cidr, strict=False).network_address),
        ip_network(record.cidr, strict=False).prefixlen,
        record.record_id,
    )


def sort_records(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    return sorted(records, key=record_sort_key)
