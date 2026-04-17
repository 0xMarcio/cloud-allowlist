from __future__ import annotations

from typing import Any

from cloud_allowlist.adapters.common import build_manifest, clone_state_for_snapshot, stale_fallback
from cloud_allowlist.model import FeedState, NormalizedRecord, instance_slug
from cloud_allowlist.normalize import normalize_records
from cloud_allowlist.sorting import canonicalize_cidr

FEED = "m365-endpoints"


def version_url(instance: str, client_request_id: str) -> str:
    return f"https://endpoints.office.com/version/{instance}?ClientRequestId={client_request_id}"


def endpoints_url(instance: str, client_request_id: str) -> str:
    return f"https://endpoints.office.com/endpoints/{instance}?ClientRequestId={client_request_id}"


def changes_url(instance: str, version: str, client_request_id: str) -> str:
    return f"https://endpoints.office.com/changes/{instance}/{version}?ClientRequestId={client_request_id}"


def parse_version_payload(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        latest = payload[0].get("latest")
        if latest:
            return str(latest)
    if isinstance(payload, dict):
        latest = payload.get("latest")
        if latest:
            return str(latest)
    raise ValueError("Microsoft 365 version response did not include a latest version")


def _ports_as_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_endpoints_payload(
    payload: list[dict[str, Any]],
    *,
    instance: str,
    source_version: str,
    fetched_at: str,
    source_url: str,
    stale: bool = False,
) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []

    for endpoint in payload:
        endpoint_id = endpoint.get("id")
        for cidr in endpoint.get("ips", []):
            cidr = canonicalize_cidr(cidr)
            family = 6 if ":" in cidr else 4
            records.append(
                NormalizedRecord(
                    record_id=f"m365:{instance}:{endpoint_id}:{family}:{cidr}",
                    vendor="m365",
                    feed=FEED,
                    family=family,
                    cidr=cidr,
                    source_url=source_url,
                    source_version=source_version,
                    fetched_at=fetched_at,
                    instance=instance,
                    service=endpoint.get("serviceArea"),
                    product=endpoint.get("serviceAreaDisplayName"),
                    category=endpoint.get("category"),
                    required=endpoint.get("required"),
                    express_route=endpoint.get("expressRoute"),
                    tcp_ports=_ports_as_string(endpoint.get("tcpPorts")),
                    udp_ports=_ports_as_string(endpoint.get("udpPorts")),
                    extra={
                        "id": endpoint_id,
                        "urls": endpoint.get("urls", []),
                        "notes": endpoint.get("notes"),
                        "serviceArea": endpoint.get("serviceArea"),
                        "serviceAreaDisplayName": endpoint.get("serviceAreaDisplayName"),
                    },
                    stale=stale,
                )
            )

    return normalize_records(records)


def parse_changes_payload(payload: Any, *, instance: str) -> dict[str, dict[str, Any]]:
    hints: dict[str, dict[str, Any]] = {}
    if not isinstance(payload, list):
        return hints

    for entry in payload:
        disposition = str(entry.get("disposition", "")).lower()
        endpoint_id = entry.get("endpointSetId", entry.get("id"))
        effective_date = entry.get("effectiveDate")
        for cidr in entry.get("ips", []):
            cidr = canonicalize_cidr(cidr)
            family = 6 if ":" in cidr else 4
            record_id = f"m365:{instance}:{endpoint_id}:{family}:{cidr}"
            hints[record_id] = {
                "effectiveDate": effective_date,
                "disposition": disposition,
                "endpointSetId": endpoint_id,
                "instance": instance,
            }
    return hints


def collect_m365(
    fetcher: Any,
    *,
    instance: str,
    client_request_id: str,
    previous_state: FeedState | None,
    snapshot_date: str,
    fetched_at: str,
    timeout_seconds: int,
) -> FeedState:
    try:
        version_result = fetcher.fetch_json(version_url(instance, client_request_id), timeout=timeout_seconds)
        current_version = parse_version_payload(version_result.payload)

        if (
            previous_state
            and not previous_state.manifest.stale
            and previous_state.manifest.source_version == current_version
        ):
            return clone_state_for_snapshot(previous_state, snapshot_date)

        endpoints_result = fetcher.fetch_json(endpoints_url(instance, client_request_id), timeout=timeout_seconds)
        records = parse_endpoints_payload(
            endpoints_result.payload,
            instance=instance,
            source_version=current_version,
            fetched_at=fetched_at,
            source_url=endpoints_url(instance, client_request_id),
        )

        change_hints: dict[str, dict[str, Any]] = {}
        raw_artifacts: dict[str, Any] = {
            f"m365-{instance_slug(instance)}-version.json": version_result.payload,
            f"m365-{instance_slug(instance)}-endpoints.json": endpoints_result.payload,
        }
        manifest_details: dict[str, Any] = {"latest": current_version}

        previous_version = previous_state.manifest.source_version if previous_state else None
        if previous_version and previous_version != current_version:
            try:
                changes_result = fetcher.fetch_json(
                    changes_url(instance, previous_version, client_request_id),
                    timeout=timeout_seconds,
                )
                change_hints = parse_changes_payload(changes_result.payload, instance=instance)
                raw_artifacts[f"m365-{instance_slug(instance)}-changes.json"] = changes_result.payload
            except Exception as changes_error:
                manifest_details["changes_error"] = str(changes_error)

        manifest = build_manifest(
            vendor="m365",
            feed=FEED,
            instance=instance,
            upstream_url=endpoints_url(instance, client_request_id),
            records=records,
            fetch_status="success",
            stale=False,
            source_version=current_version,
            details=manifest_details,
        )
        return FeedState(
            snapshot_date=snapshot_date,
            manifest=manifest,
            records=records,
            change_hints=change_hints,
            raw_artifacts=raw_artifacts,
        )
    except Exception as exc:
        if previous_state is None:
            raise
        return stale_fallback(previous_state, snapshot_date, str(exc))
