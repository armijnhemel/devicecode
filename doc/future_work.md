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
