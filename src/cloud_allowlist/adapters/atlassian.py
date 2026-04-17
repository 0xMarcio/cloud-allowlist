from __future__ import annotations

from typing import Any
import hashlib
import json

from cloud_allowlist.adapters.common import build_manifest, clone_state_for_snapshot, source_version_matches, stale_fallback
from cloud_allowlist.io_utils import sha256_hex
from cloud_allowlist.model import FeedState, NormalizedRecord
from cloud_allowlist.normalize import normalize_records
from cloud_allowlist.sorting import canonicalize_cidr

ATLASSIAN_URL = "https://ip-ranges.atlassian.com/"
FEED = "atlassian-ip-ranges"


def _extract_cidr_strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        try:
            found.append(canonicalize_cidr(value))
        except ValueError:
            return []
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(_extract_cidr_strings(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_extract_cidr_strings(child))
    return found


def _candidate_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        candidates: list[dict[str, Any]] = []
        for value in payload.values():
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
        if candidates:
            return candidates
        if _extract_cidr_strings(payload):
            return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _item_identity(item: dict[str, Any]) -> str:
    for field_name in ("id", "name", "key"):
        value = item.get(field_name)
        if value is not None:
            return str(value)
    digest_source = json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(digest_source).hexdigest()[:12]


def parse_atlassian_payload(payload: dict[str, Any], *, fetched_at: str, source_url: str, source_version: str, stale: bool = False) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    published_at = payload.get("creationDate")

    for item in _candidate_items(payload):
        cidrs = sorted(set(_extract_cidr_strings(item)))
        if not cidrs:
            continue
        item_identity = _item_identity(item)
        for cidr in cidrs:
            family = 6 if ":" in cidr else 4
            records.append(
                NormalizedRecord(
                    record_id=f"atlassian:{item_identity}:{family}:{cidr}",
                    vendor="atlassian",
                    feed=FEED,
                    family=family,
                    cidr=cidr,
                    source_url=source_url,
                    source_version=source_version,
                    source_published_at=published_at,
                    fetched_at=fetched_at,
                    product=item.get("product") or item.get("service") or item.get("name"),
                    category=item.get("perimeter") or item.get("category"),
                    direction=item.get("direction"),
                    region=item.get("region") or item.get("scope"),
                    extra=item,
                    stale=stale,
                )
            )

    return normalize_records(records)


def collect_atlassian(fetcher: Any, *, previous_state: FeedState | None, snapshot_date: str, fetched_at: str, timeout_seconds: int) -> FeedState:
    try:
        result = fetcher.fetch_json(ATLASSIAN_URL, timeout=timeout_seconds)
        source_version = str(result.payload.get("md5") or result.payload.get("syncToken") or f"sha256:{sha256_hex(result.raw_bytes)}")
        if source_version_matches(previous_state, source_version):
            return clone_state_for_snapshot(previous_state, snapshot_date)

        records = parse_atlassian_payload(
            result.payload,
            fetched_at=fetched_at,
            source_url=ATLASSIAN_URL,
            source_version=source_version,
        )
        manifest = build_manifest(
            vendor="atlassian",
            feed=FEED,
            upstream_url=ATLASSIAN_URL,
            records=records,
            fetch_status="success",
            stale=False,
            source_version=source_version,
            source_published_at=result.payload.get("creationDate"),
            details={
                "creationDate": result.payload.get("creationDate"),
                "syncToken": result.payload.get("syncToken"),
                "md5": result.payload.get("md5"),
                "url": result.payload.get("url"),
            },
        )
        return FeedState(
            snapshot_date=snapshot_date,
            manifest=manifest,
            records=records,
            raw_artifacts={"atlassian-ip-ranges.json": result.payload},
        )
    except Exception as exc:
        if previous_state is None:
            raise
        return stale_fallback(previous_state, snapshot_date, str(exc))
