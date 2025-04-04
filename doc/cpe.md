# Processing CPE and CVE data

Common Platform Enumeration, or [CPE][cpe], is naming convention for software,
hardware, operating systems, and so on, and is used extensively in the security
industry, for example on the NVD CVE pages, where CPEs are used for listing so
called "Known Affected Software Configurations" ([example][cve-2006-2561]) and
can be used as a key to look up CVEs and other security information.

The CPE data is published as a data dump in XML format.

## Cross correlating CPEs with CVE information

Many entries in the [CVE dataset][cvelistv5] have references to CPEs. This
makes it possible to cross correlate CPE and CVE and also find out if there
are known CVEs for devices (regardless of the software has been fixed or not).

Some caveats: there are errors in both datasets. There are duplicate entries
for the same device in the CPE dataset. Two examples from version `5.12` of the
CPE dictionary with timestamp `2025-03-29T03:55:00.679Z` (which might or might
not have been fixed in newer versions) have the same device listed, with
different CPEs, but with the same `title`:

```
$ grep -i Buffalo official-cpe-dictionary_v2.3.xml  |grep -i WHR-HP-G54 | grep cpe-23 | grep -vi firmware
    <cpe-23:cpe23-item name="cpe:2.3:h:buffalo:whr-hp-g54:-:*:*:*:*:*:*:*"/>
    <cpe-23:cpe23-item name="cpe:2.3:h:buffalotech:whr-hp-g54:-:*:*:*:*:*:*:*"/>
$ grep tl-wr743nd official-cpe-dictionary_v2.3.xml  | grep -v firmware | grep cpe-23
    <cpe-23:cpe23-item name="cpe:2.3:h:tp-link:tl-wr743nd:v1:*:*:*:*:*:*:*"/>
    <cpe-23:cpe23-item name="cpe:2.3:h:tp-link:tl-wr743nd_v1:-:*:*:*:*:*:*:*"/>
```

The CVE data uses old or retired CPE for example CVE-2024-9915 which has an old
CPE (`d-link` was renamed to `dlink` at some point) which is still present in
the [Git repository][cve-2024-9915-archive]. Curiously, the NVD website entry
for [CVE-2024-9915][cve-2024-9915] uses the correct CPE, so it seems that the
NVD website is somehow/somewhere cleaned up first.

Sometimes the CPE data contains references to CVEs, but not vice versa, for
example:

```
$ grep CVE official-cpe-dictionary_v2.3.xml  | grep CVEProject | uniq | head -n 5
      <reference href="https://github.com/CVEProject/cvelist/blob/master/2021/32xxx/CVE-2021-32539.json">Advisory</reference>
      <reference href="https://github.com/CVEProject/cvelistV5/blob/main/cves/2024/11xxx/CVE-2024-11493.json">Advisory</reference>
      <reference href="https://github.com/CVEProject/cvelist/blob/master/2021/33xxx/CVE-2021-33974.json">Advisory</reference>
      <reference href="https://github.com/CVEProject/cvelist/blob/master/2023/2xxx/CVE-2023-2762.json">Advisory</reference>
      <reference href="https://github.com/CVEProject/cvelist/blob/master/2023/3xxx/CVE-2023-3897.json">Advisory</reference>
```

These references can be out of date (and some of them actually are), so in the
scripts these are first cross-referenced with known numbers of actually
published and valid CVEs (ignoring the ones that have been rejected).

[cpe]:https://nvd.nist.gov/products/cpe
[cve-2006-2561]:https://nvd.nist.gov/vuln/detail/CVE-2006-2561
[cve-2024-9915]:https://nvd.nist.gov/vuln/detail/CVE-2024-9915
[cve-2024-9915-archive]:https://github.com/CVEProject/cvelistV5/blob/5d27562a7b563760aa456cd42d13a1971a6ef77a/cves/2024/9xxx/CVE-2024-9915.json
[cvelistv5]:https://github.com/CVEProject/cvelistV5
