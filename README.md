# cloud-allowlist

## Snapshot

| field | value |
| --- | --- |
| snapshot_date | `2026-04-17` |
| record_count | 23849 |
| unique_cidrs | 18262 |
| feed_count | 6 |
| stale_feed_count | 0 |

## Feeds

| vendor | feed | instance | records | unique_cidrs | published | version | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `atlassian` | `atlassian-ip-ranges` | `-` | 612 | 373 | `2026-04-07T02:01:27.152558` | `1775527287` | `success` |
| `aws` | `aws-ip-ranges` | `-` | 15498 | 10245 | `2026-04-17-18-27-05` | `1776450425` | `success` |
| `github` | `github-meta` | `-` | 6589 | 6535 | `-` | `sha256:617eb43da216dd03034baff76775c6739bf4cd8f89027737ce11055a815211ba` | `success` |
| `google` | `google-cloud` | `-` | 910 | 910 | `2026-04-17T13:16:23.22253` | `1776456983222` | `success` |
| `google` | `google-goog` | `-` | 111 | 111 | `2026-04-17T13:16:23.22253` | `1776456983222` | `success` |
| `m365` | `m365-endpoints` | `Worldwide` | 129 | 93 | `-` | `2026033100` | `success` |

## Files

| dataset | path |
| --- | --- |
| manifest | `dist/manifest.json` |
| all_json | `dist/json/all.json` |
| all_csv | `dist/csv/all.csv` |
| all_txt | `dist/txt/all.txt` |
| all_txt_ipv4 | `dist/txt/all-ipv4.txt` |
| all_txt_ipv6 | `dist/txt/all-ipv6.txt` |
| terraform | `dist/terraform/cloud_allowlist.auto.tfvars.json` |
| paloalto | `dist/paloalto/ip/all.txt` |
| pfsense | `dist/pfsense/urltable/all.txt` |
| latest_changes_md | `dist/changes/latest.md` |
| latest_changes_json | `dist/changes/latest.json` |
| snapshot_history | `state/history/snapshots/` |

## Raw URLs

| dataset | url |
| --- | --- |
| all_txt | `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/txt/all.txt` |
| github_paloalto | `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/paloalto/ip/vendors/github.txt` |
| aws_pfsense | `https://raw.githubusercontent.com/0xMarcio/cloud-allowlist/main/dist/pfsense/urltable/vendors/aws.txt` |
