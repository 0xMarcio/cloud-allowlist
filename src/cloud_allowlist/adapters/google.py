from __future__ import annotations

from typing import Any

from cloud_allowlist.adapters.common import build_manifest, clone_state_for_snapshot, source_version_matches, stale_fallback
from cloud_allowlist.model import FeedState, NormalizedRecord
from cloud_allowlist.normalize import normalize_records
from cloud_allowlist.sorting import canonicalize_cidr

GOOGLE_GOOG_URL = "https://www.gstatic.com/ipranges/goog.json"
GOOGLE_CLOUD_URL = "https://www.gstatic.com/ipranges/cloud.json"


def parse_google_payload(
    payload: dict[str, Any],
    *,
    feed: str,
    source_url: str,
    fetched_at: str,
    stale: bool = False,
) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    source_version = str(payload.get("syncToken", ""))
    published_at = payload.get("creationTime")

    for entry in payload.get("prefixes", []):
        for family, field_name in ((4, "ipv4Prefix"), (6, "ipv6Prefix")):
            cidr = entry.get(field_name)
            if not cidr:
                continue
            cidr = canonicalize_cidr(cidr)
            service = entry.get("service")
            scope = entry.get("scope")
            records.append(
                NormalizedRecord(
                    record_id=f"google:{feed}:{family}:{cidr}:{service or ''}:{scope or ''}",
                    vendor="google",
                    feed=feed,
                    family=family,
                    cidr=cidr,
                    source_url=source_url,
                    source_version=source_version,
                    source_published_at=published_at,
                    fetched_at=fetched_at,
                    service=service,
                    region=scope,
                    extra={"scope": scope, "service": service},
                    stale=stale,
                )
            )

    return normalize_records(records)


def collect_google_feed(
    fetcher: Any,
    *,
    url: str,
    feed: str,
    previous_state: FeedState | None,
    snapshot_date: str,
    fetched_at: str,
    timeout_seconds: int,
) -> FeedState:
    try:
        result = fetcher.fetch_json(url, timeout=timeout_seconds)
        source_version = str(result.payload.get("syncToken", ""))
        if source_version_matches(previous_state, source_version):
            return clone_state_for_snapshot(previous_state, snapshot_date)

        records = parse_google_payload(result.payload, feed=feed, source_url=url, fetched_at=fetched_at)
        manifest = build_manifest(
            vendor="google",
            feed=feed,
            upstream_url=url,
            records=records,
            fetch_status="success",
            stale=False,
            source_version=source_version,
            source_published_at=result.payload.get("creationTime"),
            details={
                "syncToken": result.payload.get("syncToken"),
                "creationTime": result.payload.get("creationTime"),
            },
        )
        return FeedState(
            snapshot_date=snapshot_date,
            manifest=manifest,
            records=records,
            raw_artifacts={f"{feed}.json": result.payload},
        )
    except Exception as exc:
        if previous_state is None:
            raise
        return stale_fallback(previous_state, snapshot_date, str(exc))
