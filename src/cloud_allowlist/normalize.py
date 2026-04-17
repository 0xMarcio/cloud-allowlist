from __future__ import annotations

from typing import Iterable
import json

from cloud_allowlist.model import NormalizedRecord
from cloud_allowlist.sorting import canonicalize_cidr, cidr_family, sort_records


def _normalized_signature(record: NormalizedRecord) -> str:
    return json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))


def normalize_records(records: Iterable[NormalizedRecord]) -> list[NormalizedRecord]:
    exact_records: dict[str, NormalizedRecord] = {}

    for record in records:
        cidr = canonicalize_cidr(record.cidr)
        normalized = NormalizedRecord(
            record_id=record.record_id,
            vendor=record.vendor,
            feed=record.feed,
            instance=record.instance,
            section=record.section,
            service=record.service,
            product=record.product,
            category=record.category,
            direction=record.direction,
            region=record.region,
            network_border_group=record.network_border_group,
            family=cidr_family(cidr),
            cidr=cidr,
            source_url=record.source_url,
            source_version=record.source_version,
            source_published_at=record.source_published_at,
            fetched_at=record.fetched_at,
            required=record.required,
            express_route=record.express_route,
            tcp_ports=record.tcp_ports,
            udp_ports=record.udp_ports,
            extra=record.extra,
            stale=record.stale,
        )
        exact_records[_normalized_signature(normalized)] = normalized

    return sort_records(list(exact_records.values()))
