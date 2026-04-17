# cloud-allowlist

Builds one normalized allowlist dataset from these official feeds:

- AWS
- Microsoft 365
- GitHub Meta
- Google `goog.json`
- Google `cloud.json`
- Atlassian

Outputs are written to `dist/` in:

- JSON
- CSV
- TXT
- Terraform tfvars JSON
- Palo Alto-friendly TXT
- pfSense URL table TXT
- daily change reports

State is file-based under `state/`. There is no database, no Docker, and no external service dependency.

## Run

```bash
python -m pip install -e .[dev]
cloud-allowlist update --use-fixtures
pytest -q
```

Live update:

```bash
cloud-allowlist update
```

Other commands:

```bash
cloud-allowlist diff --from-date YYYY-MM-DD --to-date YYYY-MM-DD
cloud-allowlist validate
```

## Important paths

- `dist/manifest.json`
- `dist/json/all.json`
- `dist/csv/all.csv`
- `dist/txt/all.txt`
- `dist/terraform/cloud_allowlist.auto.tfvars.json`
- `dist/paloalto/ip/`
- `dist/pfsense/urltable/`
- `dist/changes/latest.md`
- `state/history/snapshots/`

## GitHub Actions

- `.github/workflows/ci.yml` runs tests and a fixture-based smoke build.
- `.github/workflows/update.yml` runs daily and on manual dispatch, refreshes data, and commits `dist/` and `state/` when outputs change.

## Notes

- Microsoft 365 is instance-based. `Worldwide` is enabled by default in `config/sources.yaml`.
- If one upstream fails, the last known good data for that feed is reused and marked `stale`.
- GitHub Meta is useful, but not a complete list of every GitHub-hosted network path.
- Google `goog.json` and `cloud.json` are different official feeds and stay separate here.

## Example raw URLs

- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/txt/all.txt`
- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/paloalto/ip/vendors/github.txt`
- `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/pfsense/urltable/vendors/aws.txt`
