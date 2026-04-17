# cloud-allowlist

## Snapshot

| field | value |
| --- | --- |
| snapshot_date | `2026-04-17` |
| record_count | 23849 |
| cidrs | 18262 |
| ipv4_cidrs | 14065 |
| ipv6_cidrs | 4197 |
| ipv4_addrs | 152833311 |
| feed_count | 6 |
| stale_feed_count | 0 |

## Feeds

| dataset | records | cidrs | v4 | v6 | ipv4_addrs | updated | links |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `atlassian` | 612 | 373 | 257 | 116 | 75663 | `2026-04-07` | [json](dist/json/vendors/atlassian.json) [txt](dist/txt/vendors/atlassian.txt) [pa](dist/paloalto/ip/vendors/atlassian.txt) [pf](dist/pfsense/urltable/vendors/atlassian.txt) [src](https://ip-ranges.atlassian.com/) |
| `aws` | 15498 | 10245 | 7538 | 2707 | 101528654 | `2026-04-17` | [json](dist/json/vendors/aws.json) [txt](dist/txt/vendors/aws.txt) [pa](dist/paloalto/ip/vendors/aws.txt) [pf](dist/pfsense/urltable/vendors/aws.txt) [src](https://ip-ranges.amazonaws.com/ip-ranges.json) |
| `github` | 6589 | 6535 | 5283 | 1252 | 26920412 | `2026-04-17` | [json](dist/json/vendors/github.json) [txt](dist/txt/vendors/github.txt) [pa](dist/paloalto/ip/vendors/github.txt) [pf](dist/pfsense/urltable/vendors/github.txt) [src](https://api.github.com/meta) |
| `google-cloud` | 910 | 910 | 862 | 48 | 16600192 | `2026-04-17` | [json](dist/json/vendors/google-cloud.json) [txt](dist/txt/vendors/google-cloud.txt) [pa](dist/paloalto/ip/vendors/google-cloud.txt) [pf](dist/pfsense/urltable/vendors/google-cloud.txt) [src](https://www.gstatic.com/ipranges/cloud.json) |
| `google-goog` | 111 | 111 | 96 | 15 | 22112000 | `2026-04-17` | [json](dist/json/vendors/google-goog.json) [txt](dist/txt/vendors/google-goog.txt) [pa](dist/paloalto/ip/vendors/google-goog.txt) [pf](dist/pfsense/urltable/vendors/google-goog.txt) [src](https://www.gstatic.com/ipranges/goog.json) |
| `m365-worldwide` | 129 | 93 | 34 | 59 | 2514957 | `2026-04-17` | [json](dist/json/vendors/m365-worldwide.json) [txt](dist/txt/vendors/m365-worldwide.txt) [pa](dist/paloalto/ip/vendors/m365-worldwide.txt) [pf](dist/pfsense/urltable/vendors/m365-worldwide.txt) [src](https://endpoints.office.com/endpoints/Worldwide?ClientRequestId=2331b645-45d0-42fc-8d84-b83cc2f1ef2b) |

## Outputs

| dataset | cidrs | links |
| --- | --- | --- |
| `all` | 18262 | [json](dist/json/all.json) [csv](dist/csv/all.csv) [txt](dist/txt/all.txt) |
| `all-ipv4` | 14065 | [txt](dist/txt/all-ipv4.txt) [pa](dist/paloalto/ip/all-ipv4.txt) [pf](dist/pfsense/urltable/all-ipv4.txt) |
| `all-ipv6` | 4197 | [txt](dist/txt/all-ipv6.txt) [pa](dist/paloalto/ip/all-ipv6.txt) [pf](dist/pfsense/urltable/all-ipv6.txt) |
| `meta` | - | [manifest](dist/manifest.json) [changes-md](dist/changes/latest.md) [changes-json](dist/changes/latest.json) [tf](dist/terraform/cloud_allowlist.auto.tfvars.json) |
