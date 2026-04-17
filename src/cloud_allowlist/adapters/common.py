from __future__ import annotations

from dataclasses import replace

from cloud_allowlist.model import FeedManifest, FeedState, NormalizedRecord


def clone_state_for_snapshot(previous_state: FeedState, snapshot_date: str, fetch_status: str = "cached") -> FeedState:
    if previous_state.snapshot_date == snapshot_date:
        return previous_state

    manifest = replace(
        previous_state.manifest,
        fetch_status=fetch_status,
        stale=False,
        error_message=None,
        last_good_snapshot_date=None,
    )
    return FeedState(
        snapshot_date=snapshot_date,
        manifest=manifest,
        records=previous_state.records,
        change_hints=previous_state.change_hints,
    )


def stale_fallback(previous_state: FeedState, snapshot_date: str, error_message: str) -> FeedState:
    manifest = replace(
        previous_state.manifest,
        fetch_status="stale-fallback",
        stale=True,
        error_message=error_message,
        last_good_snapshot_date=previous_state.snapshot_date,
    )
    records = [replace(record, stale=True) for record in previous_state.records]
    return FeedState(
        snapshot_date=snapshot_date,
        manifest=manifest,
        records=records,
        change_hints=previous_state.change_hints,
    )


def source_version_matches(previous_state: FeedState | None, source_version: str | None) -> bool:
    return bool(
        previous_state
        and not previous_state.manifest.stale
        and previous_state.manifest.source_version == source_version
    )


def manifest_record_count(records: list[NormalizedRecord]) -> int:
    return len(records)


def build_manifest(
    *,
    vendor: str,
    feed: str,
    upstream_url: str,
    records: list[NormalizedRecord],
    fetch_status: str,
    stale: bool,
    instance: str | None = None,
    source_version: str | None = None,
    source_published_at: str | None = None,
    error_message: str | None = None,
    last_good_snapshot_date: str | None = None,
    details: dict | None = None,
) -> FeedManifest:
    return FeedManifest(
        vendor=vendor,
        feed=feed,
        instance=instance,
        upstream_url=upstream_url,
        record_count=manifest_record_count(records),
        fetch_status=fetch_status,
        stale=stale,
        source_version=source_version,
        source_published_at=source_published_at,
        error_message=error_message,
        last_good_snapshot_date=last_good_snapshot_date,
        details=details or {},
    )
