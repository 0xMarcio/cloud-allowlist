# cloud-allowlist

## Snapshot

| field | value |
| --- | --- |
| snapshot_date | `2026-04-17` |
| cidrs | 18,262 |
| ipv4_cidrs | 14,065 |
| ipv6_cidrs | 4,197 |
| ipv4_addrs | 152,833,311 |
| ipv6_addrs | 4,397,607,995,573,118,828,935,446,003,741 |

## Feeds

| dataset | cidrs | v4 | v6 | ipv4_addrs | ipv6_addrs | updated | links |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `atlassian` | 373 | 257 | 116 | 75,663 | 4,951,760,526,076,402,573,787,529,218 | `2026-04-07` | [json](dist/json/vendors/atlassian.json) [txt](dist/txt/vendors/atlassian.txt) [pa](dist/paloalto/ip/vendors/atlassian.txt) [pf](dist/pfsense/urltable/vendors/atlassian.txt) [src](https://ip-ranges.atlassian.com/) |
| `aws` | 10,245 | 7,538 | 2,707 | 101,528,654 | 1,578,785,777,412,639,701,612,351,193,101 | `2026-04-17` | [json](dist/json/vendors/aws.json) [txt](dist/txt/vendors/aws.txt) [pa](dist/paloalto/ip/vendors/aws.txt) [pf](dist/pfsense/urltable/vendors/aws.txt) [src](https://ip-ranges.amazonaws.com/ip-ranges.json) |
| `github` | 6,535 | 5,283 | 1,252 | 26,920,412 | 713,292,394,505,268,875,004,521,480,192 | `2026-04-17` | [json](dist/json/vendors/github.json) [txt](dist/txt/vendors/github.txt) [pa](dist/paloalto/ip/vendors/github.txt) [pf](dist/pfsense/urltable/vendors/github.txt) [src](https://api.github.com/meta) |
| `google-cloud` | 910 | 862 | 48 | 16,600,192 | 910,321,142,169,815,768,553,750,528 | `2026-04-17` | [json](dist/json/vendors/google-cloud.json) [txt](dist/txt/vendors/google-cloud.txt) [pa](dist/paloalto/ip/vendors/google-cloud.txt) [pf](dist/pfsense/urltable/vendors/google-cloud.txt) [src](https://www.gstatic.com/ipranges/cloud.json) |
| `google-goog` | 111 | 96 | 15 | 22,112,000 | 2,060,860,680,695,484,717,817,669,877,760 | `2026-04-17` | [json](dist/json/vendors/google-goog.json) [txt](dist/txt/vendors/google-goog.txt) [pa](dist/paloalto/ip/vendors/google-goog.txt) [pf](dist/pfsense/urltable/vendors/google-goog.txt) [src](https://www.gstatic.com/ipranges/goog.json) |
| `m365-worldwide` | 93 | 34 | 59 | 2,514,957 | 39,734,973,839,093,631,714,242,592,786 | `2026-04-17` | [json](dist/json/vendors/m365-worldwide.json) [txt](dist/txt/vendors/m365-worldwide.txt) [pa](dist/paloalto/ip/vendors/m365-worldwide.txt) [pf](dist/pfsense/urltable/vendors/m365-worldwide.txt) [src](https://endpoints.office.com/endpoints/Worldwide?ClientRequestId=2331b645-45d0-42fc-8d84-b83cc2f1ef2b) |

## Outputs

| dataset | cidrs | links |
| --- | --- | --- |
| `all` | 18,262 | [json](dist/json/all.json) [csv](dist/csv/all.csv) [txt](dist/txt/all.txt) |
| `all-ipv4` | 14,065 | [txt](dist/txt/all-ipv4.txt) [pa](dist/paloalto/ip/all-ipv4.txt) [pf](dist/pfsense/urltable/all-ipv4.txt) |
| `all-ipv6` | 4,197 | [txt](dist/txt/all-ipv6.txt) [pa](dist/paloalto/ip/all-ipv6.txt) [pf](dist/pfsense/urltable/all-ipv6.txt) |
| `meta` | - | [manifest](dist/manifest.json) [changes-md](dist/changes/latest.md) [changes-json](dist/changes/latest.json) [tf](dist/terraform/cloud_allowlist.auto.tfvars.json) |
