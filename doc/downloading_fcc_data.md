# Downloading FCC documents

## Getting a list of known FCC grantees

A list of known grantees is available from the FCC in XML format at:

<https://apps.fcc.gov/oetcf/eas/reports/GranteeSearch.cfm>

The XML file that can be downloaded there is not versioned, or time stamped,
and it isn't listed on the website when it was updated, so the only way to
verify if it has been changed is to redownload and compare.

A small hackish script to dump the FCC grant ids can be found in the `src`
directory and is called `devicecode_dump_fcc_grantees.py` which can be
invoked as follows:

```
$ python3 devicecode_dump_fcc_grantees.py -i results.xml
```

Alternatively you can use a (much faster) shell command (the dump script
performs some extra XML sanity checks):

```
$ grep grantee_code results.xml | cut -f 2 -d '>' | cut -f 1 -d '<'
```

The output of these commands can be used as in input to the FCC document
fetching script, and perform extra sanity checks.

## Downloading PDFs from fcc.report

The cleanest and easiest website to download the data from is
[FCC.report][fcc.report] because it is fast and it serves fairly clean HTML
that is easy to process.

Downloading is fairly trivial: given a valid FCC id grab the HTML of the
overview page, parse the HTML to extract PDF paths and descriptions, store
the original HTML, download the PDFs and store a mapping of PDFs to
descriptions.

For example to download the data for the device with FCC id `2AGN7-X9` the
following command could be used:

```
$ python devicecode_fetch_fcc.py 2AGN7-X9 -o ~/fcc-data
```

If there is a list of known FCC grantee codes (see above for an explanation)
and it is stored in the file `known_fcc_grantees_20240618.txt` the following
command can be used:

```
$ python devicecode_fetch_fcc.py 2AGN7-X9 -o ~/fcc-data -g known_fcc_grantees_20240618.txt
```

To force downloading all the data the `--force` parameter can be used:

```
$ python devicecode_fetch_fcc.py 2AGN7-X9 -o ~/fcc-data --force
```

[fcc.report]:https://fcc.report/
