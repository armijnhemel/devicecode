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

def squash(device_one, device_two, device_three, debug=False, verbose=False):
    '''Squash two devices. Device 1 (TechInfoDepot) is "leading".
       Device 3 (OpenWrt) is merely for extra verification of data
       and adding some more information.'''

    self_squash = False
    if device_one == device_two:
        self_squash = True

    # additional chips
    if device_one['additional_chips'] != device_two['additional_chips']:
        pass

    # brand
    if device_one['brand'] != device_two['brand']:
        if debug and verbose:
            print(f"Brand inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['brand']}")
            print(f"  Device 2: {device_two['brand']}")

    # commercial
    if device_one['commercial'] != device_two['commercial']:
        conflict = False
        commercial = copy.deepcopy(device_one['commercial'])

        for i in ['deal_extreme', 'end_of_life_date', 'release_date']:
            if device_one['commercial'][i] == '' or device_two['commercial'][i] == '':
                if device_one['commercial'][i] == '' and device_two['commercial'][i]:
                    commercial[i] = device_two['commercial'][i]
            else:
                if device_one['commercial'][i] != device_two['commercial'][i]:
                    conflict = True

        if conflict and debug:
            print(f"Commercial CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['commercial']}")
            print(f"  Device 2: {device_two['commercial']}")

        if not conflict:
            device_one['commercial'] = commercial

    # cpus
    if device_one['cpus'] != device_two['cpus']:
        conflict = False
        cpu = copy.deepcopy(device_one['cpus'])

        if conflict and debug:
            print(f"CPU CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['cpus']}")
            print(f"  Device 2: {device_two['cpus']}")

    # defaults
    if device_one['defaults'] != device_two['defaults']:
        conflict = False
        defaults = copy.deepcopy(device_one['defaults'])

        for i in ['ip', 'ip_comment', 'password', 'password_comment', 'uses_dhcp']:
            if device_one['defaults'][i] == '' or device_two['defaults'][i] == '':
                if device_one['defaults'][i] == '' and device_two['defaults'][i]:
                    defaults[i] = device_two['defaults'][i]
            else:
                if device_one['defaults'][i] != device_two['defaults'][i]:
                    conflict = True

        if conflict and debug:
            print(f"Default values CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['defaults']}")
            print(f"  Device 2: {device_two['defaults']}")

        if not conflict:
            device_one['defaults'] = defaults

    # device types
    if device_one['device_types'] != device_two['device_types']:
        device_types = set(device_one['device_types'])
        device_types.update(device_two['device_types'])
        if debug and device_one['device_types'] and device_two['device_types'] and verbose:
            print(f"Device type inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['device_types']}")
            print(f"  Device 2: {device_two['device_types']}")
        device_one['device_types'] = sorted(device_types)

    # expansions
    if device_one['expansions'] != device_two['expansions']:
        expansions = set(device_one['expansions'])
        expansions.update(device_two['expansions'])
        if debug and device_one['expansions'] and device_two['expansions'] and verbose:
            print(f"Flags inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['expansions']}")
            print(f"  Device 2: {device_two['expansions']}")
        device_one['expansions'] = sorted(expansions)

    # flags
    if device_one['flags'] != device_two['flags']:
        flags = set(device_one['flags'])
        flags.update(device_two['flags'])
        if debug and device_one['flags'] and device_two['flags'] and verbose:
            print(f"Flags inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['flags']}")
            print(f"  Device 2: {device_two['flags']}")
        device_one['flags'] = sorted(flags)
    if device_three:
        if device_three['flags']:
            flags = set(device_one['flags'])
            flags.update(device_three['flags'])
            device_one['flags'] = sorted(flags)

    # flash
    if device_one['flash'] != device_two['flash']:
        pass

    # has_jtag
    if device_one['has_jtag'] != device_two['has_jtag']:
        if device_one['has_jtag'] == 'unknown':
            device_one['has_jtag'] = device_two['has_jtag']
        else:
            if device_two['has_jtag'] != 'unknown':
                if debug:
                    print(f"JTAG CONFLICT for '{device_one['title']}'")
                    print(f"  Device 1: {device_one['has_jtag']}")
                    print(f"  Device 2: {device_two['has_jtag']}")
    if device_three:
        if device_one['has_jtag'] == 'unknown':
            device_one['has_jtag'] = device_three['has_jtag']
        elif device_three['has_jtag'] != 'unknown':
            if device_one['has_jtag'] != device_three['has_jtag']:
                # TODO
                # This is weird, as OpenWrt says there is no JTAG, while
                # the other data says there is. Probably this is a data
                # error somewhere or a different interpretation of what
                # the presence of JTAG means. There are a few examples
                # in the current (Jan 2025) data:
                # d-link_dir-615_c1
                # gateworks_ventanagw5100
                # gateworks_ventanagw5200
                # gateworks_ventanagw5300
                # gateworks_ventanagw5310
                # gateworks_ventanagw5400
                # gateworks_ventanagw5410
                # fon_fonera2_fon2202
                # mikrotik_rb750gr3
                # netgear_wgt634u
                # zyxel_nsa310b
                pass

    # has_serial_port
    if device_one['has_serial_port'] != device_two['has_serial_port']:
        if device_one['has_serial_port'] == 'unknown':
            device_one['has_serial_port'] = device_two['has_serial_port']
        else:
            if device_two['has_serial_port'] != 'unknown':
                if debug:
                    print(f"Serial port CONFLICT for '{device_one['title']}'")
                    print(f"  Device 1: {device_one['has_serial_port']}")
                    print(f"  Device 2: {device_two['has_serial_port']}")
    if device_three:
        if device_one['has_serial_port'] == 'unknown':
            device_one['has_serial_port'] = device_three['has_serial_port']
        elif device_three['has_serial_port'] != 'unknown':
            if device_one['has_serial_port'] != device_three['has_serial_port']:
                # TODO
                # This is weird, as OpenWrt says there is no serial port,
                # while the other data says there is. Probably this is a data
                # error somewhere. The only example in the current (Jan 2025) data
                # is tp-link_archer_c2600 which is clearly a data error.
                pass

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
            if device_two['jtag']['voltage']:
                if not device_one['jtag']['voltage']:
                    jtag['voltage'] = device_two['jtag']['voltage']
                else:
                    conflict = True

        if conflict and debug:
            print(f"JTAG CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['jtag']}")
            print(f"  Device 2: {device_two['jtag']}")

        if not conflict:
            device_one['jtag'] = jtag

    # manufacturer
    if device_one['manufacturer'] != device_two['manufacturer']:
        conflict = False
        manufacturer = copy.deepcopy(device_one['manufacturer'])

        for i in ['country', 'name', 'model', 'revision']:
            if device_one['manufacturer'][i] == '' or device_two['manufacturer'][i] == '':
                if device_one['manufacturer'][i] == '' and device_two['manufacturer'][i]:
                    manufacturer[i] = device_two['manufacturer'][i]
            else:
                if device_one['manufacturer'][i] != device_two['manufacturer'][i]:
                    conflict = True

        if conflict and debug:
            print(f"Manufacturer CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['manufacturer']}")
            print(f"  Device 2: {device_two['manufacturer']}")

        if not conflict:
            device_one['manufacturer'] = manufacturer

    # model
    if device_one['model'] != device_two['model']:
        conflict = False
        model = copy.deepcopy(device_one['model'])

        for i in ['model', 'part_number', 'pcb_id', 'serial_number', 'series']:
            if device_one['model'][i] == '' or device_two['model'][i] == '':
                if device_one['model'][i] == '' and device_two['model'][i]:
                    model[i] = device_two['model'][i]
            else:
                if device_one['model'][i] != device_two['model'][i]:
                    conflict = True

        if conflict and debug:
            print(f"Model CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['model']}")
            print(f"  Device 2: {device_two['model']}")

        if not conflict:
            device_one['model'] = model

    # network
    if device_one['network'] != device_two['network']:
        pass

    # power
    if device_one['power'] != device_two['power']:
        conflict = False
        power = copy.deepcopy(device_one['power'])

        # barrel_length
        if device_one['power']['barrel_length'] == 0.0 or device_two['power']['barrel_length'] == 0.0:
            power['barrel_length'] = max(device_one['power']['barrel_length'], device_two['power']['barrel_length'])
        else:
            if device_one['power']['barrel_length'] != device_two['power']['barrel_length']:
                conflict = True

        # connector
        if device_one['power']['connector'] == '' or device_two['power']['connector'] == '':
            if device_one['power']['connector'] == '' and device_two['power']['connector']:
                power['connector'] = device_two['power']['connector']
        else:
            if device_one['power']['connector'] != device_two['power']['connector']:
                conflict = True

        # inner_barrel_size
        if device_one['power']['inner_barrel_size'] == 0.0 or device_two['power']['inner_barrel_size'] == 0.0:
            power['inner_barrel_size'] = max(device_one['power']['inner_barrel_size'], device_two['power']['inner_barrel_size'])
        else:
            if device_one['power']['inner_barrel_size'] != device_two['power']['inner_barrel_size']:
                conflict = True

        # outer_barrel_size
        if device_one['power']['outer_barrel_size'] == 0.0 or device_two['power']['outer_barrel_size'] == 0.0:
            power['outer_barrel_size'] = max(device_one['power']['outer_barrel_size'], device_two['power']['outer_barrel_size'])
        else:
            if device_one['power']['outer_barrel_size'] != device_two['power']['outer_barrel_size']:
                conflict = True

        # polarity, skip for now
        # voltage
        if not device_one['power']['voltage']:
            if device_two['power']['voltage']:
                power['voltage'] = device_two['power']['voltage']
        else:
            if device_two['power']['voltage']:
                if device_one['power']['voltage'] != device_two['power']['voltage']:
                    conflict = True

        # voltage type skip for now

        if debug and conflict:
            print(f"Power CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['power']}")
            print(f"  Device 2: {device_two['power']}")

        if not conflict:
            device_one['power'] = power

    # power_supply
    if device_one['power_supply'] != device_two['power_supply']:
        conflict = False
        power_supply = copy.deepcopy(device_one['power_supply'])

        for i in ['brand', 'country', 'model', 'style']:
            if device_one['power_supply'][i] == '' or device_two['power_supply'][i] == '':
                if device_one['power_supply'][i] == '' and device_two['power_supply'][i]:
                    power_supply[i] = device_two['power_supply'][i]
            else:
                if device_one['power_supply'][i] != device_two['power_supply'][i]:
                    conflict = True

        # e_level, skip
        # input_amperage, skip
        # other things, skip

        if debug and conflict:
            print(f"Power supply CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['power_supply']}")
            print(f"  Device 2: {device_two['power_supply']}")

        if not conflict:
            device_one['power_supply'] = power_supply

    # radios
    if device_one['radios'] != device_two['radios']:
        pass

    # ram
    if device_one['ram'] != device_two['ram']:
        pass

    conflict = False
    regulatory = copy.deepcopy(device_one['regulatory'])
    # regulatory
    if device_one['regulatory'] != device_two['regulatory']:

        # fcc_ids
        if regulatory['fcc_ids'] != device_two['regulatory']['fcc_ids']:
            if not regulatory['fcc_ids']:
                regulatory['fcc_ids'] = device_two['regulatory']['fcc_ids']
            elif device_two['regulatory']['fcc_ids']:
                # This usually happens if dates don't match or if there
                # is an invalid FCC id used with one entry having a date
                # and the other not having an associated date.
                pass

        # industry_canada_ids
        if regulatory['industry_canada_ids'] != device_two['regulatory']['industry_canada_ids']:
            if not regulatory['industry_canada_ids']:
                regulatory['industry_canada_ids'] = device_two['regulatory']['industry_canada_ids']
            elif device_two['regulatory']['industry_canada_ids']:
                pass

        # us_ids
        if regulatory['us_ids'] != device_two['regulatory']['us_ids']:
            if not regulatory['us_ids']:
                regulatory['us_ids'] = device_two['regulatory']['us_ids']
            elif device_two['regulatory']['us_ids']:
                pass

        for i in ['wifi_certified', 'wifi_certified_date']:
            if device_one['regulatory'][i] == '' or device_two['regulatory'][i] == '':
                if device_one['regulatory'][i] == '' and device_two['regulatory'][i]:
                    regulatory[i] = device_two['regulatory'][i]
            else:
                if device_one['regulatory'][i] != device_two['regulatory'][i]:
                    conflict = True

        if debug and conflict:
            print(f"Regulatory CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['regulatory']}")
            print(f"  Device 2: {device_two['regulatory']}")

    if not conflict and device_three:
        # fcc_ids
        if not regulatory['fcc_ids']:
            regulatory['fcc_ids'] = device_three['regulatory']['fcc_ids']

    if not conflict:
        device_one['regulatory'] = regulatory

    # serial.
    # First make a deep copy of the data of device 1 and change that
    # before assigning the merged result if there is no conflict
    conflict = False
    serial = copy.deepcopy(device_one['serial'])
    if serial != device_two['serial']:
        # baud rate
        if serial['baud_rate'] == 0 or device_two['serial']['baud_rate'] == 0:
            serial['baud_rate'] = max(serial['baud_rate'], device_two['serial']['baud_rate'])
        else:
            if serial['baud_rate'] != device_two['serial']['baud_rate']:
                conflict = True

        # connector
        if serial['connector'] == '' or device_two['serial']['connector'] == '':
            if serial['connector'] == '' and device_two['serial']['connector']:
                serial['connector'] = device_two['serial']['connector']
        else:
            if serial['connector'] != device_two['serial']['connector']:
                conflict = True

        # data/parity/stop
        if serial['data_parity_stop'] != device_two['serial']['data_parity_stop']:
            if serial['data_parity_stop'] == 'unknown':
                serial['data_parity_stop'] = device_two['serial']['data_parity_stop']
            elif device_two['serial']['data_parity_stop'] == 'unknown':
                pass
            else:
                conflict = True

        # number of pins
        if serial['number_of_pins'] == 0 or device_two['serial']['number_of_pins'] == 0:
            serial['number_of_pins'] = max(serial['number_of_pins'], device_two['serial']['number_of_pins'])
        else:
            if serial['number_of_pins'] != device_two['serial']['number_of_pins']:
                conflict = True

        # populated
        if serial['populated'] != device_two['serial']['populated']:
            if serial['populated'] == 'unknown':
                serial['populated'] = device_two['serial']['populated']
            elif device_two['serial']['populated'] != 'unknown':
                conflict = True

        # voltage
        if serial['voltage'] != device_two['serial']['voltage']:
            if device_two['serial']['voltage']:
                if not serial['voltage']:
                    serial['voltage'] = device_two['serial']['voltage']
                else:
                    conflict = True

        if conflict and debug:
            print(f"Serial CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['serial']}")
            print(f"  Device 2: {device_two['serial']}")

    if not conflict:
        if device_three:
            if serial['data_parity_stop'] == 'unknown' and device_three['serial']['data_parity_stop'] != 'unknown':
                serial['data_parity_stop'] = device_three['serial']['data_parity_stop']
            if not serial['connector'] and device_three['serial']['connector']:
                serial['connector'] = device_three['serial']['connector']
            if serial['baud_rate'] == 0 and device_three['serial']['baud_rate'] != 0:
                serial['baud_rate'] = device_three['serial']['baud_rate']
            if not serial['voltage']:
                serial['voltage'] = device_three['serial']['voltage']
        device_one['serial'] = serial

    if device_one['has_serial_port'] == 'unknown':
        if device_one['serial']['baud_rate'] != 0:
            device_one['has_serial_port'] = 'yes'
        elif device_one['serial']['connector'] != '':
            device_one['has_serial_port'] = 'yes'

    # software
    # First make a deep copy of the data of device 1 and change that
    # before assigning the merged result if there is no conflict
    conflict = False
    software = copy.deepcopy(device_one['software'])
    if software != device_two['software']:
        for i in ['ddwrt', 'gargoyle', 'openwrt', 'os', 'os_version', 'tomato']:
            if software[i] == '' or device_two['software'][i] == '':
                if software[i] == '' and device_two['software'][i]:
                    software[i] = device_two['software'][i]
            else:
                if software[i] != device_two['software'][i]:
                    conflict = True

        if software['sdk'] != device_two['software']['sdk']:
            if software['sdk']['name'] == '':
                software['sdk'] = device_two['software']['sdk']
            else:
                if device_two['software']['sdk']['name']:
                    conflict = True

        if debug and conflict:
            print(f"Software CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['software']}")
            print(f"  Device 2: {device_two['software']}")

        # third party software
        third_party = set(software['third_party'])
        third_party.update(device_two['software']['third_party'])
        if debug and software['third_party'] and device_two['software']['third_party'] and verbose:
            print(f"Third party software inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['software']['third_party']}")
            print(f"  Device 2: {device_two['software']['third_party']}")

        if not conflict:
            if device_three:
                third_party.update(device_three['software']['third_party'])
        software['third_party'] = sorted(third_party)

    if not conflict:
        if device_three:
            for i in ['ddwrt', 'gargoyle', 'openwrt', 'os', 'os_version', 'tomato']:
                if not software[i]:
                    software[i] = device_three['software'][i]
            if software['bootloader']['manufacturer'] != device_three['software']['bootloader']['manufacturer']:
                if software['bootloader']['manufacturer'] == '':
                    if device_three['software']['bootloader']['manufacturer'] != '':
                        software['bootloader']['manufacturer'] = device_three['software']['bootloader']['manufacturer']
            if not software['packages']:
                software['packages'] = device_three['software']['packages']
            if not software['partitions']:
                software['partitions'] = device_three['software']['partitions']
            if software['sdk']['name'] == '':
                software['sdk'] = device_three['software']['sdk']
        device_one['software'] = software

    # switch
    if device_one['switch'] != device_two['switch']:
        pass

    # tag lines
    if device_one['taglines'] != device_two['taglines']:
        taglines = set(device_one['taglines'])
        taglines.update(device_two['taglines'])
        if debug and device_one['taglines'] and device_two['taglines'] and verbose:
            print(f"Taglines inconsistency for '{device_one['title']}'")
            print(f"  Device 1: {device_one['taglines']}")
            print(f"  Device 2: {device_two['taglines']}")
        device_one['taglines'] = sorted(taglines)

    # title, always use the first device, pass
    if device_one['title'] != device_two['title']:
        pass

    # web
    if device_one['web'] != device_two['web']:
        conflict = False
        web = copy.deepcopy(device_one['web'])

        for i in ['download_page', 'techinfodepot', 'wikidevi', 'openwrt']:
            if web[i] == '' or device_two['web'][i] == '':
                if web[i] == '' and device_two['web'][i]:
                    web[i] = device_two['web'][i]
            else:
                if device_one['web'][i] != device_two['web'][i]:
                    conflict = True

        if conflict and debug:
            print(f"Web CONFLICT for '{device_one['title']}'")
            print(f"  Device 1: {device_one['web']}")
            print(f"  Device 2: {device_two['web']}")

        if not conflict:
            device_one['web'] = web

    # record all origins in case the file is a result of multiple inputs
    if 'origins' in device_one and 'origins' in device_two:
        if not self_squash:
            device_one['origins'] += device_two['origins']
        if device_three:
            device_one['origins'] += device_three['origins']
    return device_one

@click.command(short_help='Squash TechInfoDepot, WikiDevi, OpenWrt and overlay information into a single file per device')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory called \'squash\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--debug', is_flag=True, help='print debug output')
@click.option('--verbose', is_flag=True, help='be verbose (for debuging)')
def main(devicecode_directory, output_directory, use_git, debug, verbose):
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
    valid_directory_names = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']

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

    # create the 'squashed' directory if necessary
    squashed_directory = output_directory / 'squashed'
    squashed_directory.mkdir(exist_ok=True, parents=True)

    # keep mappings between TechInfoDepot and WikiDevi devices names/URLs
    techinfodepot_to_wikidevi = {}
    wikidevi_to_techinfodepot = {}

    # OpenWrt to WikiDevi devices names/URLs v.v.
    openwrt_to_wikidevi = {}
    wikidevi_to_openwrt = {}

    # mapping between TechInfoDepot and OpenWrt (one way)
    techinfodepot_to_openwrt = {}

    # keep a mapping between data URLs to name. This is basically just a
    # cache as it would always yield the same result for a title.
    # This cache is shared between all entries.
    data_url_to_name = {}

    techinfodepot_items = {}
    wikidevi_items = {}
    openwrt_items = {}

    # Then walk the result files for the wikis, apply the overlays
    # to the data and keep a mapping betweeen the various wikis.
    for p in devicecode_dirs:
        devicecode_dir = p / 'devices'
        overlay_directory = p / 'overlays'
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue
            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    title = device['title']

                    try:
                        data_url = device['origins'][0]['data_url']
                    except Exception as e:
                        data_url = title.replace(' ', '_')
                        device['web']['data_url'] = data_url

                    data_url_to_name[data_url] = device['title']

                    # Then see if there are any overlays that need to be integrated
                    overlay_dir_for_device = overlay_directory / title.replace('/', '-')
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
                        if device['web']['openwrt']:
                            techinfodepot_to_openwrt[device['title']] = device['web']['openwrt']
                        techinfodepot_items[device['title']] = device
                    elif p.name == 'WikiDevi':
                        if device['web']['techinfodepot']:
                            wikidevi_to_techinfodepot[device['title']] = device['web']['techinfodepot']
                        wikidevi_items[device['title']] = device
                    elif p.name == 'OpenWrt':
                        if device['web']['wikidevi']:
                            wikidevi_name = data_url_to_name.get(device['web']['wikidevi'], '')
                            if wikidevi_name:
                                openwrt_to_wikidevi[device['title']] = wikidevi_name
                                wikidevi_to_openwrt[wikidevi_name] = device['title']
                        openwrt_items[device['title']] = device

            except json.decoder.JSONDecodeError:
                pass

    # now compare the "patched" TechInfoDepot and WikiDevi files.
    # The TechInfoDepot data will be treated as "leading" and in
    # case of a conflict the TechInfoDepot data will be preferred.
    #
    # There are a few situations for the TechInfoDepot data:
    #
    # 1. there is no link to wikidevi and no link from wikidevi to techinfodepot A     B
    # 2. there is a link to wikidevi and no link from wikidevi to techinfodepot  A --> B
    # 3. there is a link to wikidevi and a matching link from wikidevi to techinfodepot A <--> B
    # 4. there is a link to wikidevi and a non-matching link from wikidevi to techinfodepot A --> B --> C
    # 5. there is no link to wikidevi and a link from wikidevi to techinfodepot   A <-- B
    #
    # Additionally there can be data from OpenWrt devices, in all scenarios.

    # store all the squashed devices.
    squashed_devices = []

    # store which wikidevi devices have already been processed.
    processed_wikidevi = set()

    # store which openwrt devices have already been processed.
    processed_openwrt = set()

    # start with devices in TechInfoDepot
    for name_techinfodepot in techinfodepot_items:
        device = techinfodepot_items[name_techinfodepot]
        if 'origins' in device:
            data_url = device['origins'][0]['data_url']
        else:
            data_url = device['title'].replace(' ', '_')

        device_name = device['title']
        if name_techinfodepot in techinfodepot_to_wikidevi:
            # There is a link to something in WikiDevi, so this means
            # scenario 2, 3, 4, but of course only if it is actually
            # in our data.

            # first extract the target name
            target_name = techinfodepot_to_wikidevi[name_techinfodepot]

            # then see if the device is known in the current Wikidevi data set
            wikidevi_name = data_url_to_name.get(target_name, None)
            if not wikidevi_name:
                # the device is not known in WikiDevi, so just copy
                # the original data and continue.
                openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                if openwrt_name:
                    openwrt_device = openwrt_items.get(openwrt_name.rsplit(':', maxsplit=1)[-1], None)
                    if openwrt_device:
                        squash_result = squash(device, device, openwrt_device, debug=debug, verbose=verbose)
                        squashed_devices.append(squash_result)
                        processed_openwrt.add(openwrt_name.rsplit(':', maxsplit=1)[-1])
                    else:
                        squashed_devices.append(device)
                else:
                    squashed_devices.append(device)
                continue

            if wikidevi_name not in wikidevi_items:
                # the device is not known in WikiDevi, so just copy
                # the original data and continue.
                openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                if openwrt_name:
                    openwrt_device = openwrt_items.get(openwrt_name.rsplit(':', maxsplit=1)[-1], None)
                    if openwrt_device:
                        squash_result = squash(device, device, openwrt_device, debug=debug, verbose=verbose)
                        squashed_devices.append(squash_result)
                        processed_openwrt.add(openwrt_name.rsplit(':', maxsplit=1)[-1])
                    else:
                        squashed_devices.append(device)
                else:
                    squashed_devices.append(device)
                continue

            # there is a known WikiDevi device
            # verify if this is scenario 2, 3 or 4
            if not wikidevi_items[wikidevi_name]['web']['techinfodepot']:
                # scenario 2: A --> B
                # As a sanity check only squash if the names are the same
                if name_techinfodepot == wikidevi_name:
                    openwrt_name = wikidevi_to_openwrt.get(wikidevi_name, None)
                    if not openwrt_name:
                        openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                        if openwrt_name:
                            openwrt_name = openwrt_name.rsplit(':', maxsplit=1)[-1]
                    openwrt_device = openwrt_items.get(openwrt_name, None)
                    squash_result = squash(device, wikidevi_items[wikidevi_name], openwrt_device, debug=debug, verbose=verbose)
                    processed_wikidevi.add(name_techinfodepot)
                    if openwrt_name:
                        processed_openwrt.add(openwrt_name)
                    squashed_devices.append(squash_result)
            else:
                if data_url == wikidevi_items[wikidevi_name]['web']['techinfodepot']:
                    # scenario 3: A <--> B
                    # As a sanity check only squash if the names are the same
                    if name_techinfodepot == wikidevi_name:
                        openwrt_name = wikidevi_to_openwrt.get(wikidevi_name, None)
                        if not openwrt_name:
                            openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                            if openwrt_name:
                                openwrt_name = openwrt_name.rsplit(':', maxsplit=1)[-1]
                        openwrt_device = openwrt_items.get(openwrt_name, None)
                        squash_result = squash(device, wikidevi_items[wikidevi_name], openwrt_device, debug=debug, verbose=verbose)
                        processed_wikidevi.add(name_techinfodepot)
                        if openwrt_name:
                            processed_openwrt.add(openwrt_name)
                        squashed_devices.append(squash_result)
                    else:
                        # TODO: find out what to do here
                        pass
                else:
                    # scenario 4: A --> B --> C
                    # Often the difference between the name is just
                    # case, so perhaps checking case insensitive might
                    # be enough. It depends on whether or not the wikis
                    # are case sensitive.
                    # TODO: find out what to do here
                    pass

            target_name = data_url_to_name.get(data_url, None)
            if target_name:
                if target_name == device_name:
                    processed_wikidevi.add(target_name)
        else:
            # scenario 1, 5
            if data_url in wikidevi_to_techinfodepot.values():
                # scenario 5: A <-- B
                # there is no link to wikidevi, but there is a
                # backlink from a wikidevi entry to a *valid*
                # TechInfoDepot entry.
                # First find the corresponding WikiDevi item
                # and see if it matches the device's name
                for wikidevi_name, techinfodepot_target in wikidevi_to_techinfodepot.items():
                    if data_url == techinfodepot_target:
                        openwrt_name = wikidevi_to_openwrt.get(wikidevi_name, None)
                        if not openwrt_name:
                            openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                            if openwrt_name:
                                openwrt_name = openwrt_name.rsplit(':', maxsplit=1)[-1]
                        openwrt_device = openwrt_items.get(openwrt_name, None)
                        squash_result = squash(device, wikidevi_items[wikidevi_name], openwrt_device, debug=debug, verbose=verbose)
                        processed_wikidevi.add(name_techinfodepot)
                        if openwrt_name:
                            processed_openwrt.add(openwrt_name)
                        squashed_devices.append(squash_result)
                        break
            else:
                # scenario 1: A   B
                # store the device data
                # TODO: do a more extensive search to find similar devices
                if name_techinfodepot in wikidevi_items:
                    openwrt_name = wikidevi_to_openwrt.get(name_techinfodepot, None)
                    if not openwrt_name:
                        openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                        if openwrt_name:
                            openwrt_name = openwrt_name.rsplit(':', maxsplit=1)[-1]
                    openwrt_device = openwrt_items.get(openwrt_name, None)
                    squash_result = squash(device, wikidevi_items[name_techinfodepot], openwrt_device, debug=debug, verbose=verbose)
                    processed_wikidevi.add(name_techinfodepot)
                    if openwrt_name:
                        processed_openwrt.add(openwrt_name)
                    squashed_devices.append(squash_result)
                else:
                    # there is nothing to be squashed, so just copy the original data
                    openwrt_name = techinfodepot_to_openwrt.get(name_techinfodepot, None)
                    if openwrt_name:
                        openwrt_device = openwrt_items.get(openwrt_name.rsplit(':', maxsplit=1)[-1], None)
                        if openwrt_device:
                            squash_result = squash(device, device, openwrt_device, debug=debug, verbose=verbose)
                            squashed_devices.append(squash_result)
                            processed_openwrt.add(openwrt_name.rsplit(':', maxsplit=1)[-1])
                        else:
                            squashed_devices.append(device)
                    else:
                        squashed_devices.append(device)

    # now for everything that was in WikiDevi, but which hadn't been processed yet
    for name_wikidevi in wikidevi_items:
        if name_wikidevi in processed_wikidevi:
            continue
        openwrt_name = wikidevi_to_openwrt.get(name_wikidevi, None)
        openwrt_device = openwrt_items.get(openwrt_name, None)
        if openwrt_device:
            squash_result = squash(wikidevi_items[name_wikidevi], wikidevi_items[name_wikidevi], openwrt_device, debug=debug, verbose=verbose)
            processed_wikidevi.add(name_wikidevi)
            squashed_devices.append(squash_result)
            if openwrt_name:
                processed_openwrt.add(openwrt_name)
        else:
            squashed_devices.append(wikidevi_items[name_wikidevi])

    for name_openwrt in openwrt_items:
        if name_openwrt in processed_openwrt:
            continue
        #squashed_devices.append(openwrt_items[name_openwrt])

    for squashed_device in squashed_devices:
        squashed_file_name = squashed_directory / f"{squashed_device['title'].replace('/', '-')}.json"
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
