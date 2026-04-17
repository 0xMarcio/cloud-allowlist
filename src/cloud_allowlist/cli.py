from __future__ import annotations

from argparse import ArgumentParser, Namespace
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import sys
import uuid

from cloud_allowlist.adapters.atlassian import collect_atlassian
from cloud_allowlist.adapters.aws import collect_aws
from cloud_allowlist.adapters.github_meta import collect_github_meta
from cloud_allowlist.adapters.google import GOOGLE_CLOUD_URL, GOOGLE_GOOG_URL, collect_google_feed
from cloud_allowlist.adapters.m365 import collect_m365
from cloud_allowlist.config import RuntimeConfig, load_config
from cloud_allowlist.diffing import build_change_report, render_change_report_markdown
from cloud_allowlist.emitters.csv_out import emit_csv_outputs
from cloud_allowlist.emitters.json_out import emit_json_outputs
from cloud_allowlist.emitters.paloalto_out import emit_paloalto_outputs
from cloud_allowlist.emitters.pfsense_out import emit_pfsense_outputs
from cloud_allowlist.emitters.terraform_out import emit_terraform_outputs
from cloud_allowlist.emitters.txt_out import build_text_collections, emit_txt_outputs
from cloud_allowlist.io_utils import (
    FixtureFetcher,
    LiveFetcher,
    atomic_write_gzip_json,
    atomic_write_json,
    atomic_write_text,
    ensure_directory,
    read_gzip_json,
    read_json,
    utc_now_iso,
    utc_today,
)
from cloud_allowlist.model import FeedManifest, FeedState, Snapshot, group_label, output_name
from cloud_allowlist.normalize import normalize_records


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="cloud-allowlist")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser("update", help="Fetch, normalize, diff, emit, and persist state.")
    update_parser.add_argument("--use-fixtures", action="store_true", help="Use local fixtures instead of live network fetches.")

    diff_parser = subparsers.add_parser("diff", help="Build a historical diff from saved snapshots.")
    diff_parser.add_argument("--from-date", required=True, help="Baseline snapshot date in YYYY-MM-DD format.")
    diff_parser.add_argument("--to-date", required=True, help="Current snapshot date in YYYY-MM-DD format.")

    subparsers.add_parser("validate", help="Validate config, state, and generated outputs.")
    return parser


def _root() -> Path:
    return Path.cwd()


def _config_path(root: Path) -> Path:
    return root / "config" / "sources.yaml"


def _state_dir(root: Path) -> Path:
    return root / "state"


def _dist_dir(root: Path) -> Path:
    return root / "dist"


def _latest_feed_path(root: Path, name: str) -> Path:
    return _state_dir(root) / "latest" / "feeds" / f"{name}.json"


def _latest_raw_path(root: Path, filename: str) -> Path:
    return _state_dir(root) / "latest" / "raw" / filename


def _snapshot_path(root: Path, snapshot_date: str) -> Path:
    return _state_dir(root) / "history" / "snapshots" / snapshot_date / "normalized.json.gz"


def _change_history_path(root: Path, snapshot_date: str, suffix: str) -> Path:
    return _state_dir(root) / "history" / "changes" / f"{snapshot_date}.{suffix}"


def _load_feed_state(root: Path, name: str) -> FeedState | None:
    payload = read_json(_latest_feed_path(root, name))
    if payload is None:
        return None
    return FeedState.from_storage_dict(payload)


def _save_feed_state(root: Path, name: str, state: FeedState) -> None:
    atomic_write_json(_latest_feed_path(root, name), state.to_storage_dict())
    if state.manifest.stale:
        return
    for artifact_name, payload in state.raw_artifacts.items():
        atomic_write_json(_latest_raw_path(root, artifact_name), payload)


def _load_snapshot(root: Path, snapshot_date: str) -> Snapshot:
    path = _snapshot_path(root, snapshot_date)
    if not path.exists():
        raise FileNotFoundError(f"No snapshot exists for {snapshot_date}")
    return Snapshot.from_dict(read_gzip_json(path))


def _find_previous_snapshot(root: Path, snapshot_date: str) -> Snapshot | None:
    snapshots_dir = _state_dir(root) / "history" / "snapshots"
    if not snapshots_dir.exists():
        return None
    candidates = sorted(
        directory.name
        for directory in snapshots_dir.iterdir()
        if directory.is_dir() and directory.name < snapshot_date
    )
    if not candidates:
        return None
    return _load_snapshot(root, candidates[-1])


def _save_snapshot(root: Path, snapshot: Snapshot) -> None:
    atomic_write_gzip_json(_snapshot_path(root, snapshot.snapshot_date), snapshot.to_dict())


def _prune_history(root: Path, keep_days: int) -> None:
    today = date.fromisoformat(utc_today())
    cutoff = today - timedelta(days=keep_days - 1)

    snapshots_dir = _state_dir(root) / "history" / "snapshots"
    if snapshots_dir.exists():
        for child in snapshots_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                child_date = date.fromisoformat(child.name)
            except ValueError:
                continue
            if child_date < cutoff:
                for nested in sorted(child.rglob("*"), reverse=True):
                    if nested.is_file():
                        nested.unlink()
                    elif nested.is_dir():
                        nested.rmdir()
                child.rmdir()

    changes_dir = _state_dir(root) / "history" / "changes"
    if changes_dir.exists():
        for child in changes_dir.iterdir():
            if not child.is_file():
                continue
            try:
                file_date = date.fromisoformat(child.stem)
            except ValueError:
                continue
            if file_date < cutoff:
                child.unlink()


def _load_m365_client_ids(root: Path) -> dict[str, str]:
    path = _state_dir(root) / "m365_client_ids.json"
    return dict(read_json(path, default={}) or {})


def _save_m365_client_ids(root: Path, client_ids: dict[str, str]) -> None:
    atomic_write_json(_state_dir(root) / "m365_client_ids.json", client_ids)


def _get_m365_client_id(root: Path, instance: str, client_ids: dict[str, str]) -> str:
    existing = client_ids.get(instance)
    if existing:
        return existing
    generated = str(uuid.uuid4())
    client_ids[instance] = generated
    _save_m365_client_ids(root, client_ids)
    return generated


def _build_manifest_payload(snapshot: Snapshot) -> dict[str, Any]:
    collections = build_text_collections(snapshot.records)
    per_feed_unique_counts: dict[str, int] = {}
    grouped: dict[str, set[str]] = {}
    for record in snapshot.records:
        key = group_label(record.vendor, record.feed, record.instance)
        grouped.setdefault(key, set()).add(record.cidr)
    for key, values in grouped.items():
        per_feed_unique_counts[key] = len(values)

    feeds: list[dict[str, Any]] = []
    for manifest in sorted(snapshot.manifests, key=lambda item: (item.vendor, item.feed, item.instance or "")):
        payload = manifest.to_dict()
        payload["unique_cidr_count"] = per_feed_unique_counts.get(group_label(manifest.vendor, manifest.feed, manifest.instance), 0)
        feeds.append(payload)

    return {
        "snapshot_date": snapshot.snapshot_date,
        "record_count": len(snapshot.records),
        "cidr_count": len(collections["all"]),
        "vendor_count": len({record.vendor for record in snapshot.records}),
        "feed_count": len(snapshot.manifests),
        "stale_feed_count": sum(1 for manifest in snapshot.manifests if manifest.stale),
        "feeds": feeds,
    }


def _write_change_outputs(root: Path, report: dict[str, Any], current_date: str) -> None:
    markdown = render_change_report_markdown(report)
    dist_changes_dir = _dist_dir(root) / "changes"
    ensure_directory(dist_changes_dir)
    atomic_write_json(dist_changes_dir / "latest.json", report)
    atomic_write_text(dist_changes_dir / "latest.md", markdown)
    atomic_write_json(_change_history_path(root, current_date, "json"), report)
    atomic_write_text(_change_history_path(root, current_date, "md"), markdown)


def _emit_outputs(root: Path, snapshot: Snapshot) -> None:
    manifest_payload = _build_manifest_payload(snapshot)
    dist_dir = _dist_dir(root)
    emit_json_outputs(dist_dir, snapshot, manifest_payload)
    emit_csv_outputs(dist_dir, snapshot.records)
    emit_txt_outputs(dist_dir, snapshot.records)
    emit_terraform_outputs(dist_dir, snapshot.records)
    emit_paloalto_outputs(dist_dir, snapshot.records)
    emit_pfsense_outputs(dist_dir, snapshot.records)


def _build_snapshot(feed_states: list[FeedState], snapshot_date: str) -> Snapshot:
    all_records = normalize_records([record for state in feed_states for record in state.records])
    manifests: list[FeedManifest] = [state.manifest for state in feed_states]
    change_hints = {
        group_label(state.manifest.vendor, state.manifest.feed, state.manifest.instance): state.change_hints
        for state in feed_states
        if state.change_hints
    }
    return Snapshot(
        snapshot_date=snapshot_date,
        records=all_records,
        manifests=manifests,
        change_hints=change_hints,
    )


def run_update(root: Path, *, use_fixtures: bool) -> int:
    config = load_config(_config_path(root))
    snapshot_date = utc_today()
    fetched_at = utc_now_iso()
    fetcher = FixtureFetcher(root / "tests" / "fixtures") if use_fixtures else LiveFetcher(config.user_agent)
    client_ids = _load_m365_client_ids(root)

    ensure_directory(_state_dir(root) / "latest" / "feeds")
    ensure_directory(_state_dir(root) / "latest" / "raw")
    ensure_directory(_state_dir(root) / "history" / "snapshots")
    ensure_directory(_state_dir(root) / "history" / "changes")
    ensure_directory(_dist_dir(root))

    feed_states: list[FeedState] = []

    if "aws" in config.enabled_vendors:
        state = collect_aws(
            fetcher,
            previous_state=_load_feed_state(root, "aws"),
            snapshot_date=snapshot_date,
            fetched_at=fetched_at,
            timeout_seconds=config.default_timeout_seconds,
        )
        feed_states.append(state)

    if "m365" in config.enabled_vendors:
        for instance in config.m365_instances:
            client_id = _get_m365_client_id(root, instance, client_ids)
            state = collect_m365(
                fetcher,
                instance=instance,
                client_request_id=client_id,
                previous_state=_load_feed_state(root, output_name("m365", "m365-endpoints", instance)),
                snapshot_date=snapshot_date,
                fetched_at=fetched_at,
                timeout_seconds=config.default_timeout_seconds,
            )
            feed_states.append(state)

    if "github" in config.enabled_vendors:
        state = collect_github_meta(
            fetcher,
            previous_state=_load_feed_state(root, "github"),
            snapshot_date=snapshot_date,
            fetched_at=fetched_at,
            timeout_seconds=config.github_timeout_seconds,
            api_version=config.github_api_version,
        )
        feed_states.append(state)

    if "google" in config.enabled_vendors:
        goog_state = collect_google_feed(
            fetcher,
            url=GOOGLE_GOOG_URL,
            feed="google-goog",
            previous_state=_load_feed_state(root, "google-goog"),
            snapshot_date=snapshot_date,
            fetched_at=fetched_at,
            timeout_seconds=config.default_timeout_seconds,
        )
        cloud_state = collect_google_feed(
            fetcher,
            url=GOOGLE_CLOUD_URL,
            feed="google-cloud",
            previous_state=_load_feed_state(root, "google-cloud"),
            snapshot_date=snapshot_date,
            fetched_at=fetched_at,
            timeout_seconds=config.default_timeout_seconds,
        )
        feed_states.extend([goog_state, cloud_state])

    if "atlassian" in config.enabled_vendors:
        state = collect_atlassian(
            fetcher,
            previous_state=_load_feed_state(root, "atlassian"),
            snapshot_date=snapshot_date,
            fetched_at=fetched_at,
            timeout_seconds=config.default_timeout_seconds,
        )
        feed_states.append(state)

    if not feed_states:
        raise RuntimeError("No feeds were enabled in config/sources.yaml")

    if all(state.manifest.stale for state in feed_states):
        raise RuntimeError("Every enabled feed failed and stale fallback was used for all of them")

    snapshot = _build_snapshot(feed_states, snapshot_date)
    previous_snapshot = _find_previous_snapshot(root, snapshot_date)
    report = build_change_report(previous_snapshot, snapshot)
    _write_change_outputs(root, report, snapshot_date)
    _save_snapshot(root, snapshot)
    _emit_outputs(root, snapshot)

    for state in feed_states:
        _save_feed_state(root, output_name(state.manifest.vendor, state.manifest.feed, state.manifest.instance), state)

    _prune_history(root, config.history_retention_days)
    _save_m365_client_ids(root, client_ids)
    return 0


def run_diff(root: Path, from_date: str, to_date: str) -> int:
    baseline = _load_snapshot(root, from_date)
    current = _load_snapshot(root, to_date)
    report = build_change_report(baseline, current)
    compare_base = _dist_dir(root) / "changes"
    ensure_directory(compare_base)
    compare_name = f"compare-{from_date}-to-{to_date}"
    atomic_write_json(compare_base / f"{compare_name}.json", report)
    atomic_write_text(compare_base / f"{compare_name}.md", render_change_report_markdown(report))
    return 0


def run_validate(root: Path) -> int:
    config = load_config(_config_path(root))
    client_ids = _load_m365_client_ids(root)
    for instance in config.m365_instances:
        if instance in client_ids:
            uuid.UUID(client_ids[instance])

    manifest_path = _dist_dir(root) / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("dist/manifest.json does not exist. Run `cloud-allowlist update` first.")

    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or "feeds" not in manifest:
        raise ValueError("dist/manifest.json is not valid")

    required_paths = [
        _dist_dir(root) / "json" / "all.json",
        _dist_dir(root) / "csv" / "all.csv",
        _dist_dir(root) / "txt" / "all.txt",
        _dist_dir(root) / "changes" / "latest.md",
        _dist_dir(root) / "changes" / "latest.json",
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing generated file: {path}")
    return 0


def _dispatch(args: Namespace) -> int:
    root = _root()
    if args.command == "update":
        return run_update(root, use_fixtures=args.use_fixtures)
    if args.command == "diff":
        return run_diff(root, args.from_date, args.to_date)
    if args.command == "validate":
        return run_validate(root)
    raise ValueError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
