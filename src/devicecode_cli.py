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
from devicecode import data, defaults

PART_TO_NAME = {'h': 'hardware', 'a': 'application',
                'o': 'operating system'}

# valid directory names should be one of the following
VALID_DIRECTORIES = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']


class DeviceCodeException(Exception):
    pass

@click.group()
def app():
    pass

@app.command(short_help='Devicecode device comparer')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES,
              case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
def compare(devicecode_directory, wiki_type, no_overlays):
    '''Compare devices'''
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    devicecode_directories = get_directories(devicecode_directory, wiki_type)

    if not devicecode_directories:
        print(f"No valid device directories found in {devicecode_directory}.", file=sys.stderr)
        sys.exit(1)

    #devices, overlays = data.read_data(devicecode_directories, no_overlays)
    #devices = data.read_data_with_overlays(devicecode_directories, no_overlays)


@app.command(short_help='Devicecode value dumper')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES, case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
@click.option('--value', help='value to print', required=True,
              type=click.Choice(['baudrate_serial', 'baudrate_jtag', 'cve']))
@click.option('--pretty', help='pretty print format', required=True,
              type=click.Choice(['list', 'line', 'counter']))
def dump(devicecode_directory, wiki_type, no_overlays, value, pretty):
    '''Dump lists of known values'''
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    devicecode_directories = get_directories(devicecode_directory, wiki_type)

    if not devicecode_directories:
        print(f"No valid device directories found in {devicecode_directory}.", file=sys.stderr)
        sys.exit(1)

    devices = data.read_data_with_overlays(devicecode_directories, no_overlays)
    value_counter = collections.Counter()

    match value:
        case 'baudrate_jtag':
            for d in devices:
                if d['jtag']['baud_rate'] != 0:
                    value_counter.update([d['jtag']['baud_rate']])
        case 'baudrate_serial':
            for d in devices:
                if d['serial']['baud_rate'] != 0:
                    value_counter.update([d['serial']['baud_rate']])
        case 'cve':
            for d in devices:
                value_counter.update(d['regulatory']['cve'])

    match pretty:
        case 'list':
            print(sorted(set(value_counter)))
        case 'line':
            for d in sorted(set(value_counter)):
                print(d)
        case 'counter':
            for v, count in value_counter.most_common():
                print(count, v)


@app.command(short_help='DeviceCode CLI')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES, case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
def search(devicecode_directory, wiki_type, no_overlays):
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    devicecode_directories = get_directories(devicecode_directory, wiki_type)

    if not devicecode_directories:
        print(f"No valid device directories found in {devicecode_directory}.", file=sys.stderr)
        sys.exit(1)

    devices, overlays = data.read_data(devicecode_directories, no_overlays)

def get_directories(devicecode_directory, wiki_type):
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
            if not p.name in VALID_DIRECTORIES:
                continue
            if wiki_type:
                if p.name != wiki_type:
                    continue
            devices_dir = p / 'devices'
            if not (devices_dir.exists() and devices_dir.is_dir()):
                continue
            devicecode_directories.append(devices_dir)
    return devicecode_directories


if __name__ == "__main__":
    app()
