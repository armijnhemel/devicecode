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

    # verify the directory names, they should be one of the following
    valid_directory_names = ['TechInfoDepot', 'WikiDevi']

    # Inside these directories a directory called 'devices' should always
    # be present. Optionally there can be a directory called 'overlays'
    # with overlay files.

    devicecode_dirs = []
    for p in devicecode_directory.iterdir():
        if not p.is_dir():
            continue
        if not p.name in valid_directory_names:
            continue
        devices_dir = p / 'devices'
        if not (devices_dir.exists() and devices_dir.is_dir()):
            continue
        devicecode_dirs.append(devices_dir)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    # Then walk all the result files, check the FCC ids and optionally create overlays
    for devicecode_dir in devicecode_dirs:
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    if 'regulatory' not in device:
                        continue
                    fcc_ids = device['regulatory']['fcc_ids']
                    overlay_data = {'type': 'overlay', 'name': 'fcc_id', 'source': 'fcc'}
                    write_overlay = False
                    overlay_fcc_ids = []

                    if len(fcc_ids) != 1:
                        # TODO: fix for files with multiple FCC ids
                        continue

                    for f in fcc_ids:
                        fcc_id = f['fcc_id']
                        fcc_date = f['fcc_date']
                        if fcc_date == '':
                            if report_only:
                                print(f"No FCC date defined for {fcc_id}")
                                continue

                        dates = []

                        if (fcc_input_directory / fcc_id).is_dir():
                            # load the file with approved dates, if it exists
                            approved_file = fcc_input_directory / fcc_id / 'approved_dates.json'
                            if approved_file.exists():
                                with open(approved_file, 'r') as approved:
                                    dates += json.load(approved)

                                # if there is no date at all create an overlay with
                                # the earliest date defined as the FCC date.
                                if fcc_date == '':
                                    overlay_fcc_ids.append({'fcc_date': dates[0], 'fcc_id': fcc_id, 'fcc_type': 'unknown'})
                                    write_overlay=True
                                elif fcc_date not in dates:
                                    # possibly wrong data, create an overlay (TODO)
                                    # copy the existing data to the overlay data
                                    overlay_fcc_ids.append(f)
                                else:
                                    # copy the existing data to the overlay data
                                    overlay_fcc_ids.append(f)
                        else:
                            if report_only:
                                print(f"FCC data missing for {fcc_id}")
                            # copy the existing data to the overlay data
                            overlay_fcc_ids.append(f)

                    if write_overlay:
                        overlay_data['data'] = overlay_fcc_ids
                        overlay_file = overlay_directory / result_file.stem / 'fcc_id.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))

            except json.decoder.JSONDecodeError:
                pass



if __name__ == "__main__":
    main()
