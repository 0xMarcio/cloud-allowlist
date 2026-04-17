from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import gzip
import hashlib
import json
import shutil
import urllib.error
import urllib.request


@dataclass(frozen=True)
class FetchResult:
    url: str
    payload: Any
    raw_bytes: bytes
    headers: dict[str, str]
    status: int


class LiveFetcher:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def fetch_json(self, url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> FetchResult:
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(url, headers=request_headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_bytes = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                raw_bytes = gzip.decompress(raw_bytes)
            payload = json.loads(raw_bytes.decode("utf-8"))
            return FetchResult(
                url=url,
                payload=payload,
                raw_bytes=raw_bytes,
                headers=dict(response.headers.items()),
                status=response.status,
            )


class FixtureFetcher:
    def __init__(self, fixture_root: Path, failing_patterns: set[str] | None = None) -> None:
        self.fixture_root = fixture_root
        self.failing_patterns = failing_patterns or set()

    def fetch_json(self, url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> FetchResult:
        del headers
        del timeout
        for pattern in self.failing_patterns:
            if pattern in url:
                raise urllib.error.URLError(f"Fixture fetch blocked for pattern: {pattern}")

        fixture_path = self._resolve_fixture(url)
        raw_bytes = fixture_path.read_bytes()
        return FetchResult(
            url=url,
            payload=json.loads(raw_bytes.decode("utf-8")),
            raw_bytes=raw_bytes,
            headers={},
            status=200,
        )

    def _resolve_fixture(self, url: str) -> Path:
        if url == "https://ip-ranges.amazonaws.com/ip-ranges.json":
            return self.fixture_root / "aws-ip-ranges.json"
        if url == "https://api.github.com/meta":
            return self.fixture_root / "github-meta.json"
        if url == "https://www.gstatic.com/ipranges/goog.json":
            return self.fixture_root / "google-goog.json"
        if url == "https://www.gstatic.com/ipranges/cloud.json":
            return self.fixture_root / "google-cloud.json"
        if url == "https://ip-ranges.atlassian.com/":
            return self.fixture_root / "atlassian-ip-ranges.json"
        if "https://endpoints.office.com/version/" in url:
            instance = url.split("/version/")[1].split("?", 1)[0].lower()
            return self.fixture_root / f"m365-version-{instance}.json"
        if "https://endpoints.office.com/endpoints/" in url:
            instance = url.split("/endpoints/")[1].split("?", 1)[0].lower()
            return self.fixture_root / f"m365-endpoints-{instance}.json"
        if "https://endpoints.office.com/changes/" in url:
            remainder = url.split("/changes/")[1].split("?", 1)[0]
            instance = remainder.split("/", 1)[0].lower()
            return self.fixture_root / f"m365-changes-{instance}.json"
        raise FileNotFoundError(f"No fixture mapping for URL: {url}")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    atomic_write_text(path, f"{text}\n")


def atomic_write_gzip_json(path: Path, payload: Any) -> None:
    ensure_directory(path.parent)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    json_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with temp_path.open("wb") as handle:
        with gzip.GzipFile(fileobj=handle, mode="wb", mtime=0) as gz_file:
            gz_file.write(json_bytes)
    temp_path.replace(path)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_gzip_json(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
