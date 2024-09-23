#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import gzip
import hashlib
import json
import multiprocessing
import pathlib
import re
import shutil
import struct
import sys

import click
import pdfminer
import PIL.Image
from pdfminer.high_level import extract_pages

import devicecode_defaults as defaults

# mapping of texts to functionality
TEXT_TO_FUNCTIONALITY = {
    'upnp': 'UPnP',
    'universal plug and play': 'UPnP',
    'telnet': 'telnet',
    'syslog': 'syslog',
}

PROGRAMS = ['arptables', 'bpalogin', 'bridge-utils', 'busybox', 'ebtables', 'glibc',
            'hostapd', 'iproute', 'iptables', 'iputils', 'linux', 'nmap',
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
    text =  "\n ".join(texts).lower()
    text = re.sub(r'\s+', ' ', text)

    results = []
    results_found = False

    # then search for a bunch of things
    for t in TEXT_TO_FUNCTIONALITY:
        if t in text:
            results.append({'type': 'functionality', 'value': TEXT_TO_FUNCTIONALITY[t]})
            results_found = True

    result_ips = defaults.REGEX_IP.findall(text)
    for result_ip in result_ips:
        if len(result_ip.split('.')[0]) > 3:
            continue
        ip_components = [int(x) <= 255 for x in result_ip.split('.')]
        if ip_components == [True, True, True, True]:
            if result_ip.split('.')[3] == '000':
                continue
            if result_ip.startswith('192.168'):
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'private'})
            elif result_ip.startswith('172.'):
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'private'})
            elif result_ip.startswith('10.'):
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'private'})
            elif result_ip.startswith('224.'):
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'multicast'})
            elif result_ip.startswith('255.'):
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'netmask'})
            else:
                # TODO: filter paragraph numbers
                results.append({'type': 'IP address', 'value': result_ip, 'extra_data': 'possible'})
            results_found = True

    if 'gnu general public license' in text:
        results.append({'type': 'license', 'value': 'GNU GPL'})
        results_found = True

    if 'open source' in text:
        results.append({'type': 'reference', 'value': 'open source'})
        results_found = True

    for i in ['default password', 'default user password', 'default admin password',
              'default username and password', 'by default, the password is',
              'the password is', 'by default, the username and password',
              'default user name and password']:
        if i in text:
            results.append({'type': 'reference', 'value': 'default password'})
            results_found = True
            break

    for i in ['default username', 'default user name', 'default user\'s name',
              'default user id', 'default users', 'default username and password',
              'default user name and password', 'by default the user name is',
              'by default, the username and password']:
        if i in text:
            results.append({'type': 'reference', 'value': 'default user'})
            results_found = True
            break

    for t in PROGRAMS:
        if t in text:
            results.append({'type': 'program', 'value': t})
            results_found = True

    return (results_found, results)

# Stitch images. Only the image name is needed, not any of the data
# extracted from the PDF: the coordinates recorded in the PDF do not
# match the dimensons of the images, so rely on the actual image data
# that was extracted in an earlier step in the process and use that
# instead.
def stitch(images, orientation, image_page_directory, img_directory, stitch_directory, clean_output):
    '''Stitch a collection of images extracted from a PDF'''
    image_name = stitch_directory / images[0]
    img_hash = ''

    # first determine the width and height of the new image
    height = 0
    width = 0
    try:
        for img_name in images:
            orig_image = PIL.Image.open(image_page_directory / img_name)
            if orientation == 'horizontal':
                width += orig_image.size[0]
                height = orig_image.size[1]
            else:
                width = orig_image.size[0]
                height += orig_image.size[1]
    except PIL.UnidentifiedImageError:
        status = False
        return (status, image_name.name, img_hash)

    # Create a new image
    new_image = PIL.Image.new('RGB',(width, height), (250,250,250))

    # then add all the images to the new image
    x = 0
    y = 0
    for img_name in images:
        orig_image = PIL.Image.open(image_page_directory / img_name)
        try:
            if orientation == 'horizontal':
                new_image.paste(orig_image, (x,y))
                x += orig_image.size[0]
            else:
                new_image.paste(orig_image, (x,y))
                y += orig_image.size[1]
        except OSError:
            status = False
            return (status, image_name.name, img_hash)
    new_image.save(image_name)
    with open(image_name, 'rb') as new_img:
        img_hash = hashlib.sha256(new_img.read()).hexdigest()
        img_hash_file = img_directory / img_hash[0] / img_hash

        if not clean_output:
            if not img_hash_file.exists():
                shutil.copy(image_name, img_hash_file)

        image_name.unlink()

        if not clean_output:
            image_name.hardlink_to(img_hash_file)
        status = True
    return (status, image_name.name, img_hash)

def process_fcc(task):
    fccid, meta = task
    fcc_directory = meta['fcc_input_directory'] / fccid
    output_directory = meta['output_directory']
    verbose = meta['verbose']
    process_uninteresting = meta['process_uninteresting']
    force = meta['force']
    no_images = meta['no_images']
    clean_output = meta['clean_output']

    if not fcc_directory.is_dir():
        print(f"{fcc_directory} is not a directory, skipping.", file=sys.stderr)
        return
    if not (fcc_directory / 'descriptions.json').exists():
        print("'descriptions.json' does not exist, skipping.", file=sys.stderr)
        return

    (output_directory / fccid).mkdir(exist_ok=True, parents=True)
    shutil.copy(fcc_directory / 'approved_dates.json', output_directory / fccid)
    shutil.copy(fcc_directory / 'descriptions.json', output_directory / fccid)

    # check if the descriptions.json file can be read and is valid JSON
    with open(fcc_directory / 'descriptions.json', 'r') as input_file:
        try:
            descriptions = json.loads(input_file.read())
        except:
            print(f"descriptions.json is not valid JSON, skipping {fccid}.", file=sys.stderr)
            return

        # create a directory for images per FCC id. This is where
        # all images will be stored. The rest will be hardlinked. This is
        # done because there is a lot of duplication in some PDFs (80-90%)
        img_directory = output_directory / 'images'

        # Then process each individual PDF file.
        # * compute SHA256 hash
        # * extract text
        # * extract pictures

        # Results are written to an unpack directory for each PDF
        # as the file names can be the same in different PDFs.
        for pdf in descriptions['data']:
            if not (fcc_directory / pdf['name']).exists():
                print(f"{pdf['name']} does not exist, skipping.", file=sys.stderr)
                continue

            if not process_uninteresting:
                if pdf['type'] in IGNORE_FILES:
                    continue

            if verbose:
                print(f"Processing {fccid} - {pdf['name']}")

            # create two directories for output:
            # one for original output (original images and extracted text)
            # and one for post processed output (such as text search results,
            # recombined images).
            # These directories should not exist (because that means the file
            # has already been processed) and an error is thrown, unless --force is used
            pdf_orig_output_directory = output_directory / fccid / pdf['name'] / 'orig'
            if pdf_orig_output_directory.exists():
                if not force:
                    print(f"Output directory '{pdf_orig_output_directory}' already exists, skipping {pdf['name']}.", file=sys.stderr)
                    continue
            pdf_orig_output_directory.mkdir(exist_ok=True, parents=True)

            pdf_output_directory = output_directory / fccid / pdf['name'] / 'processed'
            if pdf_output_directory.exists():
                if not force:
                    print(f"Output directory '{pdf_output_directory}' already exists, skipping {pdf['name']}.", file=sys.stderr)
                    continue
            pdf_output_directory.mkdir(exist_ok=True, parents=True)

            page_results = []
            image_results = []

            # process the individual items per page. This is done for
            # a few reasons: first, keeping a mapping between elements
            # and page numbers is useful, especially if there are many
            # pages in the document. Second, images that need to be
            # combined into a single image always are on a single page.
            page_number = 0

            try:
                for page_layout in extract_pages(fcc_directory / pdf['name']):
                    page_number += 1
                    images = []
                    image_metadata = {}
                    img_page_directory = pdf_orig_output_directory / str(page_number) / 'images'

                    if not no_images:
                        # keep track of images
                        image_writer = pdfminer.image.ImageWriter(img_page_directory)

                    extracted_texts = []
                    for element in page_layout:
                        if not no_images and isinstance(element, pdfminer.layout.LTFigure):
                            try:
                                img_name = image_writer.export_image(element._objs[0])
                                full_img_name = img_page_directory / img_name

                                # compute the SHA256 of the image file to see if it already
                                # exists. There is a lot of duplication, taking up unnecessary
                                # disk space.
                                # Because pdfminer doesn't allow writing to a user specified
                                # file or a buffer first write to a file, compute the SHA256,
                                # copy the file (if necessary) and then hardlinking the original
                                # file name.
                                with open(full_img_name, 'rb') as new_img:
                                    img_hash = hashlib.sha256(new_img.read()).hexdigest()
                                    img_hash_file = img_directory / img_hash[0] / img_hash
                                    if not img_hash_file.exists():
                                        shutil.copy(full_img_name, img_hash_file)
                                    full_img_name.unlink()
                                    full_img_name.hardlink_to(img_hash_file)
                                images.append((element, img_name))
                                if not image_metadata:
                                    image_metadata = {'original': [], 'processed': []}
                                image_metadata['original'].append({'name': img_name, 'sha256': img_hash})
                            except AttributeError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and an AttributeError exception
                                # is thrown with the message:
                                # AttributeError: 'LTFigure' object has no attribute 'srcsize'
                                # Is this an error in pdfminer?
                                # example: FCC ID: 2AD4X-WP25M1200, file: 3788894.pdf
                                pass
                            except pdfminer.pdfexceptions.PDFValueError:
                                # TODO: fix this
                                pass
                            except KeyError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and a KeyError exception
                                # is thrown with the message:
                                # KeyError: 'JBIG2Globals'
                                # example: FCC ID: HDCWLAN192XF1, file: 2967552.pdf
                                # https://github.com/pdfminer/pdfminer.six/issues/743
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
                            except PIL.UnidentifiedImageError:
                                # TODO: fix this.
                                # example: FCC ID: HDCWLAN192XF1, file 1930164.pdf
                                # could be related to missing JPEG2000 support.
                                pass
                            except OSError:
                                # TODO: fix this.
                                # example: FCC ID: TE7M4R, file 4041072.pdf
                                # could be related to missing JPEG2000 support.
                                pass
                            except ValueError:
                                # TODO: fix this.
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
                        if not clean_output:
                            with open(text_directory / 'extracted.txt', 'w') as output_file:
                                for line in extracted_texts:
                                    output_file.write(line)
                        results_found, search_results = search_text(extracted_texts)
                        if results_found:
                            page_results.append({'page': page_number, 'results': search_results})

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
                                    status, stitched_file, img_hash = stitch(stitch_names, orientation, img_page_directory, img_directory, stitch_directory, clean_output)
                                    if status:
                                        image_metadata['processed'].append({'name': stitched_file, 'sha256': img_hash, 'inputs': stitch_names})

                                    # reset
                                    to_stitch = [image]
                                    orientation = None
                            elif orientation == 'vertical':
                                if round(to_stitch[-1][0].y0 - image[0].height, 2) == round(image[0].y0, 2):
                                    to_stitch.append(image)
                                else:
                                    stitch_names = list(map(lambda x: x[1], to_stitch))
                                    stitch_directory.mkdir(exist_ok=True, parents=True)
                                    status, stitched_file, img_hash = stitch(stitch_names, orientation, img_page_directory, img_directory, stitch_directory, clean_output)
                                    if status:
                                        image_metadata['processed'].append({'name': stitched_file, 'sha256': img_hash, 'inputs': stitch_names})

                                    # reset
                                    to_stitch = [image]
                                    orientation = None
                        if len(to_stitch) > 1:
                            stitch_names = list(map(lambda x: x[1], to_stitch))
                            stitch_directory.mkdir(exist_ok=True, parents=True)
                            status, stitched_file, img_hash = stitch(stitch_names, orientation, img_page_directory, img_directory, stitch_directory, clean_output)
                            if status:
                                image_metadata['processed'].append({'name': stitched_file, 'sha256': img_hash, 'inputs': stitch_names})

                    if image_metadata:
                        image_results.append({'page': page_number, 'results': image_metadata})

                    if clean_output:
                        for img_name in images:
                            try:
                                (img_page_directory / img_name[1]).unlink()
                            except:
                                pass

            except TypeError:
                # TODO: fix this. It is likely an error in pdfminer
                # Example: 3869887.pdf in FCC id 2APJB-NE1
                # Error:
                # TypeError: 'PDFObjRef' object is not iterable
                pass
            except KeyError:
                pass
            except struct.error:
                # TODO: fix this. It is likely an error in pdfminer
                # Example: 1509933.pdf in FCC id PPD-AR5B95
                # Error:
                # struct.error: unpack requires a buffer of 2 bytes
                pass
            except pdfminer.psexceptions.PSSyntaxError:
                pass
            except pdfminer.psexceptions.PSEOF:
                pass
            except pdfminer.pdfdocument.PDFSyntaxError:
                # TODO: fix this.
                # Example: 2999362.pdf in FCC id ZWJ-0823
                # Error:
                # No /Root object! - Is this really a PDF?
                pass
            except pdfminer.pdfdocument.PDFNoValidXRef:
                pass
            except pdfminer.ccitt.CCITTG4Parser.InvalidData:
                pass
            except pdfminer.pdfdocument.PDFEncryptionError:
                # example: 165344.pdf in FCC id M4Y-000325
                pass
            except pdfminer.pdfexceptions.PDFNotImplementedError:
                # example: 992035.pdf in FCC id PH7MV430A
                pass

            # write various metadata to files for further processing
            if image_results:
                with gzip.open(output_directory / fccid / pdf['name'] / 'images.json.gz', 'w') as output_file:
                    output_file.write(json.dumps(image_results, indent=4).encode('utf-8'))
                if clean_output:
                    for img_name in images:
                        try:
                            (img_page_directory / img_name[1]).unlink()
                        except FileNotFoundError:
                            pass
            if page_results:
                with open(output_directory / fccid / pdf['name'] / 'text.json', 'w') as output_file:
                    output_file.write(json.dumps(page_results, indent=4))

@click.command(short_help='Process downloaded FCC documents')
@click.option('--fcc-directory', '-d', 'fcc_input_directory', required=True,
              help='top level input directory with one directory per FCC id',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory for extracted data, \
                    data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('-j', '--jobs', default=1, type=click.IntRange(min=1),
              help='Number of jobs running simultaneously')
@click.option('--verbose', is_flag=True, help='be verbose')
@click.option('--force', is_flag=True, help='always force processing')
@click.option('--process-uninteresting', is_flag=True, default=False,
              help='process uninteresting files')
@click.option('--no-images', is_flag=True, help='do not extract or process images')
@click.option('--no-text', is_flag=True, help='do not extract or process text')
@click.option('--clean-output', is_flag=True, help='only write clean results (no raw results)')
def main(fccids, fcc_input_directory, output_directory, jobs, verbose, force, process_uninteresting, no_images, no_text, clean_output):
    if not fcc_input_directory.is_dir():
        print(f"{fcc_input_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    # create a directory for images per FCC id. This is where
    # all images will be stored. The rest will be hardlinked. This is
    # done because there is a lot of duplication in some PDFs (80-90%)
    img_directory = output_directory / 'images'
    img_directory.mkdir(exist_ok=True, parents=True)
    for i in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']:
        subdir = img_directory / i
        subdir.mkdir(exist_ok=True)

    meta_information = {'fcc_input_directory': fcc_input_directory, 'verbose': verbose,
                        'output_directory': output_directory, 'force': force,
                        'process_uninteresting': process_uninteresting, 'no_images': no_images,
                        'no_text': no_text, 'clean_output': clean_output}

    tasks = map(lambda x: (x, meta_information), fccids)
    pool = multiprocessing.Pool(jobs)
    pool.map(process_fcc, tasks, chunksize=1)

    if clean_output:
        shutil.rmtree(img_directory)


if __name__ == "__main__":
    main()
