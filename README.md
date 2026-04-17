# cloud-allowlist

`cloud-allowlist` aggregates official machine-readable cloud allowlist feeds into one normalized dataset and emits deterministic files under `dist/` for text consumers, Terraform, Palo Alto, and pfSense. It keeps a small rolling snapshot history under `state/`, writes a daily change report, and reuses the last known good feed data when one upstream is temporarily unavailable.

## Supported sources

- AWS: `https://ip-ranges.amazonaws.com/ip-ranges.json`
- Microsoft 365: version, endpoints, and changes APIs for configurable instances
- GitHub Meta: `https://api.github.com/meta`
- Google `goog.json` and `cloud.json`
- Atlassian IP ranges: `https://ip-ranges.atlassian.com/`

## Repository layout

```text
.
├── .github/workflows/
├── config/sources.yaml
├── dist/
├── src/cloud_allowlist/
├── state/
└── tests/fixtures/
```

Key paths:

- `dist/manifest.json`: run manifest with per-feed status, versions, counts, and stale flags
- `dist/json/`: normalized JSON outputs and vendor slices
- `dist/csv/all.csv`: one row per normalized record
- `dist/txt/`: IP-only line outputs
- `dist/terraform/cloud_allowlist.auto.tfvars.json`: Terraform-friendly map of CIDR lists
- `dist/paloalto/ip/`: Palo Alto-friendly IP lists
- `dist/pfsense/urltable/`: pfSense URL table style lists
- `dist/changes/latest.md`: latest human-readable change report
- `state/history/snapshots/YYYY-MM-DD/normalized.json.gz`: deterministic compressed daily snapshot
- `state/latest/raw/`: latest successful raw upstream payloads

## Local usage

```bash
python -m pip install -e .[dev]
cloud-allowlist update --use-fixtures
pytest -q
```

Live update:

```bash
cloud-allowlist update
```

Historical diff from saved snapshots:

```bash
cloud-allowlist diff --from-date 2026-04-16 --to-date 2026-04-17
```

Validation:

```bash
cloud-allowlist validate
```

## How it works

- All adapters normalize into one canonical record model.
- CIDRs are canonicalized with `ipaddress`.
- Normalized records are sorted deterministically and deduplicated only when every normalized field matches.
- Latest state is file-based only. There is no database and no external service dependency.
- If one vendor fetch fails after a successful prior run, the repo reuses that vendor's last known good normalized data, marks it `stale`, and records the failure in `dist/manifest.json` and the change report.
- If every enabled feed fails, the run exits non-zero instead of silently publishing a fully stale dataset.

## GitHub Actions automation

`/.github/workflows/ci.yml` runs on pushes and pull requests. It installs the package, runs `pytest -q`, and runs a fixture-based smoke build.

`/.github/workflows/update.yml` runs daily and on manual dispatch. It:

- installs the package
- runs tests
- runs `cloud-allowlist update`
- commits `dist/` and `state/` when outputs changed

Normal GitHub Actions enablement is the only manual step outside local execution.

## Consuming generated files

TXT, Palo Alto, and pfSense outputs are IP/CIDR-only and dedupe by CIDR. JSON and CSV retain richer metadata such as Microsoft 365 URLs, service area details, GitHub domains metadata, Google scope, and Atlassian item metadata.

Examples:

- Terraform: load `dist/terraform/cloud_allowlist.auto.tfvars.json`
- Palo Alto: import `dist/paloalto/ip/all.txt` or vendor-specific files such as `dist/paloalto/ip/vendors/github.txt`
- pfSense URL Table: use `dist/pfsense/urltable/all.txt` or vendor-specific files such as `dist/pfsense/urltable/vendors/aws.txt`

Raw GitHub URL examples once the repo is published:

- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/paloalto/ip/all.txt`
- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/paloalto/ip/vendors/github.txt`
- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/pfsense/urltable/all.txt`
- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/pfsense/urltable/vendors/aws.txt`

## Caveats

- GitHub Meta is useful but not exhaustive for every GitHub-hosted service path.
- Microsoft 365 data is instance-based. `Worldwide` is enabled by default, and other supported instances are configurable in `config/sources.yaml`.
- Google publishes both `goog.json` and `cloud.json`; they are separate official feeds with different meanings and remain separate here.
- A stale feed fallback keeps prior data in outputs instead of dropping the vendor entirely, but it is still marked stale until the upstream recovers.
