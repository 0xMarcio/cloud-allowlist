from __future__ import annotations

from collections import defaultdict
from typing import Any

from cloud_allowlist.model import FeedManifest, NormalizedRecord, Snapshot, group_label


VOLATILE_FIELDS = {"fetched_at", "stale", "source_version", "source_published_at", "source_url"}


def _record_group(record: NormalizedRecord) -> str:
    return group_label(record.vendor, record.feed, record.instance)


def _metadata_view(record: NormalizedRecord) -> dict[str, Any]:
    payload = record.to_dict()
    return {key: value for key, value in payload.items() if key not in VOLATILE_FIELDS}


def _metadata_changes(previous: NormalizedRecord, current: NormalizedRecord) -> dict[str, dict[str, Any]]:
    previous_view = _metadata_view(previous)
    current_view = _metadata_view(current)
    changes: dict[str, dict[str, Any]] = {}
    for key in sorted(set(previous_view) | set(current_view)):
        if previous_view.get(key) != current_view.get(key):
            changes[key] = {"from": previous_view.get(key), "to": current_view.get(key)}
    return changes


def build_change_report(previous_snapshot: Snapshot | None, current_snapshot: Snapshot) -> dict[str, Any]:
    if previous_snapshot is None:
        stale_feeds = [
            manifest.to_dict()
            for manifest in current_snapshot.manifests
            if manifest.stale
        ]
        return {
            "from_date": None,
            "to_date": current_snapshot.snapshot_date,
            "has_prior_baseline": False,
            "summary": [],
            "details": {},
            "stale_feeds": stale_feeds,
            "message": "No prior baseline snapshot exists for comparison.",
        }

    previous_records = {record.record_id: record for record in previous_snapshot.records}
    current_records = {record.record_id: record for record in current_snapshot.records}

    detail_groups: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"added": [], "removed": [], "metadata_changed": []}
    )

    for record_id in sorted(set(current_records) - set(previous_records)):
        record = current_records[record_id]
        detail_groups[_record_group(record)]["added"].append(
            {
                "record_id": record.record_id,
                "cidr": record.cidr,
                "metadata": _metadata_view(record),
            }
        )

    for record_id in sorted(set(previous_records) - set(current_records)):
        record = previous_records[record_id]
        detail_groups[_record_group(record)]["removed"].append(
            {
                "record_id": record.record_id,
                "cidr": record.cidr,
                "metadata": _metadata_view(record),
            }
        )

    for record_id in sorted(set(current_records) & set(previous_records)):
        previous_record = previous_records[record_id]
        current_record = current_records[record_id]
        changes = _metadata_changes(previous_record, current_record)
        if changes:
            detail_groups[_record_group(current_record)]["metadata_changed"].append(
                {
                    "record_id": record_id,
                    "cidr": current_record.cidr,
                    "changed_fields": changes,
                }
            )

    for label, hints in current_snapshot.change_hints.items():
        for addition in detail_groups.get(label, {}).get("added", []):
            hint = hints.get(addition["record_id"])
            if hint and hint.get("effectiveDate"):
                addition["effective_date"] = hint["effectiveDate"]

    labels = set(detail_groups)
    labels.update(group_label(manifest.vendor, manifest.feed, manifest.instance) for manifest in current_snapshot.manifests)
    labels.update(group_label(manifest.vendor, manifest.feed, manifest.instance) for manifest in previous_snapshot.manifests)

    summaries: list[dict[str, Any]] = []
    for label in sorted(labels):
        vendor, feed, *instance = label.split("/")
        details = detail_groups.get(label, {"added": [], "removed": [], "metadata_changed": []})
        summaries.append(
            {
                "vendor": vendor,
                "feed": feed,
                "instance": instance[0] if instance else None,
                "added": len(details["added"]),
                "removed": len(details["removed"]),
                "metadata_changed": len(details["metadata_changed"]),
            }
        )

    stale_feeds = [
        manifest.to_dict()
        for manifest in current_snapshot.manifests
        if manifest.stale
    ]

    return {
        "from_date": previous_snapshot.snapshot_date,
        "to_date": current_snapshot.snapshot_date,
        "has_prior_baseline": True,
        "summary": summaries,
        "details": dict(detail_groups),
        "stale_feeds": stale_feeds,
        "message": "No changes detected."
        if not any(item["added"] or item["removed"] or item["metadata_changed"] for item in summaries)
        else None,
    }


def render_change_report_markdown(report: dict[str, Any]) -> str:
    lines = ["# Cloud Allowlist Change Report", ""]
    if not report["has_prior_baseline"]:
        lines.append(f"- Snapshot date: `{report['to_date']}`")
        lines.append(f"- {report['message']}")
    else:
        lines.append(f"- Baseline: `{report['from_date']}`")
        lines.append(f"- Current: `{report['to_date']}`")
        if report.get("message"):
            lines.append(f"- {report['message']}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        if report["summary"]:
            for item in report["summary"]:
                label = f"{item['vendor']}/{item['feed']}"
                if item.get("instance"):
                    label = f"{label}/{item['instance']}"
                lines.append(
                    f"- `{label}`: added {item['added']}, removed {item['removed']}, metadata changed {item['metadata_changed']}"
                )
        else:
            lines.append("- No material changes.")

    if report["stale_feeds"]:
        lines.append("")
        lines.append("## Stale Feeds")
        lines.append("")
        for manifest in report["stale_feeds"]:
            label = group_label(manifest["vendor"], manifest["feed"], manifest.get("instance"))
            lines.append(
                f"- `{label}` using last good snapshot `{manifest.get('last_good_snapshot_date')}`: {manifest.get('error_message', 'upstream fetch failed')}"
            )

    if report.get("details"):
        lines.append("")
        lines.append("## Details")
        lines.append("")
        for label in sorted(report["details"]):
            details = report["details"][label]
            lines.append(f"### `{label}`")
            lines.append("")
            if not any(details.values()):
                lines.append("- No changes.")
                lines.append("")
                continue
            for item in details["added"]:
                suffix = f" (effective {item['effective_date']})" if item.get("effective_date") else ""
                lines.append(f"- Added `{item['cidr']}`{suffix}")
            for item in details["removed"]:
                lines.append(f"- Removed `{item['cidr']}`")
            for item in details["metadata_changed"]:
                changed_fields = ", ".join(sorted(item["changed_fields"]))
                lines.append(f"- Metadata changed for `{item['cidr']}`: {changed_fields}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
