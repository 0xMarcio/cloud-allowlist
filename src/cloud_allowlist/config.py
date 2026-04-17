from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re


@dataclass(frozen=True)
class RuntimeConfig:
    enabled_vendors: list[str]
    m365_instances: list[str]
    default_timeout_seconds: int
    github_timeout_seconds: int
    user_agent: str
    github_api_version: str | None
    history_retention_days: int
    outputs: dict[str, bool]


def _strip_comments(line: str) -> str:
    if line.lstrip().startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", line).rstrip("\n")


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text == "":
        return ""
    if text.startswith("'") and text.endswith("'"):
        return text[1:-1]
    if text.startswith('"') or text.startswith("[") or text.startswith("{"):
        return json.loads(text)
    if text in {"true", "false", "null"} or re.fullmatch(r"-?\d+", text):
        return json.loads(text)
    return text


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        candidate = _strip_comments(raw_line)
        if not candidate.strip():
            continue

        indent = len(candidate) - len(candidate.lstrip(" "))
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        key, separator, value = candidate.strip().partition(":")
        if separator != ":":
            raise ValueError(f"Invalid config line: {raw_line}")

        container = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            container[key.strip()] = child
            stack.append((indent, child))
        else:
            container[key.strip()] = _parse_scalar(value.strip())

    return root


def load_config(path: Path) -> RuntimeConfig:
    payload = parse_simple_yaml(path.read_text(encoding="utf-8"))
    outputs = payload.get("outputs", {})

    config = RuntimeConfig(
        enabled_vendors=list(payload.get("enabled_vendors", [])),
        m365_instances=list(payload.get("m365_instances", ["Worldwide"])),
        default_timeout_seconds=int(payload.get("timeouts", {}).get("default_seconds", 20)),
        github_timeout_seconds=int(payload.get("timeouts", {}).get("github_seconds", 20)),
        user_agent=str(payload.get("http", {}).get("user_agent", "cloud-allowlist/0.1")),
        github_api_version=payload.get("http", {}).get("github_api_version"),
        history_retention_days=int(payload.get("history_retention_days", 35)),
        outputs={key: bool(value) for key, value in outputs.items()},
    )
    validate_config(config)
    return config


def validate_config(config: RuntimeConfig) -> None:
    valid_vendors = {"aws", "m365", "github", "google", "atlassian"}
    invalid_vendors = sorted(set(config.enabled_vendors) - valid_vendors)
    if invalid_vendors:
        raise ValueError(f"Unsupported vendors in config: {', '.join(invalid_vendors)}")

    if config.history_retention_days < 1:
        raise ValueError("history_retention_days must be at least 1")

    if not config.m365_instances:
        raise ValueError("At least one Microsoft 365 instance must be configured")
