from __future__ import annotations

from pathlib import Path
import json

from cloud_allowlist.adapters.atlassian import parse_atlassian_payload
from cloud_allowlist.adapters.aws import parse_aws_payload
from cloud_allowlist.adapters.github_meta import parse_github_meta
from cloud_allowlist.adapters.google import parse_google_payload
from cloud_allowlist.adapters.m365 import parse_changes_payload, parse_endpoints_payload, parse_version_payload


FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_parse_aws_fixture() -> None:
    records = parse_aws_payload(load_fixture("aws-ip-ranges.json"), fetched_at="2026-04-17T00:00:00Z", source_url="fixture://aws")
    assert len(records) == 3
    assert records[0].vendor == "aws"
    assert records[0].cidr == "3.5.140.0/22"
    assert any(record.family == 6 for record in records)


def test_parse_m365_fixtures() -> None:
    version = parse_version_payload(load_fixture("m365-version-worldwide.json"))
    records = parse_endpoints_payload(
        load_fixture("m365-endpoints-worldwide.json"),
        instance="Worldwide",
        source_version=version,
        fetched_at="2026-04-17T00:00:00Z",
        source_url="fixture://m365",
    )
    changes = parse_changes_payload(load_fixture("m365-changes-worldwide.json"), instance="Worldwide")
    assert version == "2026041700"
    assert len(records) == 4
    assert records[0].instance == "Worldwide"
    assert records[0].extra["urls"]
    assert changes["m365:Worldwide:1:4:40.104.0.0/15"]["effectiveDate"] == "2026-04-20T00:00:00Z"


def test_parse_github_fixture() -> None:
    records = parse_github_meta(
        load_fixture("github-meta.json"),
        fetched_at="2026-04-17T00:00:00Z",
        source_url="fixture://github",
        source_version="sha256:test",
    )
    sections = {record.section for record in records}
    assert "ssh_keys" not in sections
    assert "hooks" in sections
    assert records[0].extra["domains"]["website"][0] == "github.com"


def test_parse_google_fixtures() -> None:
    goog_records = parse_google_payload(
        load_fixture("google-goog.json"),
        feed="google-goog",
        source_url="fixture://goog",
        fetched_at="2026-04-17T00:00:00Z",
    )
    cloud_records = parse_google_payload(
        load_fixture("google-cloud.json"),
        feed="google-cloud",
        source_url="fixture://cloud",
        fetched_at="2026-04-17T00:00:00Z",
    )
    assert len(goog_records) == 2
    assert len(cloud_records) == 2
    assert {record.feed for record in cloud_records} == {"google-cloud"}


def test_parse_atlassian_fixture() -> None:
    records = parse_atlassian_payload(
        load_fixture("atlassian-ip-ranges.json"),
        fetched_at="2026-04-17T00:00:00Z",
        source_url="fixture://atlassian",
        source_version="syncToken:test",
    )
    cidrs = {record.cidr for record in records}
    assert len(records) == 3
    assert "104.192.136.0/21" in cidrs
    assert "13.52.5.0/24" in cidrs
    assert "2401:1d80:3000::/36" in cidrs
