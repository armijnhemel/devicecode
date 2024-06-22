#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

import click

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
            for _, pdf_name, description in descriptions:
                if not (fcc_directory / pdf_name).exists:
                    print(f"{pdf_name} does not exist, skipping.", file=sys.stderr)
                    continue


if __name__ == "__main__":
    main()
