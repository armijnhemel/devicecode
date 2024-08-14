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
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--report-only', '-r', is_flag=True, help='report only')
def main(fcc_input_directory, devicecode_directory, output_directory, report_only):
    if not fcc_input_directory.is_dir():
        print(f"{fcc_input_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not report_only and not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not report_only:
        overlay_directory = output_directory / 'overlays'
        overlay_directory.mkdir(exist_ok=True)

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
                    # a device then things get a little bit more complicated
                    # so skip for now.
                    dates = []
                    if len(fcc_ids) != 1:
                        continue

                    for fcc_id in fcc_ids:
                        if fcc_date == '':
                            if report_only:
                                print(f"No FCC date defined for {fcc_id}")
                                continue

                        if (fcc_input_directory / fcc_id).is_dir():

                            # load the file with approved dates, if it exists
                            approved_file = fcc_input_directory / fcc_id / 'approved_dates.json'
                            if approved_file.exists():
                                with open(approved_file, 'r') as approved:
                                    dates += json.load(approved)

                                # if there is no date at all create an overlay with
                                # the earliest date defined as the FCC date.
                                if fcc_date == '':
                                    overlay_data = {'type': 'overlay', 'source': 'fcc'}
                                    overlay_data['data'] = {'regulatory': {'fcc_date': dates[0]}}
                                    overlay_file = overlay_directory / result_file.stem / 'fcc.json'
                                    overlay_file.parent.mkdir(parents=True, exist_ok=True)
                                    with open(overlay_file, 'w') as overlay:
                                        overlay.write(json.dumps(overlay_data, indent=4))
                                elif fcc_date not in dates:
                                    # wrong data, create an overlay
                                    pass

                        else:
                            if report_only:
                                print(f"FCC data missing for {fcc_id}")

        except json.decoder.JSONDecodeError:
            pass



if __name__ == "__main__":
    main()
