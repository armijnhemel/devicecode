#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

import click
import pdfminer
import PIL.Image
from pdfminer.high_level import extract_pages

def stitch(images, orientation, image_directory, output_directory):
    # first find the new wdith and height
    height = 0
    width = 0
    for img in images:
        img_data, img_name = img
        orig_image = PIL.Image.open(image_directory / img_name)
        if orientation == 'horizontal':
            width += orig_image.size[0]
            height = orig_image.size[1]
        else:
            width = orig_image.size[0]
            height += orig_image.size[1]

    # Create a new image
    new_image = PIL.Image.new('RGB',(width, height), (250,250,250))

    # then add all the new images
    x = 0
    y = 0
    for img in images:
        img_data, img_name = img
        orig_image = PIL.Image.open(image_directory / img_name)
        if orientation == 'horizontal':
            pass
        else:
            new_image.paste(orig_image, (x,y))
            y += orig_image.size[1]
    new_image.save(output_directory / images[0][1])

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
def main(fccids, fcc_input_directory, output_directory, verbose, force):
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
            # * extract text
            # * extract pictures
            # Results are written to an unpack directory for each PDF
            # as the file names can be the same in different PDFs.
            for _, pdf_name, description in descriptions:
                if not (fcc_directory / pdf_name).exists():
                    print(f"{pdf_name} does not exist, skipping.", file=sys.stderr)
                    continue

                if verbose:
                    print(f"Processing {pdf_name}")

                # create two directories for output
                # for original output
                pdf_orig_output_directory = output_directory / f"{pdf_name}.orig"
                pdf_orig_output_directory.mkdir(exist_ok=True)

                # for post processed output (such as combined images)
                pdf_output_directory = output_directory / f"{pdf_name}.output"
                pdf_output_directory.mkdir(exist_ok=True)

                # process the individual items per page. This is done for
                # a few reasons: first, keeping a mapping between elements
                # and page numbers is useful, especially if there are many
                # pages in the document. Second, images that need to be
                # combined into a single image will appear on a single page.
                num_pages = 0
                image_writer = pdfminer.image.ImageWriter(pdf_orig_output_directory)
                for page_layout in extract_pages(fcc_directory / pdf_name):
                    num_pages += 1
                    images = []
                    for element in page_layout:
                        if isinstance(element, pdfminer.layout.LTFigure):
                            # TODO: check if the image already exists. If so
                            # refuse to overwrite, unless forced.
                            try:
                                img_name = image_writer.export_image(element._objs[0])
                                images.append((element, img_name))
                            except UnboundLocalError:
                                # TODO: fix this. sometimes images aren't
                                # correctly exported and an UnboundLocalError exception
                                # is thrown with the message:
                                # "cannot access local variable 'mode' where it is not associated with a value"
                                # Is this an error in pdfminer?
                                pass
                    if len(images) > 1:
                        to_stitch = []
                        orientation = None
                        for ctr in range(0,len(images)):
                            if to_stitch == []:
                                # store the first image as a potential
                                # starting point.
                                to_stitch.append(images[ctr])
                                continue

                            # first try to figure out a stitching orientation, if any
                            if orientation is None:
                                if to_stitch[-1][0].x0 - images[ctr][0].width == images[ctr][0].x0:
                                    orientation = 'horizontal'
                                    to_stitch.append(images[ctr])
                                elif to_stitch[-1][0].y0 - images[ctr][0].height == images[ctr][0].y0:
                                    orientation = 'vertical'
                                    to_stitch.append(images[ctr])
                                else:
                                    to_stitch = [images[ctr]]
                                continue

                            if orientation == 'horizontal':
                                if to_stitch[-1][0].x0 - images[ctr][0].width == images[ctr][0].x0:
                                    to_stitch.append(images[ctr])
                                else:
                                    stitch(to_stitch, orientation, pdf_orig_output_directory, pdf_output_directory)
                                    # reset
                                    to_stitch = [images[ctr]]
                                    orientation = None
                            elif orientation == 'vertical':
                                if to_stitch[-1][0].y0 - images[ctr][0].height == images[ctr][0].y0:
                                    to_stitch.append(images[ctr])
                                else:
                                    stitch(to_stitch, orientation, pdf_orig_output_directory, pdf_output_directory)

                                    # reset
                                    to_stitch = [images[ctr]]
                                    orientation = None
                        stitch(to_stitch, orientation, pdf_orig_output_directory, pdf_output_directory)


if __name__ == "__main__":
    main()
