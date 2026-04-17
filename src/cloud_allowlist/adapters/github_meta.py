from __future__ import annotations

from typing import Any

from cloud_allowlist.adapters.common import build_manifest, clone_state_for_snapshot, source_version_matches, stale_fallback
from cloud_allowlist.io_utils import sha256_hex
from cloud_allowlist.model import FeedState, NormalizedRecord
from cloud_allowlist.normalize import normalize_records
from cloud_allowlist.sorting import canonicalize_cidr

GITHUB_META_URL = "https://api.github.com/meta"
FEED = "github-meta"


def parse_github_meta(payload: dict[str, Any], *, fetched_at: str, source_url: str, source_version: str, stale: bool = False) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    domains = payload.get("domains", {})

    for section, value in payload.items():
        if not isinstance(value, list):
            continue
        cidrs: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            try:
                cidrs.append(canonicalize_cidr(item))
            except ValueError:
                continue
        for cidr in cidrs:
            family = 6 if ":" in cidr else 4
            records.append(
                NormalizedRecord(
                    record_id=f"github:{section}:{family}:{cidr}",
                    vendor="github",
                    feed=FEED,
                    family=family,
                    cidr=cidr,
                    source_url=source_url,
                    source_version=source_version,
                    fetched_at=fetched_at,
                    section=section,
                    extra={"domains": domains},
                    stale=stale,
                )
            )

    return normalize_records(records)


def collect_github_meta(
    fetcher: Any,
    *,
    previous_state: FeedState | None,
    snapshot_date: str,
    fetched_at: str,
    timeout_seconds: int,
    api_version: str | None,
) -> FeedState:
    headers = {"Accept": "application/vnd.github+json"}
    if api_version:
        headers["X-GitHub-Api-Version"] = api_version

    try:
        result = fetcher.fetch_json(GITHUB_META_URL, headers=headers, timeout=timeout_seconds)
        source_version = f"sha256:{sha256_hex(result.raw_bytes)}"
        if source_version_matches(previous_state, source_version):
            return clone_state_for_snapshot(previous_state, snapshot_date)

        records = parse_github_meta(
            result.payload,
            fetched_at=fetched_at,
            source_url=GITHUB_META_URL,
            source_version=source_version,
        )
        manifest = build_manifest(
            vendor="github",
            feed=FEED,
            upstream_url=GITHUB_META_URL,
            records=records,
            fetch_status="success",
            stale=False,
            source_version=source_version,
            details={"domains": result.payload.get("domains", {})},
        )
        return FeedState(
            snapshot_date=snapshot_date,
            manifest=manifest,
            records=records,
            raw_artifacts={"github-meta.json": result.payload},
        )
    except Exception as exc:
        if previous_state is None:
            raise
        return stale_fallback(previous_state, snapshot_date, str(exc))
