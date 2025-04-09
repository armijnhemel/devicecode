#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import pathlib
import sys

from typing import Any

import click

import devicecode.filter as devicecode_filter
from devicecode import dataset_composer
from devicecode import suggester as Suggester
from devicecode import defaults

PART_TO_NAME = {'h': 'hardware', 'a': 'application',
                'o': 'operating system'}

def read_data(devicecode_directories, no_overlays):
    devices = []
    overlays = {}

    # store device data and overlays
    for devicecode_dir in devicecode_directories:
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue
            try:
                with open(result_file, 'r', encoding='utf-8') as wiki_file:
                    device = json.load(wiki_file)
                    devices.append(device)
            except json.decoder.JSONDecodeError:
                pass

        overlays_directory = devicecode_dir.parent / 'overlays'
        if not no_overlays and overlays_directory.exists() and overlays_directory.is_dir():
            for result_file in overlays_directory.glob('**/*'):
                if not result_file.is_file():
                    continue
                device_name = result_file.parent.name
                if device_name not in overlays:
                    overlays[device_name] = []
                try:
                    with open(result_file, 'r', encoding='utf-8') as wiki_file:
                        overlay = json.load(wiki_file)
                        if 'type' not in overlay:
                            continue
                        if overlay['type'] != 'overlay':
                            continue
                        overlays[device_name].append(overlay)
                except json.decoder.JSONDecodeError:
                    pass
    return (devices, overlays)


@click.command(short_help='DeviceCode CLI')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
def main(devicecode_directory, wiki_type, no_overlays):
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    # verify the directory names, they should be one of the following
    valid_directories = ['TechInfoDepot', 'WikiDevi', 'OpenWrt', 'squashed']

    # The wiki directories should have a fixed structure. There should
    # always be a directory 'devices' (with device data). Optionally there
    # can be a directory called 'overlays' with overlay files.
    # If present the 'squashed' directory will always be chosen and
    # the other directories will be ignored.
    squashed_directory = devicecode_directory / 'squashed' / 'devices'
    if squashed_directory.exists() and not wiki_type:
        devicecode_directories = [squashed_directory]
    else:
        devicecode_directories = []
        for p in devicecode_directory.iterdir():
            if not p.is_dir():
                continue
            if not p.name in valid_directories:
                continue
            if wiki_type:
                if p.name != wiki_type:
                    continue
            devices_dir = p / 'devices'
            if not (devices_dir.exists() and devices_dir.is_dir()):
                continue
            devicecode_directories.append(devices_dir)

    if not devicecode_directories:
        print(f"No valid directories found in {devicecode_directory}, should be one of {', '.join(valid_directories)}.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
