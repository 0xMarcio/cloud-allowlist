from __future__ import annotations

from typing import Any

from cloud_allowlist.adapters.common import build_manifest, clone_state_for_snapshot, source_version_matches, stale_fallback
from cloud_allowlist.model import FeedState, NormalizedRecord
from cloud_allowlist.normalize import normalize_records
from cloud_allowlist.sorting import canonicalize_cidr

AWS_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
FEED = "aws-ip-ranges"


def parse_aws_payload(payload: dict[str, Any], *, fetched_at: str, source_url: str, stale: bool = False) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    source_version = str(payload.get("syncToken", ""))
    published_at = payload.get("createDate")

    for entry in payload.get("prefixes", []):
        cidr = canonicalize_cidr(entry["ip_prefix"])
        records.append(
            NormalizedRecord(
                record_id=":".join(
                    [
                        "aws",
                        "4",
                        cidr,
                        str(entry.get("service", "")),
                        str(entry.get("region", "")),
                        str(entry.get("network_border_group", "")),
                    ]
                ),
                vendor="aws",
                feed=FEED,
                family=4,
                cidr=cidr,
                source_url=source_url,
                source_version=source_version,
                source_published_at=published_at,
                fetched_at=fetched_at,
                service=entry.get("service"),
                region=entry.get("region"),
                network_border_group=entry.get("network_border_group"),
                extra={},
                stale=stale,
            )
        )

    for entry in payload.get("ipv6_prefixes", []):
        cidr = canonicalize_cidr(entry["ipv6_prefix"])
        records.append(
            NormalizedRecord(
                record_id=":".join(
                    [
                        "aws",
                        "6",
                        cidr,
                        str(entry.get("service", "")),
                        str(entry.get("region", "")),
                        str(entry.get("network_border_group", "")),
                    ]
                ),
                vendor="aws",
                feed=FEED,
                family=6,
                cidr=cidr,
                source_url=source_url,
                source_version=source_version,
                source_published_at=published_at,
                fetched_at=fetched_at,
                service=entry.get("service"),
                region=entry.get("region"),
                network_border_group=entry.get("network_border_group"),
                extra={},
                stale=stale,
            )
        )

    return normalize_records(records)


def collect_aws(fetcher: Any, *, previous_state: FeedState | None, snapshot_date: str, fetched_at: str, timeout_seconds: int) -> FeedState:
    try:
        result = fetcher.fetch_json(AWS_URL, timeout=timeout_seconds)
        source_version = str(result.payload.get("syncToken", ""))
        if source_version_matches(previous_state, source_version):
            return clone_state_for_snapshot(previous_state, snapshot_date)

        records = parse_aws_payload(result.payload, fetched_at=fetched_at, source_url=AWS_URL)
        manifest = build_manifest(
            vendor="aws",
            feed=FEED,
            upstream_url=AWS_URL,
            records=records,
            fetch_status="success",
            stale=False,
            source_version=source_version,
            source_published_at=result.payload.get("createDate"),
            details={
                "syncToken": result.payload.get("syncToken"),
                "createDate": result.payload.get("createDate"),
            },
        )
        return FeedState(
            snapshot_date=snapshot_date,
            manifest=manifest,
            records=records,
            raw_artifacts={"aws-ip-ranges.json": result.payload},
        )
    except Exception as exc:
        if previous_state is None:
            raise
        return stale_fallback(previous_state, snapshot_date, str(exc))
