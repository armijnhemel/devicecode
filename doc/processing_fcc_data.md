# Design: processing FCC documents

Devices coming onto the US market need to have approval from the [FCC][fcc]
before they are allowed to be sold. The FCC test reports are available online
and often include pictures of the device (including internal pictures of the
board), as well as manuals of the devices, and so on.

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
elements are extracted separately and not recombined. In case of doubt you
should always look at the original PDF file.

### Text

Text is extracted and stored per page.

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission
