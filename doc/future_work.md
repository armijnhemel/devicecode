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

## Explore using a standard structured data format such as RDF

Data is currently stored as JSON files. It might be good to use a more
structured data format such as RDF, or others, to reap the benefits of using
tools available for those formats (such as SPARQL for RDF).

Alternatively, look at representing a device as a graph.

## Create overlays

The data in these wikis is often incomplete and sometimes incorrect. Creating
overlays that can be enabled/disabled at will to augment the data is a very
helpful mechanism. A good example is the ODM field, where for many devices it
isn't known which ODM made the device. This makes making comparisons between
devices more difficult.

If this information becomes available it can be stored in an overlay separate
from the original data. Existing overlays are:

* FCC dates
* OUI information (networking)
* CPE mapping, plus derived CVE information

### Possible overlays

* CPU type information: for many devices the chip vendor and model are given
  but not the architecture (ARM/MIPS/etc.). By using some lookup table mapping
  model to architecture it should be fairly simple to create these overlays.

## Add software update information/press releases

Crawl firmware update information, such as ChangeLogs or firmware update pages
and press releases to get an indication of when devices were released or
supported. Add this information as an overlay.

## Add information from firmware analysis

A lot of information can be extracted from doing a proper firmware analysis.

## Add information from BoxMatrix (AVM Fritz!Box wiki)

https://boxmatrix.info/wiki/BoxMatrix

## Use purl for package information

Additionally add package information as (approximate) purls.
