# Future work/ideas

This is a list of future work and ideas for this data. Some of it might already
be hidden in some of the data from the Wikis.

## Create metadata for images extracted from FCC documents

The FCC documents often have internal pictures of devices. On these pictures
sometimes the solder pads for a serial port or JTAG can be seen, but these are
not tagged as such. One solution is to let users indicate using some tool and
what the interesting areas of an image are and storing this information. This
information could be stored in a separate file (JSON, YAML, etc.) and then be
consumed by a tool to overlay this information onto the picture when displaying
the image.

OCR/image recognition might work, but for that a test set would first need to
be built, and for that the same task needs to be done anyway.

## Cross correlate OUI values with Wireshark OUI database

Wireshark maintains an automatically generated database with OUI values:

<https://www.wireshark.org/download/automated/data/manuf>

For many devices the OUI values are known, so can be cross correlated. The data
is extracted from Wireshark's source code, so assuming it is under the same
license as Wireshark.

## Explore using a standard structured data format such as RDF

Data is currently stored as JSON files. It might be good to use a more
structured data format such as RDF, or others, to reap the benefits of using
tools available for those formats (such as SPARQL for RDF).

Alternatively, look at representing a device as a graph.

## Create overlays

The data in these wikis is often incomplete and sometimes incorrect. Creating
overlays that can be enabled/disabled at will to augment the data could be very
helpful. A good example is the ODM field, where for many devices it isn't known
which ODM made the device. This makes making comparisons between devices more
difficult.

If this information becomes available it can be stored in an overlay separate
from the original data. A possible overlay could be a reconciliation of data
from the Wikis.

## Add software update information/press releases

Crawl firmware update information, such as ChangeLogs or firmware update pages
and press releases to get an indication of when devices were released or
supported. Add this information as an overlay.
