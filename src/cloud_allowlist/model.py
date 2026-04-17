from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


def _clean_mapping(value: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, item in value.items():
        if item is None:
            continue
        cleaned[key] = item
    return cleaned


@dataclass(frozen=True)
class NormalizedRecord:
    record_id: str
    vendor: str
    feed: str
    family: int
    cidr: str
    source_url: str
    fetched_at: str
    instance: str | None = None
    section: str | None = None
    service: str | None = None
    product: str | None = None
    category: str | None = None
    direction: str | None = None
    region: str | None = None
    network_border_group: str | None = None
    source_version: str | None = None
    source_published_at: str | None = None
    required: bool | None = None
    express_route: bool | None = None
    tcp_ports: str | None = None
    udp_ports: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    stale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _clean_mapping(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NormalizedRecord":
        return cls(**payload)


@dataclass(frozen=True)
class FeedManifest:
    vendor: str
    feed: str
    upstream_url: str
    record_count: int
    fetch_status: str
    stale: bool
    instance: str | None = None
    source_version: str | None = None
    source_published_at: str | None = None
    error_message: str | None = None
    last_good_snapshot_date: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _clean_mapping(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FeedManifest":
        return cls(**payload)


@dataclass
class FeedState:
    snapshot_date: str
    manifest: FeedManifest
    records: list[NormalizedRecord]
    change_hints: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_artifacts: dict[str, Any] = field(default_factory=dict)

    def to_storage_dict(self) -> dict[str, Any]:
        return {
            "snapshot_date": self.snapshot_date,
            "manifest": self.manifest.to_dict(),
            "records": [record.to_dict() for record in self.records],
            "change_hints": self.change_hints,
        }

    @classmethod
    def from_storage_dict(cls, payload: dict[str, Any]) -> "FeedState":
        return cls(
            snapshot_date=payload["snapshot_date"],
            manifest=FeedManifest.from_dict(payload["manifest"]),
            records=[NormalizedRecord.from_dict(item) for item in payload.get("records", [])],
            change_hints=payload.get("change_hints", {}),
        )


@dataclass
class Snapshot:
    snapshot_date: str
    records: list[NormalizedRecord]
    manifests: list[FeedManifest]
    change_hints: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_date": self.snapshot_date,
            "records": [record.to_dict() for record in self.records],
            "manifests": [manifest.to_dict() for manifest in self.manifests],
            "change_hints": self.change_hints,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Snapshot":
        return cls(
            snapshot_date=payload["snapshot_date"],
            records=[NormalizedRecord.from_dict(item) for item in payload.get("records", [])],
            manifests=[FeedManifest.from_dict(item) for item in payload.get("manifests", [])],
            change_hints=payload.get("change_hints", {}),
        )


def instance_slug(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def output_name(vendor: str, feed: str, instance: str | None = None) -> str:
    if vendor == "aws":
        return "aws"
    if vendor == "m365":
        return f"m365-{instance_slug(instance or 'worldwide')}"
    if vendor == "github":
        return "github"
    if vendor == "google":
        return feed
    if vendor == "atlassian":
        return "atlassian"
    return f"{vendor}-{feed}"


def terraform_vendor_key(vendor: str, feed: str, instance: str | None = None) -> str:
    return output_name(vendor, feed, instance).replace("-", "_")


def group_label(vendor: str, feed: str, instance: str | None = None) -> str:
    if instance:
        return f"{vendor}/{feed}/{instance}"
    return f"{vendor}/{feed}"
