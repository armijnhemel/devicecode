#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import collections
import copy
import json
import pathlib
import sys

import click

import devicecode.filter as devicecode_filter
from devicecode import dataset_composer
from devicecode import data, defaults

PART_TO_NAME = {'h': 'hardware', 'a': 'application',
                'o': 'operating system'}

# valid directory names should be one of the following
VALID_DIRECTORIES = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']


def get_directories(devicecode_directory, wiki_type):
    '''Create a list of valid DeviceCode directories'''
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

@click.group()
def app():
    pass

@app.command(short_help='Find nearest device')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES,
              case_sensitive=False))
@click.option('--model', '-m', required=True, help='device model name')
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
@click.option('--report', default=1, help='number of devices to report')
def find_nearest(devicecode_directory, wiki_type, model, no_overlays, report):
    '''Find the nearest device(s) given a brand and model number'''
    if not devicecode_directory.is_dir():
        raise click.ClickException(f"Directory {devicecode_directory} is not a valid directory.")

    if report <= 0:
        raise click.ClickException(f"{report=} needs to be larger than 1.")

    devicecode_directories = get_directories(devicecode_directory, wiki_type)

    if not devicecode_directories:
        print(f"No valid device directories found in {devicecode_directory}.", file=sys.stderr)
        sys.exit(1)

    devices = data.read_data_with_overlays(devicecode_directories, no_overlays)

    # First check to see if the model actually exists in the data set
    # TODO: alternatively allow a path to the JSON file with the device data?
    model_data = None
    for d in devices:
        if d['title'] == model:
            model_data = copy.deepcopy(d)
            break

    if not model_data:
        print(f"{model=} is not a valid device.", file=sys.stderr)
        sys.exit(1)

    closest = []
    closest_found = 0

    for d in devices:
        if d['title'] == model:
            continue
        # first check the ODM model
        if model_data['manufacturer']['model'] != '':
            # first check to see if the ODM has the
            # device as well
            if d['brand'] == model_data['manufacturer']['name']:
                if d['model']['model'] == model_data['manufacturer']['model']:
                    closest.append(d)
            elif d['manufacturer']['name'] == model_data['manufacturer']['name']:
                if d['manufacturer']['model'] == model_data['manufacturer']['model']:
                    closest.append(d)
        if len(closest) >= report:
            break

    for d in closest:
        print(d['title'])


@app.command(short_help='Dump values from DeviceCode')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES, case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
@click.option('--value', help='value to print', required=True,
              type=click.Choice(['baudrate_serial', 'baudrate_jtag', 'bootloader',
                         'connector_jtag', 'connector_serial', 'cpeid', 'cveid',
                         'fccid', 'ip', 'jtag', 'login', 'odm', 'odm_country',
                         'password', 'pcbid', 'sdk', 'serial']))
@click.option('--pretty', help='pretty print format', required=True,
              type=click.Choice(['list', 'line', 'counter', 'json']))
def dump(devicecode_directory, wiki_type, no_overlays, value, pretty):
    '''Dump lists of known values'''
    if not devicecode_directory.is_dir():
        raise click.ClickException(f"Directory {devicecode_directory} is not a valid directory.")

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
        case 'bootloader':
            for d in devices:
                if d['software']['bootloader']['manufacturer']:
                    value_counter.update([d['software']['bootloader']['manufacturer']])
        case 'connector_jtag':
            for d in devices:
                if d['jtag']['connector']:
                    value_counter.update([d['jtag']['connector']])
        case 'connector_serial':
            for d in devices:
                if d['serial']['connector']:
                    value_counter.update([d['serial']['connector']])
        case 'cpeid':
            for d in devices:
                value_counter.update([d['regulatory']['cpe']['cpe23']])
        case 'cveid':
            for d in devices:
                value_counter.update(d['regulatory']['cve'])
        case 'fccid':
            for d in devices:
                value_counter.update([x['fcc_id'] for x in d['regulatory']['fcc_ids']])
        case 'ip':
            for d in devices:
                if d['defaults']['ip']:
                    value_counter.update([d['defaults']['ip']])
        case 'jtag':
            for d in devices:
                if d['has_jtag']:
                    value_counter.update([d['has_jtag']])
        case 'login':
            for d in devices:
                if d['defaults']['logins']:
                    value_counter.update(d['defaults']['logins'])
        case 'odm':
            for d in devices:
                if d['manufacturer']['name']:
                    value_counter.update([d['manufacturer']['name']])
                else:
                    value_counter.update(['***UNKNOWN***'])
        case 'odm_country':
            for d in devices:
                if d['manufacturer']['country']:
                    value_counter.update([d['manufacturer']['country']])
                else:
                    value_counter.update(['***UNKNOWN***'])
        case 'password':
            for d in devices:
                if d['defaults']['password']:
                    value_counter.update([d['defaults']['password']])
        case 'pcbid':
            for d in devices:
                if d['model']['pcb_id']:
                    value_counter.update([d['model']['pcb_id']])
        case 'sdk':
            for d in devices:
                if d['software']['sdk']['name']:
                    value_counter.update([d['software']['sdk']['name']])
                else:
                    value_counter.update(['***UNKNOWN***'])
        case 'serial':
            for d in devices:
                if d['has_serial_port']:
                    value_counter.update([d['has_serial_port']])

    match pretty:
        case 'list':
            print(sorted(set(value_counter)))
        case 'line':
            for d in sorted(set(value_counter)):
                print(d)
        case 'counter':
            for v, count in value_counter.most_common():
                print(count, v)
        case 'json':
            print(json.dumps(value_counter, indent=4))


@app.command(short_help='Search DeviceCode data set using a filter')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(VALID_DIRECTORIES, case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
@click.option('--filter', 'filter_string', help='filter string')
@click.option('--pretty', help='pretty print format', required=True,
              type=click.Choice(['compact', 'compact-json', 'json']))
def search(devicecode_directory, wiki_type, no_overlays, filter_string, pretty):
    '''Search the DeviceCode data using a filter string'''
    if not devicecode_directory.is_dir():
        raise click.ClickException(f"Directory {devicecode_directory} is not a valid directory.")

    devicecode_directories = get_directories(devicecode_directory, wiki_type)

    if not devicecode_directories:
        print(f"No valid device directories found in {devicecode_directory}.", file=sys.stderr)
        sys.exit(1)

    # Read the device and overlay data
    devices, overlays = data.read_data(devicecode_directories, no_overlays)

    # Compose the dataset with the initial data.
    composer = dataset_composer.DatasetComposer(devices, overlays)
    dataset = composer.compose_data_sets()

    # Create a validator that has been primed with all valid data.
    validator = devicecode_filter.FilterValidator(dataset, token_names=defaults.TOKEN_NAMES)

    # Validate the filter string. Return all data if the filter string is empty.
    if filter_string:
        validation_result = validator.validate(filter_string)
        failures = validation_result.failures
        if failures:
            description = failures[0].description
            print(f"Filter string validation failure: \"{description}\".", file=sys.stderr)
            sys.exit(1)

        # Create the filter values.
        filter_result = devicecode_filter.process_filter(filter_string)

        # Create the filtered data set.
        dataset = composer.compose_data_sets(filter_result)

    result_devices = []
    device_names_and_models = []
    for d in dataset['brands_to_devices']:
        for device in dataset['brands_to_devices'][d]:
            result_devices.append(device)
            device_names_and_models.append(f"{d} {device['model']}")

    match pretty:
        case 'compact':
            for device in sorted(device_names_and_models):
                print(device)
        case 'compact-json':
            print(json.dumps(sorted(device_names_and_models), indent=4))
        case 'json':
            print(json.dumps(result_devices, indent=4))


if __name__ == "__main__":
    app()
