#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

import click

import devicecode_defaults as defaults

@click.command(short_help='Create OUI overlay files to provide additional data')
@click.option('--manufacturer', '-m', 'manufacturer_file', required=True,
              help='top level input directory with one directory per FCC id',
              type=click.File('r'))
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
def main(manufacturer_file, devicecode_directory, output_directory):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    ouis = {}
    for line in manufacturer_file:
        if line.startswith('#'):
            continue
        if line.startswith('00:00:00'):
            continue
        oui, manufacturer_short, manufacturer_full = line.strip().split(maxsplit=2)
        ouis[oui] = {'name_short': manufacturer_short, 'name': manufacturer_full}

    # verify the directory names, they should be one of the following
    #valid_directory_names = ['TechInfoDepot', 'WikiDevi']
    valid_directory_names = ['TechInfoDepot']

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

    # create the overlays
    overlay_directory = output_directory / 'overlays'
    overlay_directory.mkdir(exist_ok=True)

    # Then walk all the result files, check the FCC ids and optionally create overlays
    for devicecode_dir in devicecode_dirs:
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    if 'network' not in device:
                        continue

                    overlay_data = {'type': 'overlay', 'name': 'oui', 'source': 'wireshark',
                                    'license': 'GPL-2.0',
                                    'url': 'https://www.wireshark.org/download/automated/data/manuf'}
                    write_overlay = False
                    ethernet_oui_overlays = []
                    wireless_oui_overlays = []

                    for e in device['network']['ethernet_oui']:
                        orig_oui = e['oui']
                        if orig_oui not in ouis:
                            ethernet_oui_overlays.append(e)
                            continue
                        e['name'] = ouis[orig_oui].get('name', '')
                        e['name_short'] = ouis[orig_oui].get('name_short', '')
                        ethernet_oui_overlays.append(e)
                        write_overlay = True
                    for e in device['network']['wireless_oui']:
                        orig_oui = e['oui']
                        if orig_oui not in ouis:
                            wireless_oui_overlays.append(e)
                            continue
                        e['name'] = ouis[orig_oui].get('name', '')
                        e['name_short'] = ouis[orig_oui].get('name_short', '')
                        wireless_oui_overlays.append(e)
                        write_overlay = True

                    if write_overlay:
                        overlay_data['data'] = {'ethernet_oui': ethernet_oui_overlays, 'wireless_oui': wireless_oui_overlays}
                        overlay_file = overlay_directory / result_file.stem / 'network_oui.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))

            except json.decoder.JSONDecodeError:
                pass

if __name__ == "__main__":
    main()
