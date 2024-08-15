#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import pathlib
import re
import sys

import click
import pdfminer
import PIL.Image
from pdfminer.high_level import extract_pages

import devicecode_defaults as defaults

# mapping of texts to functionality
TEXT_TO_FUNCTIONALITY = {
    'upnp': 'UPnP',
    'telnet': 'telnet',
    'syslog': 'syslog',
}

PROGRAMS = ['arptables', 'bpalogin', 'bridge-utils', 'busybox', 'ebtables', 'glibc',
            'hostapd', 'iproute', 'ipset', 'iptables', 'iputils', 'linux', 'nmap', 'ppp',
            'pptpd', 'rp-pppoe', 'wireless_tools', 'wpa_supplicant']

# names of files used as descriptions that could possibly contain hints about devices
# like MiniPCIe cards being embedded or used in other devices where the FCC id would
# serve as a secondary FCC id, and not as the primary.
# As an example: PPD-AR5B95
CLASS2_PERMISSIVE = ['2adwc-ai7688h_cvrltr_fcc class ii permissive change',
                     'class 2 permissive change', 'class 2 permissive change letter',
                     'class ii change letter', 'class ii change request', 'class ii cover letter',
                     'class ii letter', 'class ii pc letter 1', 'class ii permisive change letter',
                     'class ii permissive change', 'class ii permissive change cover letter',
                     'class ii permissive change letter', 'class ii permissive change letter for fcc',
                     'class ii permissive change request letter',
                     'class ii permissive request cover letter', 'class ii premissive change letter',
                     'class ii rf info', 'class ii test photos', 'class ii test report',
                     'description of class ii permissive change', 'fcc class ii change letter',
                     'fcc declaration of class ii change', 'test report bt classics part 1',
                     'test report bt classics part 2', '(tv500i) class ii change_2016-06-01',
                     'c2pc', 'c2pc and lma', 'c2pc_basp-1920', 'c2pc cover letter', 'c2pc details',
                     'c2pc detials', 'c2pc fcc v1', 'c2pc fcc v1 letter',
                     'c2pc host manufacturer design response', 'c2pc letter',
                     'c2pc letter detector', 'c2pc letter scu', 'c2pc request',
                     'c2pc request letter', 'ciipc', 'change description', 'change id letter',
                     'change id permission letter', 'change in id cover letter',
                     'change in id permission letter', 'change in id request letter']

IGNORE_FILES = ['Test Report', 'RF Exposure Info']

# extract interesting information and patterns from extracted text
def search_text(texts):
    text =  "\n".join(texts).lower()
    results = {'functionality': [], 'user_password': [],
               'programs': [], 'license': [], 'copyrights': [],
               'ip_address': []}

    results_found = False

    # then search for a bunch of things
    for t in TEXT_TO_FUNCTIONALITY:
        if t in text:
            results['functionality'].append(TEXT_TO_FUNCTIONALITY[t])
            results_found = True

    result_ip = defaults.REGEX_IP.search(text)
    if result_ip is not None:
        results['ip_address'].append(result_ip.groups()[0])
        results_found = True

    if 'gnu general public license' in text:
        results['license'].append("GNU GPL")
        results_found = True
    return (results_found, results)

# Stitch images. Only the image name is needed, not any of the data
# extracted from the PDF: the coordinates recorded in the PDF do not
# match the dimensons of the images, so rely on the actual image data
# that was extracted in an earlier step in the process and use that
# instead.
def stitch(images, orientation, image_directory, stitch_directory):
    '''Stitch a collection of images extracted from a PDF'''
    # first determine the width and height of the new image
    height = 0
    width = 0
    for img_name in images:
        orig_image = PIL.Image.open(image_directory / img_name)
        if orientation == 'horizontal':
            width += orig_image.size[0]
            height = orig_image.size[1]
        else:
            width = orig_image.size[0]
            height += orig_image.size[1]

    # Create a new image
    new_image = PIL.Image.new('RGB',(width, height), (250,250,250))

    # then add all the images to the new image
    x = 0
    y = 0
    for img_name in images:
        orig_image = PIL.Image.open(image_directory / img_name)
        if orientation == 'horizontal':
            new_image.paste(orig_image, (x,y))
            x += orig_image.size[0]
        else:
            new_image.paste(orig_image, (x,y))
            y += orig_image.size[1]
    image_name = stitch_directory / images[0]
    new_image.save(image_name)
    return image_name.name

@click.command(short_help='Process downloaded FCC documents')
@click.option('--fcc-directory', '-d', 'fcc_input_directory', required=True,
              help='top level input directory with one directory per FCC id',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('--verbose', is_flag=True, help='be verbose')
@click.option('--force', is_flag=True, help='always force processing')
@click.option('--ignore-uninteresting', is_flag=True, help='Ignore uninteresting files')
def main(fccids, fcc_input_directory, output_directory, verbose, force, ignore_uninteresting):
    if not fcc_input_directory.is_dir():
        print(f"{fcc_input_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    for fccid in fccids:
        fcc_directory = fcc_input_directory / fccid
        if not fcc_directory.is_dir():
            print(f"{fcc_directory} is not a directory, skipping.", file=sys.stderr)
        if not (fcc_directory / 'descriptions.json').exists():
            print("'descriptions.json' does not exist, skipping.", file=sys.stderr)

        # check if the descriptions.json file can be read and is valid JSON
        with open(fcc_directory / 'descriptions.json', 'r') as input_file:
            try:
                descriptions = json.loads(input_file.read())
            except:
                print(f"descriptions.json is not valid JSON, skipping {fccid}.", file=sys.stderr)
                continue

            # Then process each individual PDF file.
            # * compute SHA256 hash
            # * extract text
            # * extract pictures

            # Results are written to an unpack directory for each PDF
            # as the file names can be the same in different PDFs.
            for pdf in descriptions:
                if not (fcc_directory / pdf['name']).exists():
                    print(f"{pdf['name']} does not exist, skipping.", file=sys.stderr)
                    continue

                if ignore_uninteresting:
                    if pdf['type'] in IGNORE_FILES:
                        continue

                if verbose:
                    print(f"Processing {pdf['name']}")

                # compute the SHA256 hash of the PDF file
                with open(fcc_directory / pdf['name'], 'rb') as pdf_file:
                    pdf_hash = hashlib.sha256(pdf_file.read()).hexdigest()

                # create two directories for output
                # for original output
                # TODO: these directories should not exist
                # and an error should be thrown, unless --force is used
                pdf_orig_output_directory = output_directory / fccid / pdf['name'] / 'orig'
                if pdf_orig_output_directory.exists():
                    if not force:
                        print(f"Output directory '{pdf_orig_output_directory}' already exists, skipping {pdf['name']}.", file=sys.stderr)
                        continue
                pdf_orig_output_directory.mkdir(exist_ok=True, parents=True)

                # for post processed output (such as combined images)
                pdf_output_directory = output_directory / fccid / pdf['name'] / 'processed'
                if pdf_output_directory.exists():
                    if not force:
                        print(f"Output directory '{pdf_output_directory}' already exists, skipping {pdf['name']}.", file=sys.stderr)
                        continue
                pdf_output_directory.mkdir(exist_ok=True, parents=True)

                # process the individual items per page. This is done for
                # a few reasons: first, keeping a mapping between elements
                # and page numbers is useful, especially if there are many
                # pages in the document. Second, images that need to be
                # combined into a single image will appear on a single page.
                page_number = 0

                # keep metadata per page
                image_metadata = {}

                for page_layout in extract_pages(fcc_directory / pdf['name']):
                    page_number += 1

                    # keep track of images
                    images = []
                    image_names = []
                    image_metadata[page_number] = {'original': [], 'processed': {}}
                    img_directory = pdf_orig_output_directory / str(page_number) / 'images'
                    image_writer = pdfminer.image.ImageWriter(img_directory)

                    extracted_texts = []
                    for element in page_layout:
                        if isinstance(element, pdfminer.layout.LTFigure):
                            try:
                                img_name = image_writer.export_image(element._objs[0])
                                images.append((element, img_name))
                                image_names.append(img_name)
                            except AttributeError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and an AttributeError exception
                                # is thrown with the message:
                                # AttributeError: 'LTFigure' object has no attribute 'srcsize'
                                # Is this an error in pdfminer?
                                # example: FCC ID: 2AD4X-WP25M1200, file: 3788894.pdf
                                pass
                            except IndexError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and an IndexError exception
                                # is thrown with the message:
                                # "IndexError: list index out of range"
                                # Is this an error in pdfminer?
                                # example: FCC ID: RAFXWL-11GRAR, file: 769930.pdf
                                pass
                            except UnboundLocalError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and an UnboundLocalError exception
                                # is thrown with the message:
                                # "cannot access local variable 'mode' where it is not associated with a value"
                                # Is this an error in pdfminer?
                                # example: FCC ID: ODMAM5N, file: 1876480.pdf
                                pass
                            except PIL.UnidentifiedImageError as e:
                                # TODO: fix this.
                                # example: FCC ID: HDCWLAN192XF1, file 1930164.pdf
                                # could be related to missing JPEG2000 support.
                                pass
                        else:
                            try:
                                if element.get_text().strip() != '':
                                    text_directory = pdf_orig_output_directory / str(page_number) / 'text'
                                    text_directory.mkdir(exist_ok=True, parents=True)
                                    extracted_texts.append(element.get_text())
                            except AttributeError:
                                pass

                    # write the extracted text per page
                    if extracted_texts:
                        with open(text_directory / 'extracted.txt', 'w') as output_file:
                            for line in extracted_texts:
                                output_file.write(line)
                        results_found, search_results = search_text(extracted_texts)
                        if results_found:
                            text_result_directory = pdf_output_directory / str(page_number) / 'text'
                            text_result_directory.mkdir(exist_ok=True, parents=True)

                            with open(text_result_directory / 'extracted.json', 'w') as output_file:
                                output_file.write(json.dumps(search_results, indent=4))

                    image_metadata[page_number]['original'] = image_names

                    if len(images) > 1:
                        to_stitch = []
                        orientation = None
                        stitch_directory = pdf_output_directory / str(page_number) / 'images'
                        for image in images:
                            if not to_stitch:
                                # store the first image as a potential starting point.
                                to_stitch.append(image)
                                continue

                            # first try to figure out a stitching orientation, if any
                            if orientation is None:
                                if round(to_stitch[-1][0].x0 - image[0].width) == round(image[0].x0):
                                    orientation = 'horizontal'
                                    to_stitch.append(image)
                                elif round(to_stitch[-1][0].y0 - image[0].height) == round(image[0].y0):
                                    orientation = 'vertical'
                                    to_stitch.append(image)
                                else:
                                    to_stitch = [image]
                                continue

                            # check if an image is still part of a "stitch chain" or
                            # if it is the start of a new image. If it is part of a new
                            # image stitch the images that were stored.
                            if orientation == 'horizontal':
                                if round(to_stitch[-1][0].x0 - image[0].width, 2) == round(image[0].x0, 2):
                                    to_stitch.append(image)
                                else:
                                    stitch_names = list(map(lambda x: x[1], to_stitch))
                                    stitch_directory.mkdir(exist_ok=True, parents=True)
                                    stitched_file = stitch(stitch_names, orientation, img_directory, stitch_directory)
                                    image_metadata[page_number]['processed'][stitched_file] = {}
                                    image_metadata[page_number]['processed'][stitched_file]['inputs'] = stitch_names

                                    # reset
                                    to_stitch = [image]
                                    orientation = None
                            elif orientation == 'vertical':
                                if round(to_stitch[-1][0].y0 - image[0].height, 2) == round(image[0].y0, 2):
                                    to_stitch.append(image)
                                else:
                                    stitch_names = list(map(lambda x: x[1], to_stitch))
                                    stitch_directory.mkdir(exist_ok=True, parents=True)
                                    stitched_file = stitch(stitch_names, orientation, img_directory, stitch_directory)
                                    image_metadata[page_number]['processed'][stitched_file] = {}
                                    image_metadata[page_number]['processed'][stitched_file]['inputs'] = stitch_names

                                    # reset
                                    to_stitch = [image]
                                    orientation = None
                        if len(to_stitch) > 1:
                            stitch_names = list(map(lambda x: x[1], to_stitch))
                            stitch_directory.mkdir(exist_ok=True, parents=True)
                            stitched_file = stitch(stitch_names, orientation, img_directory, stitch_directory)
                            image_metadata[page_number]['processed'][stitched_file] = {}
                            image_metadata[page_number]['processed'][stitched_file]['inputs'] = stitch_names

                # write various metadata to files for further processing
                with open(output_directory / fccid / pdf['name'] / 'images.json', 'w') as output_file:
                    output_file.write(json.dumps(image_metadata, indent=4))


if __name__ == "__main__":
    main()
