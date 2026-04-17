from __future__ import annotations

from pathlib import Path
import json

from cloud_allowlist.emitters.csv_out import emit_csv_outputs
from cloud_allowlist.emitters.json_out import emit_json_outputs
from cloud_allowlist.emitters.paloalto_out import emit_paloalto_outputs
from cloud_allowlist.emitters.pfsense_out import emit_pfsense_outputs
from cloud_allowlist.emitters.readme_out import emit_readme
from cloud_allowlist.emitters.terraform_out import emit_terraform_outputs
from cloud_allowlist.emitters.txt_out import build_text_collections, emit_txt_outputs
from cloud_allowlist.model import FeedManifest, NormalizedRecord, Snapshot
from cloud_allowlist.normalize import normalize_records


def sample_records() -> list[NormalizedRecord]:
    return normalize_records(
        [
            NormalizedRecord(
                record_id="github:web:4:140.82.112.0/20",
                vendor="github",
                feed="github-meta",
                family=4,
                cidr="140.82.112.0/20",
                source_url="fixture://github",
                source_version="sha256:test",
                fetched_at="2026-04-17T00:00:00Z",
                section="web",
            ),
            NormalizedRecord(
                record_id="aws:4:3.5.140.0/22:AMAZON:ap-northeast-2:ap-northeast-2",
                vendor="aws",
                feed="aws-ip-ranges",
                family=4,
                cidr="3.5.140.0/22",
                source_url="fixture://aws",
                source_version="1760000000",
                fetched_at="2026-04-17T00:00:00Z",
                service="AMAZON",
                region="ap-northeast-2",
            ),
            NormalizedRecord(
                record_id="m365:Worldwide:2:6:2603:1036::/38",
                vendor="m365",
                feed="m365-endpoints",
                instance="Worldwide",
                family=6,
                cidr="2603:1036::/38",
                source_url="fixture://m365",
                source_version="2026041700",
                fetched_at="2026-04-17T00:00:00Z",
            ),
        ]
    )


def test_emitters_write_expected_files(tmp_path: Path) -> None:
    records = sample_records()
    snapshot = Snapshot(
        snapshot_date="2026-04-17",
        records=records,
        manifests=[
            FeedManifest(vendor="aws", feed="aws-ip-ranges", upstream_url="fixture://aws", record_count=1, fetch_status="success", stale=False),
            FeedManifest(vendor="github", feed="github-meta", upstream_url="fixture://github", record_count=1, fetch_status="success", stale=False),
            FeedManifest(vendor="m365", feed="m365-endpoints", instance="Worldwide", upstream_url="fixture://m365", record_count=1, fetch_status="success", stale=False),
        ],
    )
    manifest_payload = {
        "snapshot_date": "2026-04-17",
        "feeds": [
            {
                "dataset": "aws",
                "vendor": "aws",
                "feed": "aws-ip-ranges",
                "upstream_url": "fixture://aws",
                "record_count": 1,
                "unique_cidr_count": 1,
                "ipv4_cidr_count": 1,
                "ipv6_cidr_count": 0,
                "ipv4_address_count": 1024,
                "updated_at": "2026-04-17T00:00:00Z",
            }
        ],
        "record_count": len(records),
        "cidr_count": 3,
        "ipv4_cidr_count": 2,
        "ipv6_cidr_count": 1,
        "ipv4_address_count": 5121,
        "feed_count": 3,
        "stale_feed_count": 0,
    }

    emit_json_outputs(tmp_path, snapshot, manifest_payload)
    emit_csv_outputs(tmp_path, records)
    emit_txt_outputs(tmp_path, records)
    emit_terraform_outputs(tmp_path, records)
    emit_paloalto_outputs(tmp_path, records)
    emit_pfsense_outputs(tmp_path, records)
    emit_readme(tmp_path, manifest_payload)

    assert (tmp_path / "json" / "all.json").exists()
    assert (tmp_path / "csv" / "all.csv").exists()
    assert (tmp_path / "txt" / "all.txt").read_text(encoding="utf-8").endswith("\n")
    assert (tmp_path / "txt" / "vendors" / "aws.txt").exists()
    assert (tmp_path / "paloalto" / "ip" / "all.txt").exists()
    assert (tmp_path / "pfsense" / "urltable" / "all.txt").exists()
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "| dataset | records | cidrs | v4 | v6 | ipv4_addrs | updated | links |" in readme
    assert "[json](dist/json/vendors/aws.json)" in readme
    tfvars = json.loads((tmp_path / "terraform" / "cloud_allowlist.auto.tfvars.json").read_text(encoding="utf-8"))
    assert "cloud_allowlist" in tfvars


def test_text_collections_are_deterministic() -> None:
    records = sample_records()
    reversed_records = list(reversed(records))
    assert build_text_collections(records) == build_text_collections(reversed_records)
