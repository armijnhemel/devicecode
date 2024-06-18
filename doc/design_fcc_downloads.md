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

## FCC website

All the documents are published on the FCC website, which, like many US
government websites, is horribly slow and not very good for downloading data
in bulk, or for searching. As a result there are various websites that index
the FCC website, republish the documents and offer search functionality,
all while also serving advertisments.

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission
