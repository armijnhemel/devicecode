# Design: processing FCC documents

Devices coming onto the US market need to have approval from the [FCC][fcc]
before they are allowed to be sold. The FCC test reports are available online
and often include pictures of the device (including internal pictures of the
board), as well as manuals of the devices, and so on.

Many of the documents are probably not redistributable as they are covered by
copyright (example: user manuals provided by companies), but it should be
possible to publish metadata about the documents, such as SHA256 checksums of
PDFs and SHA256 checksums of extracted images or an indication that a certain
phrase or keyword is present on some page of the document.

## Why process FCC data?

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

Many images are duplicated: quite a few PDFs store the same image multiple
times (sometimes thousands of times) and test companies tend to use the same
templates for their reports. This is why each unique image is stored in a
separate directory with the SHA256 hexdigest value as the name of the file and
the individual files with the same SHA256 value are hardlinks to this file.
Because hardlinks come with restrictions it is mandatory to keep all the FCC
data output on the same disk partition.

Deduplication can easily shave off 1/3 of required disk space.

### Text

Text is extracted and stored per page.

Sometimes text on a picture is actually a text overlay in the PDF and it is not
part of the picture (this has mostly been observed in user manuals). These
elements are extracted separately and not recombined. In case of doubt you
should always look at the original PDF file.

## Devices used as modules

There are several devices that are used as modules. A good example would be a
wireless networking card in mini-PCI form factor, that is used as a module in
other devices. The FCC pages of these devices often contain multiple documents
but some of them are documents relating to devices in which the module is
integrated, not the module itself.

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission
