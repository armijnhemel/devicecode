# Processing FCC documents

Devices coming onto the US market need to have approval from the [FCC][fcc]
before they are allowed to be sold. The FCC test reports are available online
and often include pictures of the device (including internal pictures of the
board), as well as manuals of the devices, and so on, in PDF format.

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

Extracting images makes them easier to browse and reuse, if needed, or easier
for zooming in (at least on Linux). Using `pdfminer.six` these images can
mostly be extracted (there are many variants of PDF that `pdfminer.six`
cannot process correctly). Extracted images are stored per page. Metadata of
images (page number, SHA256, as well as inputs for reconstructed images, see
below) are stored in a top level file for each PDF.

Some of the images in the documents (mostly the internal and external photos)
are stored in the document as multiple images. When extracted individually
these images are quite useless, so they first need to be recombined into a
single image.

Sometimes text on a picture is actually a text overlay in the PDF and it is not
part of the picture (this has mostly been observed in user manuals). These
elements are extracted separately and not recombined. In case of doubt you
should always look at the original PDF file.

Many images are duplicated: quite a few PDFs store the same image multiple
times (sometimes thousands of times) and test companies tend to use the same
templates for their reports. This is why each unique image is stored in a
separate directory with the SHA256 hexdigest value as the name of the file and
the individual files with the same SHA256 value are hardlinks to this file.
Because hardlinks come with restrictions it is mandatory to keep all the FCC
data output on the same disk partition. Deduplication can easily shave off 1/3
of required disk space.

Processing images takes the vast majority of time when processing PDF files.

### Text

Text is extracted and stored per page. Results of analysis of text are stored
in a top level file for each PDF and contains data like page number, plus what
kind of data was (possibly) found.

## Devices used as modules

There are several devices that are used as modules. A good example would be a
wireless networking card in mini-PCI form factor, that is used as a module in
other devices. The FCC pages of these devices often contain multiple documents
but some of them are documents relating to devices in which the module is
integrated, not the module itself.

## Workflow

The next step would be to download the FCC data, using the instructions found
in ["Downloading FCC documents"](downloading_fcc_data.md). It is assumed that
the data was downloaded in the directory `~/fcc-data/` so if you used a
different download directory you need to change the instructions below.

After downloading there are two more steps:

1. processing the downloaded FCC files
2. creating overlay files (used by for example the TUI)

To output the data into for example the directory `~/git/devicecode-data/FCC`
run the `devicecode_process_fcc.py` script as follows:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data 2AGN7-X9
```

Use the `--verbose` flag to output more debugging information:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data --verbose 2AGN7-X9
```

By default not all PDF files are processed. The files that are labeled as
`Test Report` and `RF Exposure Info` are currently skipped. If these should be
processed (not recommended) use the `--process-uninteresting` flag:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data --process-uninteresting 2AGN7-X9
```

PDFs that have already been processed are not reprocessed. To force processing
of already processed PDFs use the `--force` flag:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data --force 2AGN7-X9
```

By default images are processed. They are extracted and written to a directory
after which SHA256 checksums are computed and, if needed, images are stitched.
Processing images takes quite a long time, plus the images take up a lot of
space. To skip processing images use the `--no-images` flag:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data --no-images 2AGN7-X9
```

When supplying multiple FCC ids there is a flag (`-j`) to set the number of
processes (default: 1) that are started to process the files. To start 8
processes:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data -j8 2AGN7-X9
```

This flag only has meaning if more than one FCC id needs to be processed.

Finally there is an option to create a "clean" archive, that does not contain
the extracted images or the full extracted text, just the metadata (SHA256
checksums, descriptions of what text can be found where, or non-copyrightable
information such as IP addresses). This is because some of the FCC documents
are copyrighted (example: user manuals) and cannot be freely redistributed.
With the `--clean-output` option the images and extracted texts are removed
or not written after the PDF files have been processed:

```console
$ python devicecode_process_fcc.py -o ~/git/devicecode-data/FCC -d ~/fcc-data --clean-output 2AGN7-X9
```

[fcc]:https://en.wikipedia.org/wiki/Federal_Communications_Commission
