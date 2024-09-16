#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys

import click

def squash(device_one, device_two, debug=False):
    '''Squash two devices. Device 1 is "leading".'''

    changed = False
    # additional chips
    if device_one['additional_chips'] != device_two['additional_chips']:
        pass

    # brand
    if device_one['brand'] != device_two['brand']:
        if debug:
            print(f"Brand inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['brand']}")
            print(f"  Device 2: {device_two['brand']}")

    # commercial
    if device_one['commercial'] != device_two['commercial']:
        pass

    # cpus
    if device_one['cpus'] != device_two['cpus']:
        pass

    # defaults
    if device_one['defaults'] != device_two['defaults']:
        pass

    # device types
    if device_one['device_types'] != device_two['device_types']:
        device_types = set(device_one['device_types'])
        device_types.update(device_two['device_types'])
        if debug and device_one['device_types'] and device_two['device_types']:
            print(f"Device type inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['device_types']}")
            print(f"  Device 2: {device_two['device_types']}")
        device_one['device_types'] = sorted(device_types)
        changed = True

    # expansions
    if device_one['expansions'] != device_two['expansions']:
        pass

    # flags
    if device_one['flags'] != device_two['flags']:
        flags = set(device_one['flags'])
        flags.update(device_two['flags'])
        if debug and device_one['flags'] and device_two['flags']:
            print(f"Flags inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['flags']}")
            print(f"  Device 2: {device_two['flags']}")
        device_one['flags'] = sorted(flags)
        changed = True

    # flash
    if device_one['flash'] != device_two['flash']:
        pass

    # has_jtag
    if device_one['has_jtag'] != device_two['has_jtag']:
        if device_one['has_jtag'] == 'unknown':
            device_one['has_jtag'] = device_two['has_jtag']
            changed = True
        else:
            if device_two['has_jtag'] != 'unknown':
                if debug:
                    print(f"JTAG CONFLICT for '{device_one['title']}'")
                    print(f"  Device 1: {device_one['has_jtag']}")
                    print(f"  Device 2: {device_two['has_jtag']}")

    # has_serial_port
    if device_one['has_serial_port'] != device_two['has_serial_port']:
        if device_one['has_serial_port'] == 'unknown':
            device_one['has_serial_port'] = device_two['has_serial_port']
            changed = True
        else:
            if device_two['has_serial_port'] != 'unknown':
                if debug:
                    print(f"Serial port CONFLICT for '{device_one['title']}'")
                    print(f"  Device 1: {device_one['has_serial_port']}")
                    print(f"  Device 2: {device_two['has_serial_port']}")

    # images, not used, pass
    if device_one['images'] != device_two['images']:
        pass

    # jtag
    if device_one['jtag'] != device_two['jtag']:
        conflict = False
        jtag = copy.deepcopy(device_one['jtag'])

        # baud rate
        if device_one['jtag']['baud_rate'] == 0 or device_two['jtag']['baud_rate'] == 0:
            jtag['baud_rate'] = max(device_one['jtag']['baud_rate'], device_two['jtag']['baud_rate'])
        else:
            if device_one['jtag']['baud_rate'] != device_two['jtag']['baud_rate']:
                conflict = True

        # connector
        if device_one['jtag']['connector'] == '' or device_two['jtag']['connector'] == '':
            if device_one['jtag']['connector'] == '':
                jtag['connector'] = device_two['jtag']['connector']
        else:
            if device_one['jtag']['connector'] != device_two['jtag']['connector']:
                conflict = True

        # number of pins
        if device_one['jtag']['number_of_pins'] == 0 or device_two['jtag']['number_of_pins'] == 0:
            jtag['number_of_pins'] = max(device_one['jtag']['number_of_pins'], device_two['jtag']['number_of_pins'])
        else:
            if device_one['jtag']['number_of_pins'] != device_two['jtag']['number_of_pins']:
                conflict = True

        # populated
        if device_one['jtag']['populated'] != device_two['jtag']['populated']:
            if device_one['jtag']['populated'] == 'unknown':
                jtag['populated'] = device_two['jtag']['populated']
            elif device_two['jtag']['populated'] != 'unknown':
                conflict = True

        # voltage
        if device_one['jtag']['voltage'] != device_two['jtag']['voltage']:
            if not device_one['jtag']['voltage']:
                jtag['voltage'] = device_two['jtag']['voltage']
            elif not device_two['jtag']['populated']:
                conflict = True

        if conflict and debug:
            print(f"JTAG CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['jtag']}")
            print(f"  Device 2: {device_two['jtag']}")

        if not conflict:
            device_one['jtag'] = jtag

    # serial
    if device_one['serial'] != device_two['serial']:
        conflict = False
        serial = copy.deepcopy(device_one['serial'])

        # baud rate
        if device_one['serial']['baud_rate'] == 0 or device_two['serial']['baud_rate'] == 0:
            serial['serial'] = max(device_one['serial']['baud_rate'], device_two['serial']['baud_rate'])
        else:
            if device_one['serial']['baud_rate'] != device_two['serial']['baud_rate']:
                conflict = True

        # connector
        if device_one['serial']['connector'] == '' or device_two['serial']['connector'] == '':
            if device_one['serial']['connector'] == '':
                serial['connector'] = device_two['serial']['connector']
        else:
            if device_one['serial']['connector'] != device_two['serial']['connector']:
                conflict = True

        # number of pins
        if device_one['serial']['number_of_pins'] == 0 or device_two['serial']['number_of_pins'] == 0:
            serial['number_of_pins'] = max(device_one['serial']['number_of_pins'], device_two['serial']['number_of_pins'])
        else:
            if device_one['serial']['number_of_pins'] != device_two['serial']['number_of_pins']:
                conflict = True

        # populated
        if device_one['serial']['populated'] != device_two['serial']['populated']:
            if device_one['serial']['populated'] == 'unknown':
                serial['populated'] = device_two['serial']['populated']
            elif device_two['serial']['populated'] != 'unknown':
                conflict = True

        # voltage
        if device_one['serial']['voltage'] != device_two['serial']['voltage']:
            if not device_one['serial']['voltage']:
                serial['voltage'] = device_two['serial']['voltage']
            elif not device_two['serial']['populated']:
                conflict = True

        if conflict and debug:
            print(f"Serial CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['serial']}")
            print(f"  Device 2: {device_two['serial']}")

        if not conflict:
            device_one['serial'] = serial

    # switch
    if device_one['switch'] != device_two['switch']:
        pass

    # tag lines
    if device_one['taglines'] != device_two['taglines']:
        taglines = set(device_one['taglines'])
        taglines.update(device_two['taglines'])
        if debug and device_one['taglines'] and device_two['taglines']:
            print(f"Taglines inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['taglines']}")
            print(f"  Device 2: {device_two['taglines']}")
        device_one['taglines'] = sorted(taglines)
        changed = True

    return device_one

@click.command(short_help='Squash TechInfoDepot, WikiDevi and overlay information into a single file per device')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'squash\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--debug', is_flag=True, help='print debug output')
def main(devicecode_directory, output_directory, use_git, debug):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if use_git:
        if shutil.which('git') is None:
            print("'git' program not installed, exiting.", file=sys.stderr)
            sys.exit(1)

        os.chdir(output_directory)

        # verify the output directory is a valid Git repository
        p = subprocess.Popen(['git', 'status', output_directory],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (outputmsg, errormsg) = p.communicate()
        if p.returncode == 128:
            print(f"{output_directory} is not a Git repository, exiting.", file=sys.stderr)
            sys.exit(1)

    # verify the directory names, they should be one of the following
    valid_directory_names = ['TechInfoDepot', 'WikiDevi']

    # Inside these directories a directory called 'devices' should always
    # be present.
    devicecode_dirs = []
    for p in devicecode_directory.iterdir():
        if not p.is_dir():
            continue
        if not p.name in valid_directory_names:
            continue
        devices_dir = p / 'devices'
        if not (devices_dir.exists() and devices_dir.is_dir()):
            continue
        devicecode_dirs.append(p)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    squashed_directory = output_directory / 'squashed'
    squashed_directory.mkdir(exist_ok=True, parents=True)

    # Then walk all the result files and overlays for both TechInfoDepot
    # and WikiDevi and apply the overlays to the data.

    # keep mappings between TechInfoDepot and WikiDevi devices names/URLs
    techinfodepot_to_wikidevi = {}
    wikidevi_to_techinfodepot = {}
    data_url_to_name = {}

    techinfodepot_items = {}
    wikidevi_items = {}

    for p in devicecode_dirs:
        devicecode_dir = p / 'devices'
        overlay_directory = p / 'overlays'
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue
            try:
                is_helper_page = False
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    title = device['title']

                    try:
                        data_url = device['web']['data_url']
                    except Exception as e:
                        data_url = title.replace(' ', '_')
                        device['web']['data_url'] = data_url

                    data_url_to_name[data_url] = device['title']

                    # Then see if there are any overlays that need to be integrated
                    overlay_dir_for_device = overlay_directory / device['title']
                    for overlay_file in overlay_dir_for_device.glob('**/*'):
                        if not overlay_file.is_file():
                            continue
                        try:
                            with open(overlay_file, 'r') as overlay_wiki_file:
                                overlay = json.load(overlay_wiki_file)
                                if 'type' not in overlay:
                                    continue
                                if overlay['type'] != 'overlay':
                                    continue
                                if overlay['name'] == 'fcc_id':
                                    device['regulatory']['fcc_ids'] = overlay['data']
                                elif overlay['name'] == 'oui':
                                    device['network']['ethernet_oui'] = overlay['data']['ethernet_oui']
                                    device['network']['wireless_oui'] = overlay['data']['wireless_oui']
                                elif overlay['name'] == 'fcc_extracted_text':
                                    device['fcc_data'] = overlay['data']
                                elif overlay['name'] == 'brand':
                                    device['brand'] = overlay['data']['brand']
                        except json.decoder.JSONDecodeError:
                            pass

                    # create a mapping for each device in the different wikis
                    if p.name == 'TechInfoDepot':
                        if device['web']['wikidevi']:
                            techinfodepot_to_wikidevi[device['title']] = device['web']['wikidevi']
                        techinfodepot_items[device['title']] = device
                    elif p.name == 'WikiDevi':
                        if device['web']['techinfodepot']:
                            wikidevi_to_techinfodepot[device['title']] = device['web']['techinfodepot']
                        wikidevi_items[device['title']] = device

            except json.decoder.JSONDecodeError:
                pass

    # now compare the "patched" TechInfoDepot and WikiDevi files.
    # The TechInfoDepot data will be seen as "leading".
    # There are a few situations for the TechInfoDepot data:
    #
    # 1. there is no link to wikidevi and no link from wikidevi to techinfodepot A      B
    # 2. there is a link to wikidevi and no link from wikidevi to techinfodepot  A -->  B
    # 3. there is a link to wikidevi and a matching link from wikidevi to techinfodepot A <--> B
    # 4. there is a link to wikidevi and a non-matching link from wikidevi to techinfodepot A --> B --> C
    # 5. there is no link to wikidevi and a link from wikidevi to techinfodepot   A <-- B

    squashed_devices = []
    processed_wikidevi = set()
    for name_techinfodepot in techinfodepot_items:
        data_url = techinfodepot_items[name_techinfodepot]['web']['data_url']
        device_name = techinfodepot_items[name_techinfodepot]['title']
        if name_techinfodepot in techinfodepot_to_wikidevi:
            # scenario 2, 3, 4
            target_name = data_url_to_name.get(data_url, None)
            if target_name:
                if target_name == device_name:
                    processed_wikidevi.add(target_name)
        else:
            # scenario 1, 5
            if data_url in wikidevi_to_techinfodepot.values():
                target_name = data_url_to_name.get(data_url, None)
                if target_name:
                    if target_name == device_name:
                        pass
                else:
                    pass
            else:
                # scenario 1: A   B
                # store the device data
                # TODO: do a more extensive search to find similar devices
                if name_techinfodepot in wikidevi_items:
                    squash_result = squash(techinfodepot_items[name_techinfodepot], wikidevi_items[name_techinfodepot], debug)
                    processed_wikidevi.add(name_techinfodepot)
                    squashed_devices.append(squash_result)
                else:
                    squashed_devices.append(techinfodepot_items[name_techinfodepot])

    for name_wikidevi in wikidevi_items:
        if name_wikidevi in processed_wikidevi:
            continue
        squashed_devices.append(wikidevi_items[name_wikidevi])

    for squashed_device in squashed_devices:
        squashed_file_name = squashed_directory / f"{squashed_device['title'].replace('/', '_')}.json"
        with open(squashed_file_name, 'w') as out_file:
            json_data = json.dumps(squashed_device, sort_keys=True, indent=4)
            out_file.write(json_data)

        if use_git:
            # add the file
            p = subprocess.Popen(['git', 'add', squashed_file_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            (outputmsg, errormsg) = p.communicate()
            if p.returncode != 0:
                print(f"{squashed_file_name} could not be added", file=sys.stderr)

            commit_message = f'Add squashed version for {squashed_file_name.stem}'

            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            (outputmsg, errormsg) = p.communicate()
            if p.returncode != 0:
                print(f"{squashed_file_name} could not be committed", file=sys.stderr)

if __name__ == "__main__":
    main()
