# Downloading FCC documents

## Getting a list of known FCC grantees

A list of known grantees is available from the FCC in XML format at:

<https://apps.fcc.gov/oetcf/eas/reports/GranteeSearch.cfm>

The XML file that can be downloaded there is not versioned, or time stamped,
and it isn't listed on the website when it was updated, so the only way to
verify if it has been changed is to redownload and compare.

A small hackish script to dump the FCC grant ids to a JSON file with just the
grantee code and grantee name can be found in the `src` directory and is called
`devicecode_dump_fcc_grantees.py` which can be invoked as follows:

```console
$ python3 devicecode_dump_fcc_grantees.py -i results.xml
```

The output of these commands can be used as in input to the FCC document
fetching script, and perform extra sanity checks. Please note that sometimes
grantee codes seem to be retired (although these might not have been used for
actual devices).

## Downloading PDFs from fcc.report

The cleanest and easiest website to download the data from is
[FCC.report][fcc.report] because it is fast and it serves fairly clean HTML
that is easy to process. It should be noted that this website does not seem to
have indexed all FCC documents.

Downloading is fairly trivial: given one or more valid FCC ids grab the HTML
of the overview page, parse the HTML to extract PDF paths and descriptions,
store the original HTML, download the PDFs and store a mapping of PDFs to
descriptions for each valid FCC id.

For example to download the data for the device with FCC id `2AGN7-X9` the
following command could be used:

```console
$ python devicecode_fetch_fcc.py 2AGN7-X9 -o ~/fcc-data
```

To download for multiple FCC ids simply add them:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data 2AGN7-X9 ODMAM5N
```

If there is a list of known FCC grantee codes (see above for an explanation)
and it is stored in the file `known_fcc_grantees_20240618.json` the following
command can be used:

```console
$ python devicecode_fetch_fcc.py 2AGN7-X9 -o ~/fcc-data -g known_fcc_grantees_20240618.json
```

By default any already downloaded data will be skipped. To force
(re)downloading all the data the `--force` parameter can be used:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data --force 2AGN7-X9
```

To not overload the [FCC.report][fcc.report] site with download requests there
is an option to pause a few seconds between each download (currently hardcoded
to 2 seconds) called `--gentle`:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data --gentle 2AGN7-X9
```

Using the `--gentle` option is highly recommended.

To only download the metadata, but not the PDFs themselves, use the `--no-pdf`
flag:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data --no-pdf 2AGN7-X9
```

To not download anything, use the `--no-download` flag:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data --no-download 2AGN7-X9
```

Please note: the `--no-download` flag is only useful when metadata (such as
the file `descriptions.json`) needs to be regenerated for data that had already
been downloaded.

To print more details about what is downloaded use the `--verbose` flag:

```console
$ python devicecode_fetch_fcc.py -o ~/fcc-data --verbose 2AGN7-X9
```

[fcc.report]:https://fcc.report/
