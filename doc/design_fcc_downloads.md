# Design: downloading and processing FCC documents

Devices coming onto the US market need to have approval from the [FCC][fcc]
before they are allowed to be sold. The FCC test reports are available online
and often include pictures of the device (including internal pictures of the
board), as well as manuals of the devices, and so on. Data created for and
published by the US government is public domain so it can be redownloaded,
mined and remixed (it should be noted that this does most likely not extend
to any data provided by the manufacturer such as manuals, leaflets, and so
on).

## FCC ids

Each device is assigned an identifier from the FCC, or a so called FCC id. Some
devices (but not all, for example devices that are not intended for the US
market) in the TechInfoDepot and WikiDevi data have one or more FCC ids
associated with them. The FCC id consists of a vendor part, and a device
specific part.

FCC ids can apply to multiple devices (example: they contain identical
hardware) and some devices can have multiple FCC ids (example: there are
multiple devices in a single box, each with a separate FCC id). This makes
it easier to make connections between devices to see if they are identical.

## FCC websites

All the documents are published on the FCC website, which, like many US
government websites, is horribly slow and not very good for downloading data
in bulk, or for searching. As a result there are various websites that index
the FCC website, republish the documents and offer search functionality.
Some these were mainly created to serve advertisements.

Automatically querying the main FCC website is not doable: it is very slow
and output is ugly.

### Getting a list of known FCC grantees

A list of known grantees is available from the FCC in XML format at:

<https://apps.fcc.gov/oetcf/eas/reports/GranteeSearch.cfm>

The XML file that can be downloaded there is not versioned, or time stamped,
and it isn't listed on the website when it was updated, so the only way to
verify is redownload and compare.

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

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission