#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

import click

@click.command(short_help='Create FCC overlay files to provide additional data')
@click.option('--fcc-directory', '-f', 'fcc_input_directory', required=True,
              help='top level input directory with one directory per FCC id',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--verbose', '-v', is_flag=True, help='be verbose')
def main(fcc_input_directory, devicecode_directory, output_directory, verbose):
    if not fcc_input_directory.is_dir():
        print(f"{fcc_input_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    # Then walk all the result files, check the FCC ids of the
    for result_file in devicecode_directory.glob('**/*'):
        if not result_file.is_file():
            continue

        try:
            with open(result_file, 'r') as wiki_file:
                device = json.load(wiki_file)
                fcc_ids = device['regulatory']['fcc_ids']
                if fcc_ids:
                    fcc_date = device['regulatory']['fcc_date']

                    # if there are multiple FCC ids associated with
                    dates = []
                    if len(fcc_ids) != 1:
                        continue

                    for fcc_id in fcc_ids:
                        if fcc_date == '':
                            if verbose:
                                print(f"No FCC date defined for {fcc_id}")

                        if (fcc_input_directory / fcc_id).is_dir():
                            approved_file = fcc_input_directory / fcc_id / 'approved_dates.json'
                            if approved_file.exists():
                                with open(approved_file, 'r') as approved:
                                    dates += json.load(approved)
                            if fcc_date not in dates:
                                # wrong date?
                                pass
                        else:
                            if verbose:
                                print(f"FCC data missing for {fcc_id}")

        except json.decoder.JSONDecodeError:
            pass



if __name__ == "__main__":
    main()
