# Processing CPE, CVE and Exploit DB data

Common Platform Enumeration, or [CPE][cpe], is naming convention for software,
hardware, operating systems, and so on, and is used extensively in the security
industry, for example on the NVD CVE pages, where CPEs are used for listing so
called "Known Affected Software Configurations" ([example][cve-2006-2561]) and
can be used as a key to look up CVEs and other security information.

The CPE data is published by NIST as a data dump in XML format.

The script to create overlays for CPE, as well as CVE (more about that later)
is called `cpe_overlay.py` and can be used as follows:

```
$ python cpe_overlay.py -d /path/to/devices/data -o /path/to/output/data -c /path/to/cpe/dictionary
```

for example:

```
$ python cpe_overlay.py -d ~/git/devicecode-data/ -o ~/git/devicecode-data/ -c official-cpe-dictionary_v2.3.xml
```

This script will read the CPE XML file (which is over 630 MiB in size) and try
to match devices to CPEs, using a number of metrics, such as:

* device name
* shared references (like product pages)

This isn't a perfect match and CPE suffers from issues. For example, the CPE
dictionary contains duplicate information, where people have assigned different
CPEs to the same device. There are many such duplicate entries. Two examples
from version `5.12` of the CPE dictionary with timestamp
`2025-03-29T03:55:00.679Z` (which might or might not have been fixed in newer
versions) have the same device listed, with different CPEs, but with the same
`title`:

```
$ grep -i Buffalo official-cpe-dictionary_v2.3.xml  |grep -i WHR-HP-G54 | grep cpe-23 | grep -vi firmware
    <cpe-23:cpe23-item name="cpe:2.3:h:buffalo:whr-hp-g54:-:*:*:*:*:*:*:*"/>
    <cpe-23:cpe23-item name="cpe:2.3:h:buffalotech:whr-hp-g54:-:*:*:*:*:*:*:*"/>
$ grep tl-wr743nd official-cpe-dictionary_v2.3.xml  | grep -v firmware | grep cpe-23
    <cpe-23:cpe23-item name="cpe:2.3:h:tp-link:tl-wr743nd:v1:*:*:*:*:*:*:*"/>
    <cpe-23:cpe23-item name="cpe:2.3:h:tp-link:tl-wr743nd_v1:-:*:*:*:*:*:*:*"/>
```

These errors make it difficult to create a good mapping.

To create overlays for only one of the Wiki types pass the `--wiki-type`
parameter to the script.

## Cross correlating CPEs with CVE information

Many entries in the [CVE dataset][cvelistv5] have references to CPEs. This
makes it possible to cross correlate CPE and CVE and also find out if there
are known CVEs for devices (regardless of the software has been fixed or not):
if a CPE is known for a device, and a CVE is known for that CPE, then it can
be concluded that the CVE is relevant to some (or all) instances of that
device.

Creating this mapping is easier said than done, as like CPEs the CVE data has
its share of incorrect or incomplete data, and CPE and CVE aren't kept in sync.
The CVE data uses old or retired CPEs, for example CVE-2024-9915, which has the
old CPE `cpe:2.3:h:d-link:dir-619l_b1:*:*:*:*:*:*:*:*` (as `d-link` was renamed
to `dlink` at some point in the official CPE dictionary). This error is still
present in a recent [Git repository][cve-2024-9915-archive] snapshot.
Surprisingly, the NVD website entry for [CVE-2024-9915][cve-2024-9915] uses a
corrected CPE, so it seems that the data that is used for the NVD website is
cleaned up first, but changes are not applied to the official Git repository.

There seems to be an extra data source for the data on the NVD website. As
an example, [CVE-2004-1790][cve-2004-1790-nvd] contains a CPE for a device, but
the official CPE dictionary does not have an entry for this particular device
and the cvelist5 repository also doesn't have it. It is available in the
[FKIE-cad][fkie-cad-nvd] data feed.

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

To create CVE overlays the `cpe_overlay.py` script should be called with an
extra parameter, namely the location of a clone of the
[CVE dataset][cvelistv5]:

```
$ python cpe_overlay.py -d /path/to/devices/data -o /path/to/output/data -c /path/to/cpe/dictionary -e /path/to/cves
```

for example:

```
$ python cpe_overlay.py -d ~/git/devicecode-data/ -o ~/git/devicecode-data/ -c official-cpe-dictionary_v2.3.xml -e ~/git/cvelistV5/
```

## Cross correlating CPEs with Exploit DB information, via CVEs

Using an extra indirection it is also possible to link known Exploits to CPEs
(and thus to devices). The public [Exploit DB](exploitdb) dataset has exploits
that are linked to CVEs. By linking those to CPEs and devices it is possible to
find exploits for devices.

To generate overlays for exploitdb a checkout of the Git repository of the data
is needed. This can then be supplied to the overlay creation script:

```
$ python cpe_overlay.py -d /path/to/devices/data -o /path/to/output/data -c /path/to/cpe/dictionary -e /path/to/cves --exploitdb=/path/to/exploitdb
```

for example:

```
$ python cpe_overlay.py -d ~/git/devicecode-data/ -o ~/git/devicecode-data/ -c official-cpe-dictionary_v2.3.xml -e ~/git/cvelistV5/ --exploitdb=/home/devicecode/git/exploitdb/
```

[cpe]:https://nvd.nist.gov/products/cpe
[cve-2006-2561]:https://nvd.nist.gov/vuln/detail/CVE-2006-2561
[cve-2024-9915]:https://nvd.nist.gov/vuln/detail/CVE-2024-9915
[cve-2024-9915-archive]:https://github.com/CVEProject/cvelistV5/blob/5d27562a7b563760aa456cd42d13a1971a6ef77a/cves/2024/9xxx/CVE-2024-9915.json
[cvelistv5]:https://github.com/CVEProject/cvelistV5
[exploitdb]:https://gitlab.com/exploit-database/exploitdb
[cve-2004-1790-nvd]:https://nvd.nist.gov/vuln/detail/CVE-2004-1790
[fkie-cad-nvd]:https://github.com/fkie-cad/nvd-json-data-feeds
