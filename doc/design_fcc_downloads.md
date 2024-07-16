# Design: downloading and processing FCC documents

Devices coming onto the US market need to have approval from the [FCC][fcc]
before they are allowed to be sold. The FCC test reports are available online
and often include pictures of the device (including internal pictures of the
board), as well as manuals of the devices, and so on.

## Why not just provide the documents?

Data created for and published by the US government is public domain so it
can be redownloaded, mined and remixed but this does most likely not extend
to any data provided by the manufacturer such as manuals, leaflets, and so
on. This is why instead of providing the data directly scripts to download the
data are provided.

## FCC ids

Each device is assigned an identifier by the FCC, a so called FCC id. Some
devices (but not all, for example devices that are not intended for the US
market) in the TechInfoDepot and WikiDevi data have one or more FCC ids
associated with them. The FCC id consists of a vendor part, and a device
specific part. FCC ids makes it easier to make connections between devices
to see if they are identical.

FCC ids can apply to multiple devices (example: they contain identical
hardware) and some devices can have multiple FCC ids (example: there are
multiple devices in a single box, each with a separate FCC id).

## FCC website

All the documents are published on the FCC website, which, like many US
government websites, is horribly slow and not very good for downloading data
in bulk, or for searching. As a result there are various websites that index
the FCC website, republish the documents and offer search functionality.
Some these were mainly created to serve advertisements.

Automatically querying the main FCC website is not doable: it is very slow
and output is ugly.

## Storing FCC data

Because there is not a 1:1 correlation between FCC ids and devices the FCC
data is stored separately from devices in a subdirectory with the name of
the FCC id.

## Processing FCC data

The FCC website (and its clones) make the relevant documents available in
PDF format. The most interesting documents are probably the external/internal
photos, which often clearly show some of the used chips and solder pads (useful
for identifying serial ports), and the user manuals, which can be mined for
descriptions of functionality, default ports, default user names and passwords,
and so on. Sometimes the user manual contains open source license texts and a
written offer for source code.

### Images

Some of the images in the documents (mostly the internal and external photos)
are stored in the document as multiple images. When extracted individually
these images are quite useless, so they first need to be recombined into a
single image. Extracted images are stored per page.

Sometimes text on a picture is actually a text overlay in the PDF and it is not
part of the picture (this has mostly been observed in user manuals). These
elements are extracted separately and not recombined. In case of doubt always
look at the original PDF file.

### Text

Text is extracted and stored per page.

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission
