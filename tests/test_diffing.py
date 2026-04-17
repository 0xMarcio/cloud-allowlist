from __future__ import annotations

from cloud_allowlist.diffing import build_change_report, render_change_report_markdown
from cloud_allowlist.model import FeedManifest, NormalizedRecord, Snapshot


def record(*, record_id: str, cidr: str, service: str | None = None) -> NormalizedRecord:
    return NormalizedRecord(
        record_id=record_id,
        vendor="m365",
        feed="m365-endpoints",
        instance="Worldwide",
        family=6 if ":" in cidr else 4,
        cidr=cidr,
        source_url="fixture://m365",
        source_version="2026041700",
        fetched_at="2026-04-17T00:00:00Z",
        service=service,
        extra={"urls": ["example.com"]},
    )


def manifest() -> FeedManifest:
    return FeedManifest(
        vendor="m365",
        feed="m365-endpoints",
        instance="Worldwide",
        upstream_url="fixture://m365",
        record_count=0,
        fetch_status="success",
        stale=False,
        source_version="2026041700",
    )


def test_change_report_tracks_add_remove_and_metadata() -> None:
    previous = Snapshot(
        snapshot_date="2026-04-16",
        records=[
            record(record_id="keep", cidr="40.96.0.0/13", service="Exchange"),
            record(record_id="remove", cidr="52.112.0.0/14", service="Teams"),
            record(record_id="change", cidr="2603:1036::/38", service="Skype"),
        ],
        manifests=[manifest()],
    )
    current = Snapshot(
        snapshot_date="2026-04-17",
        records=[
            record(record_id="keep", cidr="40.96.0.0/13", service="Exchange"),
            record(record_id="add", cidr="40.104.0.0/15", service="Exchange"),
            record(record_id="change", cidr="2603:1036::/38", service="Teams"),
        ],
        manifests=[manifest()],
        change_hints={
            "m365/m365-endpoints/Worldwide": {
                "add": {"effectiveDate": "2026-04-20T00:00:00Z"}
            }
        },
    )

    report = build_change_report(previous, current)
    summary = report["summary"][0]
    assert summary["added"] == 1
    assert summary["removed"] == 1
    assert summary["metadata_changed"] == 1
    assert report["details"]["m365/m365-endpoints/Worldwide"]["added"][0]["effective_date"] == "2026-04-20T00:00:00Z"

    markdown = render_change_report_markdown(report)
    assert "Metadata changed" in markdown
    assert "effective 2026-04-20T00:00:00Z" in markdown


def test_first_run_change_report_has_no_baseline() -> None:
    current = Snapshot(
        snapshot_date="2026-04-17",
        records=[],
        manifests=[manifest()],
    )
    report = build_change_report(None, current)
    assert report["has_prior_baseline"] is False
    assert report["message"] == "No prior baseline snapshot exists for comparison."
