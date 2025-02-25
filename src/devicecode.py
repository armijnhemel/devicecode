#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import csv
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse
from collections import namedtuple
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click
import mwparserfromhell

import devicecode_defaults as defaults

@dataclass_json
@dataclass
class Amazon_ASIN:
    '''Amazon specific information'''
    # TODO: Replace with a named dictionary or tuple?
    asin: str = ''
    country: str = ''

@dataclass_json
@dataclass
class Bootloader:
    '''Chips information'''
    manufacturer: str = ''
    version: str = ''
    extra_info: list[str] = field(default_factory=list)
    vendor_modified: str = 'unknown'

@dataclass_json
@dataclass
class Chip:
    '''Chips information'''
    manufacturer: str = ''
    manufacturer_verified: bool = False
    model: str = ''
    model_verified: bool = False

    # should this be a list?
    # Chips could have multiple different cores,
    # for example ARM big.LITTLE chips.
    chip_type: str = ''
    chip_type_revision: str = ''
    extra_info: str = ''

    # for addchip
    description: str = ''

@dataclass_json
@dataclass
class Commercial:
    '''Various commercial information, such as price, barcode
       information for web shops (NewEgg, Amazon, etc.)'''
    amazon_asin: list[Amazon_ASIN] = field(default_factory=list)
    availability: str = ''
    deal_extreme: str = ''
    ean: list[str] = field(default_factory=list)
    end_of_life_date: str = ''
    newegg: list[str] = field(default_factory=list)
    release_date: str = ''
    upc: list[str] = field(default_factory=list)

@dataclass_json
@dataclass
class Defaults:
    '''Default settings like login, password and SSIDs'''
    #channel: int? str?
    ip: str = ''

    # sometimes the IP address field contains a description
    # rather than the actual IP address
    ip_comment: str = ''

    logins: list[str] = field(default_factory=list)
    logins_comment: str = ''
    password: str = ''

    # sometimes the password field contains a description
    # rather than the actual password
    password_comment: str = ''
    ssids: list[str] = field(default_factory=list)
    ssid_regexes: list[str] = field(default_factory=list)
    uses_dhcp: str = ''

@dataclass_json
@dataclass
class JTAG:
    connector: str = ''
    populated: str = 'unknown'
    voltage: float = None
    baud_rate: int = 0
    number_of_pins: int = 0

@dataclass_json
@dataclass
class Manufacturer:
    '''Manufacturer information'''
    name: str = ''
    model: str = ''
    revision: str = ''
    country: str = ''

@dataclass_json
@dataclass
class OUI:
    '''Organizationally unique identifier'''
    oui: str = ''
    name_short: str = ''
    name: str = ''

@dataclass_json
@dataclass
class Network:
    '''Networking information'''
    chips: list[Chip] = field(default_factory=list)
    jumbo_frames: str = 'unknown'
    lan_ports: int = 0
    mdix: str = 'unknown'
    docsis_version: str = ''
    # https://en.wikipedia.org/wiki/Organizationally_unique_identifier
    ethernet_oui: list[OUI] = field(default_factory=list)
    wireless_oui: list[OUI] = field(default_factory=list)

@dataclass_json
@dataclass
class Partition:
    name: str = ''

@dataclass_json
@dataclass
class Power:
    connector: str = ''
    barrel_length: float = 0.0
    inner_barrel_size: float = 0.0
    outer_barrel_size: float = 0.0
    polarity: str = ''
    voltage: float = None
    voltage_type: str = ''

@dataclass_json
@dataclass
class PowerSupply:
    brand: str = ''
    model: str = ''
    revision: str = ''
    country: str = ''
    input_voltage: str = ''
    input_amperage: str = ''
    input_current: str = ''
    input_hz: str = ''
    input_connector: str = ''
    output_voltage: str = ''
    output_amperage: str = ''
    output_current: str = ''
    output_connector: str = ''
    style: str = ''
    e_level: str = ''

@dataclass_json
@dataclass
class Radio:
    capabilities: list[str] = field(default_factory=list)
    chips: list[Chip] = field(default_factory=list)
    module: str = ''
    interface: str = ''

    # https://en.wikipedia.org/wiki/Organizationally_unique_identifier
    oui: list[str] = field(default_factory=list)
    standard: str = ''

@dataclass_json
@dataclass
class FCC:
    '''FCC id'''
    fcc_id: str = ''
    fcc_date: str = ''

    # main, auxiliary, unknown
    fcc_type: str = 'unknown'
    grantee: str = ''

@dataclass_json
@dataclass
class Regulatory:
    '''Regulatory information such as FCC
       as well as certification such as Wi-Fi Certified'''
    # all dates are YYYY-MM-DD
    fcc_ids: list[FCC] = field(default_factory=list)

    industry_canada_ids: list[str] = field(default_factory=list)

    # related to some US phone company regulations?
    us_ids: list[str] = field(default_factory=list)

    # WiFi alliance
    wifi_certified: str = ''
    wifi_certified_date: str = ''

@dataclass_json
@dataclass
class Serial:
    # connector on the board
    connector: str = ''

    # device file on the device (for serial port)
    device: str = ''

    populated: str = 'unknown'
    voltage: float = None
    baud_rate: int = 0
    number_of_pins: int = 0
    data_parity_stop: str = 'unknown'

    comments: str = ''

@dataclass_json
@dataclass
class File:
    '''File information: name + type + user + group'''
    name: str = ''
    file_type: str = ''
    user: str = ''
    group: str = ''

@dataclass_json
@dataclass
class Package:
    '''Package information: name + versions'''
    name: str = ''
    package_type: str = ''
    versions: list[str] = field(default_factory=list)

@dataclass_json
@dataclass
class Program:
    '''Program information as extracted from ps output'''
    name: str = ''
    full_name: str = ''
    origin: str = ''
    parameters: list[str] = field(default_factory=list)

@dataclass_json
@dataclass
class Software:
    '''Software information: stock OS/bootloader, third party support'''
    bootloader: Bootloader = field(default_factory=Bootloader)
    os: str = ''
    os_version: str = ''
    sdk: str = ''
    ddwrt: str = 'unknown'
    gargoyle: str = 'unknown'
    openwrt: str = 'unknown'
    tomato: str = 'unknown'
    third_party: list[str] = field(default_factory=list)
    files: list[File] = field(default_factory=list)
    programs: list[Program] = field(default_factory=list)
    packages: list[Package] = field(default_factory=list)
    partitions: list[Partition] = field(default_factory=list)

@dataclass_json
@dataclass
class Web:
    '''Various webpages associated with the device'''
    download_page: str = ''
    product_page: list[str] = field(default_factory=list)
    support_page: list[str] = field(default_factory=list)

    # references to techinfodepot and wikidevi
    techinfodepot: str = ''
    wikidevi: str = ''
    wikipedia: str = ''

@dataclass_json
@dataclass
class Model:
    '''Model information'''
    model: str = ''
    part_number: str = ''
    pcb_id: str = ''
    revision: str = ''
    serial_number: str = ''
    series: str = ''
    submodel: str = ''
    subrevision: str = ''

@dataclass_json
@dataclass
class Origin:
    '''Origin information'''
    data_url: str = ''

    # techinfodepot, wikidevi or openwrt
    origin: str = ''

@dataclass_json
@dataclass
class NetworkAdapter:
    '''Top level class holding network adapter information'''
    brand: str = ''
    manufacturer: Manufacturer = field(default_factory=Manufacturer)
    model: Model = field(default_factory=Model)
    regulatory: Regulatory = field(default_factory=Regulatory)
    title: str = ''
    web: Web = field(default_factory=Web)
    origins: list[Origin] = field(default_factory=list)

@dataclass_json
@dataclass
class USBHub:
    '''Top level class holding USB hub information'''
    brand: str = ''
    manufacturer: Manufacturer = field(default_factory=Manufacturer)
    model: Model = field(default_factory=Model)
    power_supply: PowerSupply = field(default_factory=PowerSupply)
    regulatory: Regulatory = field(default_factory=Regulatory)
    title: str = ''
    web: Web = field(default_factory=Web)
    origins: list[Origin] = field(default_factory=list)

@dataclass_json
@dataclass
class Device:
    '''Top level class holding device information'''
    additional_chips: list[Chip] = field(default_factory=list)
    brand: str = ''
    taglines: list[str] = field(default_factory=list)
    commercial: Commercial = field(default_factory=Commercial)
    cpus: list[Chip] = field(default_factory=list)
    defaults: Defaults = field(default_factory=Defaults)
    device_types: list[str] = field(default_factory=list)
    expansions: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    flash: list[Chip] = field(default_factory=list)
    has_jtag: str = 'unknown'
    has_serial_port: str = 'unknown'
    images: list[str] = field(default_factory=list)
    jtag: JTAG = field(default_factory=JTAG)
    manufacturer: Manufacturer = field(default_factory=Manufacturer)
    model: Model = field(default_factory=Model)
    network: Network = field(default_factory=Network)
    power: Power = field(default_factory=Power)
    power_supply: PowerSupply = field(default_factory=PowerSupply)
    radios: list[Radio] = field(default_factory=list)
    ram: list[Chip] = field(default_factory=list)
    regulatory: Regulatory = field(default_factory=Regulatory)
    serial: Serial = field(default_factory=Serial)
    software: Software = field(default_factory=Software)
    switch: list[Chip] = field(default_factory=list)
    title: str = ''
    web: Web = field(default_factory=Web)
    origins: list[Origin] = field(default_factory=list)

def parse_ls(ls_log):
    '''Parse output from ls -l'''
    results = []
    for line in ls_log.splitlines():
        if line in ['<pre>', '</pre>', '</syntaxhighlight>']:
            continue

        # process each individual line (except pipes and sockets, TODO)
        # Because users have not been very consistent with how 'ls'
        # was invoked the directory portions of the output (obtained
        # for example when running:
        #
        # $ ls -la /*
        #
        # are omitted.
        if line.startswith('l'):
            res = defaults.REGEX_LS_SYMLINK.match(line)
            if res:
                _, _, group, user, _, _, _, _, name, target = res.groups()
                results.append({'type': 'symlink', 'name': name, 'target': target,
                                'user': user, 'group': group})
        elif line.startswith('-'):
            res = defaults.REGEX_LS_REGULAR_DIRECTORY.match(line)
            if res:
                _, _, group, user, size, _, _, _, name = res.groups()
                results.append({'type': 'file', 'name': name, 'size': size,
                                'user': user, 'group': group})
        elif line.startswith('d'):
            res = defaults.REGEX_LS_REGULAR_DIRECTORY.match(line)
            if res:
                _, _, group, user, _, _, _, _, name = res.groups()
                if name not in ['.', '..']:
                    results.append({'type': 'directory', 'name': name,
                                    'user': user, 'group': group})
        elif line.startswith('b'):
            res = defaults.REGEX_LS_DEVICE.match(line)
            if res:
                _, _, group, user, major, minor, _, _, _, name = res.groups()
                results.append({'type': 'block device', 'name': name,
                                'user': user, 'group': group})
        elif line.startswith('c'):
            res = defaults.REGEX_LS_DEVICE.match(line)
            if res:
                _, _, group, user, major, minor, _, _, _, name = res.groups()
                results.append({'type': 'character device', 'name': name,
                                'user': user, 'group': group})
    return results


def parse_ps(ps_log):
    '''Parse output from ps'''

    # This is a bit hackish. Right now a rather fixed
    # output from ps is expected, with a fixed number of
    # columns. Which columns are used depends on the parameters
    # that were given to ps, so for example the output of
    # "ps aux" is different from the output of "ps e".
    # This is a TODO.
    results = []
    header_seen = False
    for line in ps_log.splitlines():
        for p in ['PID  Uid', 'PID Uid', 'PID USER']:
            if p in line:
                header_seen = True
                break

        if not header_seen:
            continue

        if line.endswith(']'):
            continue

        if line in ['</pre>', '</syntaxhighlight>']:
            continue

        # process each line using a regex
        ps_res = defaults.REGEX_PS.search(line)
        if ps_res is not None:
            # extract interesting information here
            ps_line = ps_res.groups()[0]
            res_split = ps_line.split()
            if res_split:
                program = res_split[0]
                program_name = pathlib.Path(program).name
                parameters = res_split[1:]
                program_res = {'type': 'ps', 'name': program_name,
                               'full_name': program, 'parameters': parameters,
                               'ps_line': ps_line}
                results.append(program_res)
    return results

def parse_log(boot_log):
    '''Parse logs, such as boot logs or serial output'''
    # store the interesting findings in a lookup table.
    # This will be a set of software packages (both open source
    # and proprietary) and functionality, as well as names of
    # source code files that were found, that could be used for
    # fingerprinting, as well as other possibly interesting
    # information.
    results = []

    # now try a bunch of regular expressions to find packages
    # BusyBox
    res = defaults.REGEX_BUSYBOX.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'package', 'name': 'busybox', 'versions': set(res)}
        results.append(package_res)

    # iptables
    res = defaults.REGEX_IPTABLES.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'package', 'name': 'iptables', 'versions': set(res)}
        results.append(package_res)

    # Linux kernel version
    res = defaults.REGEX_LINUX_VERSION.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'package', 'name': 'Linux', 'versions': sorted(set(res))}
        results.append(package_res)

    # CFE bootloader. There could be multiple hits in the same log file
    # but the findings should be consolidated somewhere else in the
    # code that is processing the results from this parser.
    res = defaults.REGEX_CFE.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'bootloader', 'name': 'CFE', 'versions': set(res)}
        results.append(package_res)

    res = defaults.REGEX_CFE_BROADCOM.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'bootloader', 'name': 'CFE', 'versions': set(res)}
        results.append(package_res)

    # Ralink U-Boot bootloader (modified U-Boot)
    res = defaults.REGEX_UBOOT_RALINK.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'bootloader', 'name': 'Ralink U-Boot', 'versions': set(res)}
        results.append(package_res)

    # Adtran bootloader (proprietary)
    res = defaults.REGEX_ADTRAN_BOOTLOADER.findall(str(boot_log))
    if res != []:
        package_res = {'type': 'bootloader', 'name': 'adtran bootloader', 'versions': set(res)}
        results.append(package_res)

    # find functionality -- TODO is this actually correct?
    #if 'console [ttyS0] enabled' in str(boot_log):
    #    serial_res = {'type': 'serial port', 'console': 'ttyS0'}
    #    results.append(serial_res)

    # find source code files

    # extract other information
    for i in ['Proprietary', 'proprietary', 'Propritary', 'Motorola Proprietary',
              'Watchguard Proprietary', 'Realtek Semiconductor Corp.', 'Commercial product',
              'Commercial. For support email ntfs-support@tuxera.com.', 'Sercomm', 'sercomm',
              'DNI', '5VT']:
        res = re.findall(fr"(\w+): module license '{i}' taints kernel.", str(boot_log))
        if res != []:
            for r in res:
                module_res = {'type': 'kernel module license', 'license': 'proprietary', 'name': r}
                results.append(module_res)

    for i in ['BSD', 'unspecified', 'unspecid']:
        res = re.findall(fr"(\w+): module license '{i}' taints kernel.", str(boot_log))
        if res != []:
            for r in res:
                if i in ['BSD']:
                    module_res = {'type': 'kernel module license', 'license': i, 'name': r}
                elif i in ['unspecified', 'unspecid']:
                    module_res = {'type': 'kernel module license', 'license': 'unspecified', 'name': r}
                results.append(module_res)

    # Linux kernel command line
    res = defaults.REGEX_LINUX_KERNEL_COMMANDLINE.findall(str(boot_log))
    if res != []:
        # some log lines seem to be split across several lines in the
        # file or have spaces inserted randomly, and sometimes some
        # information is missing or incorrect.
        # Example toh:blueendless:u35wf in OpenWrt
        #  [ 0.000000] Kernel command line: console=ttyS0,115200 rootfstype=squashfs,jff s2
        if set(filter(lambda x: '=' in x, res)):
            command_line_res = {'type': 'Linux kernel commandline', 'values': set(filter(lambda x: len(x.strip()) > 0, res))}
            results.append(command_line_res)

        # extract a few specific commandline parameters
        for fr in res:
            if 'console=' in fr:
                console_res = re.search(r'console=([\w\d]+),(\d+)', fr)
                if console_res is not None:
                    console, baud_rate = console_res.groups()
                    serial_res = {'type': 'serial port', 'console': console, 'baud_rate': int(baud_rate)}
                    results.append(serial_res)
            if 'rootfstype=' in fr:
                rootfs_res = re.search(r'rootfstype=([\w\d,]+)', fr)
                if rootfs_res:
                    rootfs_types = rootfs_res.groups()[0].split(',')
                    rootfstypes_res = {'type': 'rootfstype', 'values': defaults.KNOWN_ROOTFS.intersection(rootfs_types)}
                    results.append(rootfstypes_res)
            if 'root=' in fr:
                root_res = re.search(r'root=([\w\d/:=]+)', fr)
                if root_res:
                    root_results = {'type': 'init', 'value': root_res.groups()[0]}
                    results.append(root_results)
            if 'init=' in fr:
                init_res = re.search(r'init=([\w\d/]+)', fr)
                if init_res:
                    init_results = {'type': 'init', 'value': init_res.groups()[0]}
                    results.append(init_results)
            if 'board=' in fr:
                board_res = re.search(r'board=([\w\d\-]+)', fr)
                if board_res:
                    board_results = {'type': 'board', 'value': board_res.groups()[0]}
                    results.append(board_results)
            if 'mtdparts=' in fr:
                mtdparts = fr.split('mtdparts=')[1].split()[0]
                if '(' in mtdparts:
                    mtdparts_results = re.findall(r'\(([\w\d\-\._]+)\)', mtdparts)
                    if mtdparts_results:
                        mtdparts_result = {'type': 'mtdparts', 'names': mtdparts_results}
                        results.append(mtdparts_result)

    re_squashfs = re.compile(r"squashfs: version ([\w\d\-\.]+) \(\d{4}/\d{2}/\d{2}\) Phillip Lougher")
    if 'squashfs' in str(boot_log):
        res_squashfs = re_squashfs.findall(str(boot_log))
        if res_squashfs:
            squashfss = set(res_squashfs)
            squashfs_res = {'type': 'file system', 'name': 'squashfs', 'versions': list(squashfss), 'notes': ''}
            results.append(squashfs_res)
        if 'version 4.0 with LZMA457 ported by BRCM' in str(boot_log):
            squashfs_res = {'type': 'file system', 'name': 'squashfs', 'versions': [4.0], 'notes': 'LZMA457 ported by BRCM'}
            results.append(squashfs_res)
        if 'version 3.1 includes LZMA decompression support' in str(boot_log):
            squashfs_res = {'type': 'file system', 'name': 'squashfs', 'versions': [3.1], 'notes': 'LZMA decompression support'}
            results.append(squashfs_res)

    re_manufacturer = re.compile(r"NAND device: Manufacturer ID: 0x[\d\w]+, Chip ID: 0x[\d\w]+ \(([\d\w\s/]+) NAND")
    re_manufacturer_2 = re.compile(r"NAND device: Manufacturer ID: 0x[\d\w]+, Chip ID: 0x[\d\w]+ \(([\d\w]+) (\w+)\)")

    if 'NAND device: Manufacturer ID' in str(boot_log):
        res = re_manufacturer.search(str(boot_log))
        if res:
            nand_manufacturer = res.groups()[0]
            serial_res = {'type': 'nand', 'manufacturer': nand_manufacturer}
            results.append(serial_res)
        else:
            res = re_manufacturer_2.search(str(boot_log))
            if res:
                nand_manufacturer = res.groups()[0]
                nand_model = res.groups()[1]
                serial_res = {'type': 'nand', 'manufacturer': nand_manufacturer, 'model': nand_model}
                results.append(serial_res)
    return results

def parse_oui(oui_string):
    '''Parse OUI values, returns a list of values'''
    # various OUI
    ouis = []
    oui_values = oui_string.split(',')
    for oui in oui_values:
        for oui_value in oui.split(';'):
            if oui_value.strip() == '':
                continue
            if defaults.REGEX_OUI.match(oui_value.strip()) is not None:
                new_oui = OUI()
                new_oui.oui = oui_value.strip()
                ouis.append(new_oui)
    return ouis

def parse_chip_openwrt(chip_string):
    '''Parse chips and return a parsed data structure for entries from OpenWrt'''
    # first try to find a known manufacturer
    # Do this by first splitting from the right side,
    # checking if the result is a known manufacturer,
    # and splitting one position further if not, etc.
    chip_result = Chip()
    manufacturer_found = False
    maxsplit = 1
    num_spaces = chip_string.strip().count(' ')

    while True:
        chip_split = chip_string.strip().rsplit(maxsplit=maxsplit)
        chip_manufacturer = defaults.BRAND_REWRITE.get(chip_split[0].strip(), chip_split[0].strip())
        if chip_manufacturer in defaults.CHIP_MANUFACTURERS:
            manufacturer_found = True
            break
        elif len(chip_split) == 1:
            # this is either just a model number without a manufacturer,
            # or bogus data
            break
        else:
            if maxsplit == num_spaces:
                break
            maxsplit += 1

    if manufacturer_found:
        chip_result.manufacturer_verified = True
        chip_result.manufacturer = chip_manufacturer
        chip_model = chip_split[1].strip()
        if chip_model in defaults.CHIP_MANUFACTURERS[chip_manufacturer]:
            chip_result.model_verified = True
            chip_result.model = chip_model
    return chip_result

def parse_chip(chip_string):
    '''Parse chips and return a parsed data structure'''
    chip_result = Chip()
    chip_split = chip_string.split(';')

    # verify the chip manufacturer. This is an extra safe guard
    # against wrong data. The risk is that it should be kept up
    # to date and valid.
    chip_manufacturer = defaults.BRAND_REWRITE.get(chip_split[0].strip(), chip_split[0].strip())

    # TODO: clean up
    if '<!--' in chip_manufacturer:
        return

    if chip_manufacturer in defaults.CHIP_MANUFACTURERS:
        chip_result.manufacturer_verified = True
    chip_result.manufacturer = chip_manufacturer

    # the second entry typically is the model number
    if len(chip_split) > 1:
        chip_model = chip_split[1].strip()
        # TODO: clean up
        if '<!--' in chip_model:
            pass
        elif chip_model != '':
            if chip_model != chip_manufacturer:
                if chip_result.manufacturer_verified and chip_model in defaults.CHIP_MANUFACTURERS[chip_manufacturer]:
                    chip_result.model_verified = True
            chip_result.model = chip_model

    # the remaining data is likely text printed on the chip
    # TODO
    chip_text = "\n".join(chip_split[2:])
    if not ('<!--' in chip_text or '-->' in chip_text):
        # this might need more cleanup
        chip_result.extra_info = chip_text
    return chip_result

def parse_date(date_string):
    '''Parse various variations of dates'''
    try:
        parsed_date = datetime.datetime.strptime(date_string, "%m/%d/%Y")
    except ValueError:
        try:
            parsed_date = datetime.datetime.strptime(date_string, "%d/%m/%Y")
        except ValueError:
            try:
                parsed_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
            except ValueError:
                try:
                    # sometimes only a month and year are given
                    parsed_date = datetime.datetime.strptime(date_string, "%m/%Y")
                except ValueError:
                    return ""
    return parsed_date.strftime("%Y-%m-%d")

def parse_os(os_string):
    '''Parse OS information'''
    result = {}
    fields = os_string.split(';')
    if fields[0] not in defaults.KNOWN_OS:
        return result
    result['os'] = fields[0]

    re_linux_kernel = re.compile(r"^([2-6]\.[\d\w\-\.\+]*)$")

    if len(fields) > 1:
        for field in fields[1:]:
            if fields[0] == 'Linux':
                if field in ['', ',']:
                    continue
                if 'LSDK' in field:
                    # Atheros/Qualcomm Atheros SDK version
                    sdk_splits = field.split('-', maxsplit=1)
                    if len(sdk_splits) == 2:
                        sdk_version = sdk_splits[1]
                    else:
                        sdk_version = ''
                    result['sdk'] = 'LSDK'
                    result['sdk_version'] = sdk_version
                if 'Android' in field:
                    result['distribution'] = 'Android'
                elif 'Debian' in field:
                    result['distribution'] = 'Debian'
                elif 'Ubuntu' in field:
                    result['distribution'] = 'Ubuntu'
                elif 'Fedora' in field:
                    result['distribution'] = 'Fedora'
                elif 'OpenWrt' in field:
                    result['distribution'] = 'OpenWrt'
                elif 'OpenIPC' in field:
                    result['distribution'] = 'OpenIPC'
                elif 'Yocto' in field:
                    result['distribution'] = 'Yocto'
                else:
                    regex_res = re_linux_kernel.match(field)
                    if regex_res is not None:
                        result['kernel_version'] = regex_res.groups()[0]
    return result

def parse_serial_openwrt(log):
    '''Parse serial port information from OpenWrt'''
    result = {}

    # connector
    regex_result = list(set(defaults.REGEX_SERIAL_CONNECTOR.findall(log)))
    if len(regex_result) == 1:
        if 'connector' not in result:
            result['connector'] = regex_result[0]

    # populated
    if 'populated' in log:
        pass

    return result

def parse_serial_jtag(serial_string):
    '''Parse serial port or JTAG information from TechInfoDepot and WikiDevi'''
    result = {}

    fields = serial_string.split(',')

    if fields[0].lower() == 'yes':
        result['has_port'] = 'yes'

    # parse every single field. As there doesn't seem to
    # be a fixed order to store information the only way
    # is to process every single field.
    fields_to_process = []
    for field in fields:
        if field.strip() == '':
            # skip empty fields
            continue
        if field.strip().lower() == 'yes':
            continue
        if field.strip().lower() == 'internal':
            continue
        if ';' in field.strip():
            # fields have been concatenated with ; and
            # should first be split
            fs = field.split(';')
            for ff in fs:
                if ff.strip().strip() == '':
                    # skip empty fields
                    continue
                if ff.strip().lower() == 'yes':
                    continue
                if ff.strip().lower() == 'internal':
                    continue
                fields_to_process.append(ff.strip())
        else:
            fields_to_process.append(field.strip())

    for field in fields_to_process:
        # try to find where the connector can be found
        # (typically which solder pads). TODO: some devices
        # have multiple connectors listed, example:
        # Arndale Board
        if 'connector' not in result:
            regex_result = defaults.REGEX_SERIAL_CONNECTOR.match(field.upper())
            if regex_result is not None:
                result['connector'] = regex_result.groups()[0]
                continue
            regex_result = defaults.REGEX_SERIAL_CONNECTOR2.match(field.upper())
            if regex_result is not None:
                result['connector'] = regex_result.groups()[0]
                continue

        # baud rates
        baud_rate = None
        for br in defaults.BAUD_RATES:
            if str(br) in field:
                baud_rate = br
                result['baud_rate'] = baud_rate
                break

        # data/parity/stop
        for dps in defaults.DATA_PARITY_STOP:
            if dps in field.upper():
                result['data_parity_stop'] = defaults.DATA_PARITY_STOP[dps]
                break

        if baud_rate is not None:
            # verified to be a baud rate
            continue

        # populated or not?
        if 'populated' in field:
            if field == 'unpopulated':
                result['populated'] = 'no'
            elif field == 'populated':
                result['populated'] = 'yes'
            continue

        # voltage
        if field.upper() in ['3.3', '3.3V', '3.3V)', '3.3V TTL', 'TTL 3.3V']:
            result['voltage'] = 3.3
            continue
        if field.upper() in ['1.8', '1.8V', '1.8V TTL', 'TTL 1.8V']:
            result['voltage'] = 1.8
            continue

        # pin header
        regex_result = defaults.REGEX_SERIAL_PIN_HEADER.match(field)
        if regex_result is not None:
            result['number_of_pins'] = int(regex_result.groups()[0])
            continue

        # console via RJ11?
        if 'connector' not in result:
            if field in ['RJ11', 'RJ-11', 'RJ11 port']:
                result['connector'] = 'RJ11'
                continue

        # console via RJ45?
        if 'connector' not in result:
            if field in ['RJ45', 'RJ-45', 'RJ45 console', 'RJ-45 console', 'console port (RJ45)',
                         'console port (RJ-45)', 'console (RJ45)', 'console (RJ-45)', '(RJ45)',
                         'RJ-45 Console port']:
                result['connector'] = 'RJ45'
                continue

        # DE-9 connector
        if 'connector' not in result:
            if field in ['DB9', 'DB-9', '(DB9)', '(DB-9)', 'DB9 (Consol)', 'DE9', 'DE-9',
                         'console port (DE-9)', 'console (DE-9)']:
                result['connector'] = 'DE-9'
                continue

        # USB connector
        if 'connector' not in result:
            if field in ['microUSB', 'USB Female Micro-B', 'USB Female Mini-B',
                         'USB Female (Type-C)', 'USB Micro-B (Female)', 'USB (Type-C) Female',
                         'USB Female (Micro-B)', 'USB Female Type-C', 'USB (Micro-B) Female']:
                result['connector'] = 'USB'
                continue

        # console via HE10?
        if 'connector' not in result:
            if field in ['HE-10', 'HE-10 conn.', '(HE-10 connector']:
                result['connector'] = 'HE10'
                continue

    if result:
        # there are some devices where the first field
        # is not explicitly 'yes' but there is clear serial port
        # information.
        result['has_port'] = 'yes'
    return result

@click.command(short_help='Process TechInfoDepot or WikiDevi XML dump or OpenWrt CSV')
@click.option('--input', '-i', 'input_file', required=True,
              help='Wiki top level dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--output', '-o', 'output_directory', required=True, help='JSON output directory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', required=True,
              type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'], case_sensitive=False))
@click.option('--fcc-grantees', '-g', 'grantees',
              help='file with known FCC grantee codes',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--debug', is_flag=True, help='enable debug logging')
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
def main(input_file, output_directory, wiki_type, grantees, debug, use_git):
    # first some checks to see if the directory for the wiki type already
    # exists and create it if it doesn't exist.
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if use_git:
        if shutil.which('git') is None:
            print("'git' program not installed, exiting.", file=sys.stderr)
            sys.exit(1)

        cwd = os.getcwd()

        os.chdir(output_directory)

        # verify the output directory is a valid Git repository
        p = subprocess.Popen(['git', 'status', output_directory],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (outputmsg, errormsg) = p.communicate()
        if p.returncode == 128:
            print(f"{output_directory} is not a Git repository, exiting.", file=sys.stderr)
            sys.exit(1)

    fcc_grantees = {}
    if grantees:
        with open(grantees, 'r') as grantee:
            try:
                fcc_grantees = json.load(grantee)
            except json.decoder.JSONDecodeError:
                pass

    wiki_directory = output_directory / wiki_type
    wiki_directory.mkdir(parents=True, exist_ok=True)

    wiki_device_directory = output_directory / wiki_type / 'devices'
    wiki_device_directory.mkdir(parents=True, exist_ok=True)

    wiki_network_adapter_directory = output_directory / wiki_type / 'network_adapters'
    wiki_network_adapter_directory.mkdir(parents=True, exist_ok=True)

    wiki_original_directory = output_directory / wiki_type / 'original'
    wiki_original_directory.mkdir(parents=True, exist_ok=True)

    if wiki_type in ['TechInfoDepot', 'WikiDevi']:
        # load XML
        with open(input_file) as wiki_dump:
            wiki_info = defusedxml.minidom.parse(wiki_dump)

        # store which devices were processed. This is information needed
        # when processing so called "helper pages" which do not need to be
        # processed if the original file is not processed.
        processed_devices = {}
        updated_devices = set()

        # now walk the XML. It depends on the dialect (WikiDevi, TechInfoDepot)
        # how the contents should be parsed, as the pages are laid out in
        # a slightly different way.
        #
        # Each device is stored in a separate page.
        for p in wiki_info.getElementsByTagName('page'):
            title = ''
            is_helper_page = False

            # Walk the child elements of the page
            for child in p.childNodes:
                if child.nodeName == 'title':
                    # first store the title of the page but skip
                    # special pages such as 'Category' pages
                    # (TechInfoDepot only)
                    title = child.childNodes[0].data
                    if title.startswith('Category:'):
                        break
                    if title.startswith('List of '):
                        break

                    # some pages are actually "helper pages", not full
                    # devices, but they can add possibly useful information
                    for t in defaults.HELPER_PAGE_TITLES:
                        if title.lower().endswith(t):
                            is_helper_page = True
                            break

                elif child.nodeName == 'ns':
                    # devices can only be found in namespace 0 in both
                    # techinfodepot and wikidevi.
                    namespace = int(child.childNodes[0].data)
                    if namespace != 0:
                        break

                    # store the original data (per page)
                    # TODO: add support for Git
                    out_name = f"{title}.xml"
                    out_name = out_name.replace('/', '-')
                    orig_xml_file = wiki_original_directory / out_name
                    new_file = True
                    data_changed = True
                    out_data = p.toxml()
                    if orig_xml_file.exists():
                        new_file = False
                        with open(wiki_original_directory / out_name, 'r') as out_file:
                            orig_data = out_file.read()
                            if out_data == orig_data:
                                data_changed = False

                    if data_changed:
                        with open(wiki_original_directory / out_name, 'w') as out_file:
                            out_file.write(out_data)

                    if data_changed and use_git:
                        # add the file
                        p = subprocess.Popen(['git', 'add', orig_xml_file],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                        (outputmsg, errormsg) = p.communicate()
                        if p.returncode != 0:
                            print(f"{orig_xml_file} could not be added", file=sys.stderr)

                        if new_file:
                            commit_message = f'Add {out_name}'
                        else:
                            commit_message = f'Update {out_name}'

                        p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                        (outputmsg, errormsg) = p.communicate()
                        if p.returncode != 0:
                            print(f"{orig_xml_file} could not be committed", file=sys.stderr)

                elif child.nodeName == 'revision':
                    if is_helper_page:
                        # see if the device this is a helper page for was processed
                        parent_title = pathlib.Path(title).parent.name
                        if parent_title not in processed_devices:
                            continue
                        updated_devices.add(parent_title)
                    for c in child.childNodes:
                        if c.nodeName == 'text':
                            # grab the wiki text and parse it. This data
                            # is in the <text> element
                            wiki_text = c.childNodes[0].data
                            wikicode = mwparserfromhell.parse(wiki_text)

                            # reset device information
                            device = None
                            have_valid_data = False

                            # walk the elements in the parsed wiki text.
                            # Kind of assume a fixed order here. This is maybe a
                            # bit risky, but so far it seems to work (no exceptions
                            # have been observed).
                            # There are different elements in the Wiki text:
                            #
                            # * headings
                            # * templates
                            # * text
                            # * tags
                            #
                            # These could all contain interesting information

                            data_url = title.replace(' ', '_')
                            device_origin = Origin()
                            device_origin.data_url = data_url
                            device_origin.origin = wiki_type

                            if not is_helper_page:
                                for f in wikicode.filter(recursive=False):
                                    if isinstance(f, mwparserfromhell.nodes.template.Template):
                                        if f.name in ['Wireless embedded system\n', 'Wired embedded system\n', 'Infobox Embedded System\n']:
                                            # create a new Device() for each entry
                                            device = Device()
                                            device.title = title
                                            device.origins.append(device_origin)
                                        elif f.name in ['Infobox Network Adapter\n']:
                                            device = NetworkAdapter()
                                            device.title = title
                                            device.origins.append(device_origin)
                                        elif f.name in ['Infobox USB Hub\n']:
                                            device = USBHub()
                                            device.title = title
                                            device.origins.append(device_origin)
                            else:
                                device = processed_devices[parent_title]

                            if not device:
                                continue

                            for f in wikicode.filter(recursive=False):
                                if isinstance(f, mwparserfromhell.nodes.heading.Heading):
                                    # the heading itself doesn't contain data that
                                    # needs to be stored, but it provides insights of what
                                    # information follows as content
                                    pass
                                elif isinstance(f, mwparserfromhell.nodes.template.Template):
                                    if f.name.strip() == 'TIDTOC':
                                        # this element contains no interesting information
                                        continue

                                    if f.name.strip() in ['SCollapse', 'SCollapse2']:
                                        # alternative place for boot log, GPL info, /proc, etc.
                                        is_processed = False
                                        wiki_section_header = f.params[0].strip()
                                        for b in ['boot log', 'Boot log', 'Bootlog', 'stock boot messages']:
                                            if wiki_section_header.startswith(b):
                                                is_processed = True

                                                # parse and store the boot log.
                                                # TODO: further mine the boot log
                                                parse_results = parse_log(f.params[1].value)
                                                for p in parse_results:
                                                    if p['type'] == 'package':
                                                        found_package = Package()
                                                        found_package.name = p['name']
                                                        found_package.package_type = p['type']
                                                        found_package.versions = p['versions']
                                                        device.software.packages.append(found_package)
                                                        if p['name'] == 'Linux':
                                                            if device.software.os == '':
                                                                device.software.os = p['name']
                                                    elif p['type'] == 'bootloader':
                                                        found_package = Package()
                                                        found_package.name = p['name']
                                                        found_package.package_type = p['type']
                                                        found_package.versions = p['versions']
                                                        device.software.packages.append(found_package)
                                                    elif p['type'] == 'serial port':
                                                        if device.has_serial_port == 'no':
                                                            # Something strange is going on here,
                                                            # most likely a data interpretation error
                                                            pass
                                                        elif device.has_serial_port == 'unknown':
                                                            # The device actually has a serial port.
                                                            device.has_serial_port = 'yes'
                                                        if device.has_serial_port == 'yes':
                                                            if 'baud_rate' in p:
                                                                if device.serial.baud_rate == 0:
                                                                    device.serial.baud_rate = p['baud_rate']
                                                                elif device.serial.baud_rate != p['baud_rate']:
                                                                    # Sigh. This shouldn't happen.
                                                                    pass
                                                    elif p['type'] == 'mtdparts':
                                                        for name in sorted(set(p['names'])):
                                                            partition = Partition()
                                                            partition.name = name
                                                            device.software.partitions.append(partition)
                                                break
                                        if is_processed:
                                            have_valid_data = True
                                            continue
                                        if wiki_section_header.startswith('GPL info'):
                                            # there actually does not seem to be anything related
                                            # to GPL source code releases in this element, but
                                            # mostly settings like environment variables for
                                            # compiling source code.
                                            pass
                                        elif wiki_section_header.startswith('lsmod'):
                                            # the output of lsmod can be parsed to see which
                                            # Linux kernel modules are used on a device. By mapping
                                            # these back to source code some extra information
                                            # could be obtained: some modules are only present in
                                            # some SDKs, and so on.
                                            pass
                                        elif wiki_section_header.startswith('nvram'):
                                            # the nvram can contain useful information about
                                            # a device. Some entries found here are not from
                                            # the stock firmware, but from third party firmware
                                            # so care has to be taken to filter these prior
                                            # to processing.
                                            pass
                                        elif 'dmesg' in wiki_section_header:
                                            # like bootlogs the output of dmesg can contain
                                            # very useful information.
                                            pass
                                        elif wiki_section_header.startswith('ls -la'):
                                            parse_results = parse_ls(f.params[1].value)
                                            for parse_result in parse_results:
                                                ls_file = File()
                                                ls_file.file_type = parse_result['type']
                                                ls_file.name = parse_result['name']
                                                ls_file.user = parse_result['user']
                                                ls_file.group = parse_result['group']
                                                device.software.files.append(ls_file)
                                        elif wiki_section_header.startswith('ps'):
                                            # the output of ps can contain the names
                                            # of programs and executables
                                            for p in ['PID  Uid', 'PID Uid', 'PID USER']:
                                                if p in f.params[1].value:
                                                    parse_results = parse_ps(f.params[1].value)
                                                    for parse_result in parse_results:
                                                        prog = Program()
                                                        prog.origin = parse_result['type']
                                                        prog.name = parse_result['name']
                                                        prog.full_name = parse_result['full_name']
                                                        prog.parameters = parse_result['parameters']
                                                        device.software.programs.append(prog)
                                                    break
                                        elif wiki_section_header.startswith('Serial console output'):
                                            pass
                                        elif wiki_section_header.lower().startswith('serial info'):
                                            # some of the entries found in the data seem to be
                                            # serial console output, instead of serial port
                                            # information.
                                            pass
                                        elif wiki_section_header.lower().startswith('cat /proc/mtd'):
                                            # possibly interesting
                                            pass
                                        elif wiki_section_header.lower().startswith('firmware'):
                                            # this seems to be largely bogus data, so skip
                                            pass
                                        elif wiki_section_header.lower().startswith('cpuinfo, mtd, bootlog'):
                                            # possibly useful information can be
                                            # extracted from this section
                                            pass
                                        elif wiki_section_header.lower().startswith('oem tty'):
                                            # possibly useful information can be extracted from this section
                                            pass
                                        elif wiki_section_header.lower().startswith('changelog'):
                                            # unsure if there is anything useful here
                                            pass
                                        elif wiki_section_header.lower().startswith('telnet'):
                                            # possibly useful information can be extracted from this section
                                            pass
                                        else:
                                            pass
                                    elif f.name == 'WiFiCert':
                                        # WiFi certification information
                                        if len(f.params) >= 2:
                                            wifi_cert, wifi_cert_date = f.params[:2]
                                            device.regulatory.wifi_certified = str(wifi_cert.value)
                                            wifi_cert_date = str(wifi_cert_date.value)
                                            device.regulatory.wifi_certified_date = parse_date(wifi_cert_date)
                                    elif f.name in ['hasPowerSupply\n', 'HasPowerSupply\n']:
                                        # some elements are a list, the first one
                                        # will always contain the identifier
                                        for param in f.params:
                                            param_elems = param.strip().split('\n')
                                            identifier, value = param_elems[0].split('=', maxsplit=1)

                                            # remove superfluous spaces
                                            identifier = identifier.strip()
                                            value = value.strip()

                                            match identifier:
                                                case 'brand':
                                                    device.power_supply.brand = defaults.BRAND_REWRITE.get(value, value)
                                                case 'model':
                                                    device.power_supply.model = value
                                                case 'revision':
                                                    device.power_supply.revision = value
                                                case 'style':
                                                    device.power_supply.style = defaults.STYLE_REWRITE.get(value, value)
                                                case 'countrymanuf':
                                                    device.power_supply.country = value
                                                case 'input_a':
                                                    device.power_supply.input_amperage = value
                                                case 'input_c':
                                                    device.power_supply.input_current = value
                                                case 'input_conn':
                                                    device.power_supply.input_connection = value
                                                case 'input_hz':
                                                    device.power_supply.input_hz = value
                                                case 'input_v':
                                                    device.power_supply.input_voltage = value
                                                case 'output_a':
                                                    device.power_supply.output_amperage = value
                                                case 'output_c':
                                                    device.power_supply.output_current = value
                                                case 'outpuc_c':
                                                    device.power_supply.output_current = value
                                                case 'output_conn':
                                                    device.power_supply.input_connection = value
                                                case 'output_v':
                                                    device.power_supply.output_voltage = value
                                                case 'e_level':
                                                    device.power_supply.e_level = value
                                        continue

                                    # WikiDevi stores some information in different places than
                                    # TechInfoDepot. TechInfoDepot tries to squeeze as much as possible
                                    # into the 'infobox', whereas WikiDevi uses separate elements.
                                    if wiki_type == 'WikiDevi':
                                        if f.name == 'TagLine':
                                            for param in f.params:
                                                tagline = str(param.value.strip())
                                                device.taglines.append(defaults.TAGLINES_REWRITE.get(tagline, tagline))
                                        elif f.name == 'TechInfoDepot':
                                            value = str(f.params[0])
                                            if value != '':
                                                device.web.techinfodepot = value
                                        elif f.name == 'ProductPage':
                                            # parse the product page value
                                            for param in f.params:
                                                value = str(param)
                                                if '://' not in value:
                                                    continue
                                                if not value.startswith('http'):
                                                    continue
                                                try:
                                                    # TODO: fix this check
                                                    urllib.parse.urlparse(value)
                                                except ValueError:
                                                    continue
                                                device.web.product_page.append(value)

                                    if f.name in ['Wireless embedded system\n', 'Wired embedded system\n', 'Infobox Embedded System\n']:
                                        # These elements are typically the most interesting item
                                        # on a page, containing hardware information.
                                        #
                                        # The information is stored in so called "parameters".
                                        # These parameters consist of one or more lines,
                                        # separated by a newline. The first line always
                                        # contains the identifier and '=', followed by a
                                        # value. Subsequent lines are values belonging to
                                        # the same identifier.
                                        have_valid_data = True

                                        num_radios = 0
                                        num_cpus = 0

                                        if wiki_type == 'TechInfoDepot':
                                            # First walk the params to see how many ASINs,
                                            # radios and CPUs are used. there can be multiple
                                            # versions of the same data but instead of a list the
                                            # identifiers contain a number. Example: in the
                                            # TechnInfoDepot data there are multiple Amazon ASINs
                                            # associated with devices. These are called asin, asin1,
                                            # asin2, asin3, etc.

                                            num_asins = 0
                                            for param in f.params:
                                                if '=' in param:

                                                    # some elements are a list, the first one
                                                    # will always contain the identifier
                                                    param_elems = param.strip().split('\n')
                                                    identifier, value = param_elems[0].split('=', maxsplit=1)
                                                    identifier = identifier.strip()
                                                    value = value.strip()

                                                    is_default = False
                                                    for default_value in defaults.DEFAULT_VALUE.get(identifier, []):
                                                        if value == default_value:
                                                            is_default = True
                                                            break

                                                    if is_default or value == '':
                                                        continue

                                                    if identifier in defaults.KNOWN_ASIN_IDENTIFIERS:
                                                        num_asins = max(num_asins, defaults.KNOWN_ASIN_IDENTIFIERS.index(identifier) + 1)
                                                    elif identifier in defaults.KNOWN_RADIO_IDENTIFIERS_TID:
                                                        num_radios = max(num_radios, int(identifier[3:4]))
                                                    elif identifier in defaults.KNOWN_CPU_IDENTIFIERS_TID:
                                                        num_cpus = max(num_cpus, int(identifier[3:4]))

                                            # create the right amount of ASINs
                                            for i in range(num_asins):
                                                device.commercial.amazon_asin.append(Amazon_ASIN())
                                        elif wiki_type == 'WikiDevi':
                                            for param in f.params:
                                                if not '=' in param:
                                                    continue
                                                identifier = param.strip().split('=')[0]
                                                if identifier in defaults.KNOWN_RADIO_IDENTIFIERS_WD:
                                                    num_radios = max(num_radios, int(identifier[2:3]))
                                                if identifier in defaults.KNOWN_CPU_IDENTIFIERS_WD:
                                                    num_cpus = max(num_cpus, int(identifier[3:4]))

                                        # create the right amount of radio elements
                                        for i in range(num_radios):
                                            device.radios.append(Radio())

                                        for param in f.params:
                                            if '=' in param:
                                                # some elements are a list, the first one
                                                # will always contain the identifier
                                                param_elems = param.strip().split('\n')
                                                identifier, value = param_elems[0].split('=', maxsplit=1)

                                                param_values = []

                                                # remove superfluous spaces
                                                identifier = identifier.strip()
                                                param_values.append(value.strip())
                                                for p in param_elems[1:]:
                                                    param_values.append(p.strip())

                                                for value in param_values:
                                                    if value == '':
                                                        continue

                                                    if wiki_type == 'TechInfoDepot':
                                                        # Determine if the value is one of the default
                                                        # values that can be skipped. Default values
                                                        # only seem to be used in TechInfoDepot.
                                                        is_default = False

                                                        if value in defaults.DEFAULT_VALUE.get(identifier, []):
                                                            continue

                                                        # A few values can be safely skipped as they
                                                        # are not interesting or of very low quality.
                                                        if identifier in set(['dimensions', 'estprice', 'weight',
                                                                          'image1_size', 'image2_size',
                                                                          'nvramsize', 'ram1size', 'ram2size',
                                                                          'ram3size', 'flash1size', 'flash2size',
                                                                          'flash3size', 'flash1maxsize',
                                                                          'flash2maxsize', 'cpu1spd', 'cpu1spd2',
                                                                          'cpu2spd', 'gpu1spd', 'ram1spd',
                                                                          'submodelappend']):
                                                            continue
                                                    if wiki_type == 'WikiDevi':
                                                        if identifier in ['price']:
                                                            continue

                                                    # then process all 300+ identifiers. Note: most of
                                                    # these identifiers only have a single value and
                                                    # will only appear once, so it is safe to just
                                                    # override the default value defined in the
                                                    # dataclass. The exceptions here are 'addchip'
                                                    # (TechInfoDepot) and 'addl_chips' (WikiDevi).
                                                    if identifier == 'brand':
                                                        if '<!--' in value and not value.startswith('<!--'):
                                                            brand = value.split('<!--')[0].strip()
                                                        else:
                                                            brand = value
                                                        device.brand = defaults.BRAND_REWRITE.get(brand, brand)
                                                    elif identifier == 'model':
                                                        device.model.model = value
                                                    elif identifier == 'revision':
                                                        device.model.revision = value
                                                    elif identifier == 'series':
                                                        device.model.series = value
                                                    elif identifier == 'type':
                                                        device_types = [x.strip() for x in value.split(',') if x.strip() != '']
                                                        for d in device_types:
                                                            device.device_types.append(defaults.DEVICE_REWRITE.get(d, d))
                                                        device.device_types.sort()
                                                    elif identifier == 'flags':
                                                        device.flags = sorted([x.strip() for x in value.split(',') if x.strip() != ''])
                                                    elif identifier in ['boardid', 'pcb_id']:
                                                        if '<!--' in value:
                                                            continue
                                                        device.model.pcb_id = value
                                                    elif identifier in ['image1', 'image2']:
                                                        device.images.append(value)

                                                    # commercial information
                                                    elif identifier == 'availability':
                                                        device.commercial.availability = value
                                                    elif identifier in ['estreldate', 'est_release_date', 'est_reoease_date']:
                                                        device.commercial.release_date = parse_date(value)
                                                    elif identifier == 'dx_sku':
                                                        device.commercial.deal_extreme = value
                                                    elif identifier in ['newegg', 'neweyg']:
                                                        eggs = value.split(',')
                                                        for egg in eggs:
                                                            if egg.strip() == '':
                                                                continue
                                                            if '<!' in egg:
                                                                continue
                                                            device.commercial.newegg.append(egg.strip())
                                                    elif identifier == 'upc':
                                                        upcs = value.split(',')
                                                        for upc in upcs:
                                                            if upc.strip().startswith('B'):
                                                                # skip ASIN
                                                                continue
                                                            device.commercial.upc.append(upc.strip())
                                                    elif identifier == 'ean':
                                                        eans = value.split(',')
                                                        for ean in eans:
                                                            if ean.strip() == '':
                                                                continue
                                                            if '<!' in ean:
                                                                continue
                                                            if ean.strip().startswith('B'):
                                                                # skip ASIN
                                                                continue
                                                            device.commercial.ean.append(ean.strip())

                                                    # default values: IP, login, passwd, etc.
                                                    elif identifier in ['defaulip', 'default_ip']:
                                                        # verify IP address via regex.
                                                        # TODO: clean up for example:
                                                        # * Compal Broadband Networks CH7465LG-LC
                                                        # * Ruckus Wireless ZoneFlex 7055
                                                        #
                                                        # Also extract optional port for the default web interface
                                                        # if present, example:
                                                        # * D-Link DWL-1750
                                                        ip_res = defaults.REGEX_IP.match(value)
                                                        if ip_res is not None:
                                                            device.defaults.ip = ip_res.groups()[0]
                                                        else:
                                                            match value:
                                                                case 'acquired via DHCP':
                                                                    device.defaults.ip_comment = value
                                                    elif identifier in ['defaultlogin', 'default_user']:
                                                        if ' or ' in value:
                                                            device.defaults.logins = value.split(' or ')
                                                        else:
                                                            match value:
                                                                case 'randomly generated':
                                                                    device.defaults.logins_comment = value
                                                                case 'set at first login':
                                                                    device.defaults.logins_comment = value
                                                                case other:
                                                                    device.defaults.logins = [value]
                                                    elif identifier in ['defaultpass', 'default_pass']:
                                                        if '<!--' in value:
                                                            continue
                                                        match value:
                                                            # ignore the following two values as it is
                                                            # unclear if these are default wiki values,
                                                            # or if they are describing the actual password
                                                            case '<!-- Leave blank -->':
                                                                pass
                                                            case '<!-- Leave blank --> -->':
                                                                pass
                                                            case '\'\'unit\'s serial number\'\'':
                                                                device.defaults.password_comment = 'unit\'s serial number'
                                                            case '(sticker on the bottom of device)':
                                                                device.defaults.password_comment = 'sticker on the bottom of the device'
                                                            case 'On the back of the router':
                                                                device.defaults.password_comment = value
                                                            case 'random 8 digit dispaly on the LCD':
                                                                device.defaults.password_comment = 'random 8 digit displayed on the LCD'
                                                            case 'randomly generated':
                                                                device.defaults.password_comment = value
                                                            case '\'randomly generated\'':
                                                                device.defaults.password_comment = 'randomly generated'
                                                            case '\'\'randomly generated\'\'':
                                                                device.defaults.password_comment = 'randomly generated'
                                                            case 'set at first login':
                                                                device.defaults.password_comment = value
                                                            case 'set on first login':
                                                                device.defaults.password_comment = 'set at first login'
                                                            case 'QR Code':
                                                                device.defaults.password_comment = value
                                                            case other:
                                                                device.defaults.password = value
                                                    elif identifier in ['defaultssid', 'default_ssid']:
                                                        ssids = list(map(lambda x: x.strip(), value.split(',')))
                                                        device.defaults.ssids = ssids
                                                    elif identifier in ['defaultssid_regex', 'default_ssid_regex']:
                                                        ssids = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.defaults.ssid_regexes = ssids

                                                    # manufacturer
                                                    elif identifier in ['countrymanuf', 'manuf_country']:
                                                        device.manufacturer.country = defaults.COUNTRY_REWRITE.get(value, value)
                                                    elif identifier == 'manuf':
                                                        if device.manufacturer.name == '':
                                                            if '<!--' in value and not value.startswith('<!--'):
                                                                manuf = value.split('<!--')[0].strip()
                                                            else:
                                                                manuf = value
                                                            device.manufacturer.name = defaults.BRAND_REWRITE.get(manuf, manuf)
                                                    elif identifier == 'manuf_model':
                                                        device.manufacturer.model = value
                                                    elif identifier in ['manuf_rev', 'manuf_revision']:
                                                        device.manufacturer.revision = value
                                                    elif identifier in set(['is_manuf', 'is_anuf', 'is_mamuf', 'is_manyf', 'if_manuf', 'os_manuf']):
                                                        # if the brand is also is the ODM simply
                                                        # copy the brand. This assumes that the
                                                        # brand is already known (which has been
                                                        # the case in all data seen so far)
                                                        if value.lower() in ['yes', 'yesyes', 'true']:
                                                            device.manufacturer.name = device.brand

                                                    # regulatory
                                                    elif identifier in ['fccapprovdate', 'fcc_date']:
                                                        try:
                                                            device.regulatory.fcc_ids[0].fcc_date = parse_date(value)
                                                        except ValueError:
                                                            continue
                                                        except IndexError:
                                                            # fcc date without an FCC id. Sigh.
                                                            continue
                                                    elif identifier == 'fcc_id':
                                                        # some devices have more than one FCC id.
                                                        fcc_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        for f in fcc_values:
                                                            if '<!--' in f:
                                                                if not f.startswith('<!--'):
                                                                    fcc_value = f.split('<!--')[0]
                                                                else:
                                                                    if f.endswith('-->'):
                                                                        fcc_value = f.split('<!--', maxsplit=1)[1][:-3].strip()
                                                                    else:
                                                                        fcc_value = f
                                                            else:
                                                                fcc_value = f
                                                            if fcc_value.startswith('2'):
                                                                grantee_code = fcc_value[:5]
                                                            else:
                                                                grantee_code = fcc_value[:3]
                                                                if not grantee_code[0].isalpha():
                                                                    continue

                                                            new_fcc = FCC()
                                                            new_fcc.fcc_id = fcc_value.strip()
                                                            new_fcc.grantee = fcc_grantees.get(grantee_code, "")

                                                            device.regulatory.fcc_ids.append(new_fcc)
                                                    elif identifier == 'us_id':
                                                        usid_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.regulatory.us_ids = usid_values
                                                    elif identifier in ['icid', 'ic_id']:
                                                        # some devices have more than one IC id.
                                                        icid_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.regulatory.industry_canada_ids = icid_values

                                                    # serial port
                                                    elif identifier == 'serial':
                                                        if value.lower() in ['no', 'none', 'none,']:
                                                            device.has_serial_port = 'no'
                                                            continue

                                                        serial_result = parse_serial_jtag(value)

                                                        if 'has_port' in serial_result:
                                                            device.has_serial_port = serial_result['has_port']
                                                        if 'connector' in serial_result:
                                                            device.serial.connector = serial_result['connector']
                                                        if 'baud_rate' in serial_result:
                                                            device.serial.baud_rate = serial_result['baud_rate']
                                                        if 'populated' in serial_result:
                                                            device.serial.populated = serial_result['populated']
                                                        if 'voltage' in serial_result:
                                                            device.serial.voltage = serial_result['voltage']
                                                        if 'number_of_pins' in serial_result:
                                                            device.serial.number_of_pins = serial_result['number_of_pins']
                                                        if 'data_parity_stop' in serial_result:
                                                            device.serial.data_parity_stop = serial_result['data_parity_stop']

                                                    # JTAG
                                                    elif identifier == 'jtag':
                                                        if value.lower() in ['no', 'none', 'none,']:
                                                            device.has_jtag = 'no'
                                                            continue

                                                        jtag_result = parse_serial_jtag(value)

                                                        if 'has_port' in jtag_result:
                                                            device.has_jtag = jtag_result['has_port']
                                                        if 'connector' in jtag_result:
                                                            device.jtag.connector = jtag_result['connector']
                                                        if 'baud_rate' in jtag_result:
                                                            device.jtag.baud_rate = jtag_result['baud_rate']
                                                        if 'populated' in jtag_result:
                                                            device.jtag.populated = jtag_result['populated']
                                                        if 'voltage' in jtag_result:
                                                            device.jtag.voltage = jtag_result['voltage']
                                                        if 'number_of_pins' in jtag_result:
                                                            device.jtag.number_of_pins = jtag_result['number_of_pins']

                                                    # third party firmware
                                                    elif identifier in ['tpfirmware', 'tp_firmware']:
                                                        if '<!-- Third' in value:
                                                            value = value.split('<!--', 1)[0]
                                                        tp_firmwares = value.split(',')
                                                        for tp_firmware in tp_firmwares:
                                                            tp_firmware = defaults.DISTRO_REWRITE.get(tp_firmware.strip(), tp_firmware.strip())
                                                            if tp_firmware == '':
                                                                continue

                                                            match tp_firmware.lower():
                                                                case 'openwrt':
                                                                    device.software.third_party.append('OpenWrt')
                                                                case 'lede':
                                                                    device.software.third_party.append('LEDE')
                                                                case 'cerowrt':
                                                                    device.software.third_party.append('CeroWrt')
                                                                case 'dd-wrt':
                                                                    device.software.third_party.append('DD-WRT')
                                                                case 'librewrt':
                                                                    device.software.third_party.append('LibreWRT')
                                                                case 'debian':
                                                                    device.software.third_party.append('Debian')
                                                                case 'armbian':
                                                                    device.software.third_party.append('Armbian')
                                                                case 'ubuntu':
                                                                    device.software.third_party.append('Ubuntu')
                                                                case 'gentoo':
                                                                    device.software.third_party.append('Gentoo')
                                                                case 'slackware':
                                                                    device.software.third_party.append('Slackware')
                                                                case 'gargoyle':
                                                                    device.software.third_party.append('Gargoyle')
                                                                case 'android':
                                                                    device.software.third_party.append('Android')
                                                                case 'fuchsia':
                                                                    device.software.third_party.append('Fuchsia')
                                                                case 'qnx':
                                                                    device.software.third_party.append('QNX')
                                                                case 'padavan':
                                                                    device.software.third_party.append('Padavan')
                                                                case 'vampik':
                                                                    device.software.third_party.append('Vampik')
                                                                case 'wive-ng':
                                                                    device.software.third_party.append('Wive-NG')
                                                                case 'freebsd':
                                                                    device.software.third_party.append('FreeBSD')
                                                                case 'netbsd':
                                                                    device.software.third_party.append('NetBSD')
                                                                case 'openbsd':
                                                                    device.software.third_party.append('OpenBSD')
                                                                case 'openipc':
                                                                    device.software.third_party.append('OpenIPC')
                                                        device.software.third_party.sort()

                                                    # additional chip
                                                    elif identifier in ['addchip', 'addl_chips']:
                                                        if value == ',,,':
                                                            continue

                                                        # here the first entry *should* be a description
                                                        if value.startswith(',,,'):
                                                            chip_splits = value.split(' ', maxsplit=1)
                                                            addchip = chip_splits[1].strip()
                                                        else:
                                                            addchip = value
                                                        if ';' not in addchip:
                                                            continue

                                                        # split the data in a description and the
                                                        # chip data to be parsed. There could be
                                                        # some more chips hidden in the chip data,
                                                        # because the wiki data isn't clean and entries
                                                        # are not clearly split. This is a TODO.
                                                        description, chipinfo = addchip.split(';', maxsplit=1)
                                                        chip_result = parse_chip(chipinfo.strip())
                                                        if chip_result is not None:
                                                            chip_result.description = description
                                                            device.additional_chips.append(chip_result)

                                                    # various OUI
                                                    elif identifier in ['ethoui', 'oui_eth', 'oui']:
                                                        ouis = parse_oui(value.upper())
                                                        for oui_value in ouis:
                                                            if identifier in ['ethoui', 'oui_eth']:
                                                                device.network.ethernet_oui.append(oui_value)
                                                            elif identifier == 'oui':
                                                                device.network.wireless_oui.append(oui_value)

                                                    elif identifier in ['stockos', 'stock_os']:
                                                        if device.software.os == '':
                                                            # parse stock OS information
                                                            result = parse_os(value)
                                                            if result:
                                                                device.software.os = result['os']
                                                    elif identifier in ['stockbootloader', 'stock_bootloader', 'stock_boot']:
                                                        bootloader_split = value.split(';')

                                                        # first entry is the manufacturer. There might be cruft here.
                                                        if '<!--' in bootloader_split[0]:
                                                            # there are a few entries in the database where the data is
                                                            # actually in the comment. Sigh.
                                                            bootloader_manufacturer = bootloader_split[0].split('<')[0].strip()
                                                        else:
                                                            bootloader_manufacturer = bootloader_split[0].strip()
                                                        device.software.bootloader.manufacturer = defaults.BRAND_REWRITE.get(bootloader_manufacturer, bootloader_manufacturer)

                                                        if len(bootloader_split) >= 2:
                                                            bootloader_version = bootloader_split[1].strip()
                                                            if bootloader_version != '':
                                                                device.software.bootloader.version = bootloader_version
                                                            for extra_info in range(2, len(bootloader_split)):
                                                                inf = bootloader_split[extra_info].strip()
                                                                if inf != '':
                                                                    if 'vendor modified' in inf or 'vender modified' in inf:
                                                                        device.software.bootloader.vendor_modified = 'yes'
                                                                    device.software.bootloader.extra_info.append(inf)

                                                    # network
                                                    elif identifier == 'lan_ports':
                                                        try:
                                                            device.network.lan_ports = int(value)
                                                        except ValueError:
                                                            pass

                                                    # power
                                                    elif identifier == 'pwr_conn':
                                                        if value == 'barrel':
                                                            device.power.connector = 'barrel'
                                                    elif identifier == 'pwr_barrel_inner':
                                                        try:
                                                            device.power.inner_barrel_size = float(value)
                                                        except ValueError:
                                                            pass
                                                    elif identifier == 'pwr_barrel_len':
                                                        try:
                                                            device.power.barrel_length = float(value)
                                                        except ValueError:
                                                            pass
                                                    elif identifier == 'pwr_barrel_outer':
                                                        try:
                                                            device.power.outer_barrel_size = float(value)
                                                        except ValueError:
                                                            pass

                                                    elif identifier in ['exp_if_types', 'expansion_if_types']:
                                                        if value == 'none':
                                                            continue
                                                        if '<!' in value:
                                                            # TODO: process this correctly
                                                            continue

                                                        expansions = value.split(',')
                                                        for expansion in expansions:
                                                            if expansion.strip() == '':
                                                                continue
                                                            ex = defaults.EXPANSION_REWRITE.get(expansion.strip().lower(), expansion.strip())
                                                            device.expansions.append(ex)
                                                        device.expansions.sort()

                                                    # process TechInfoDepot specific information
                                                    if wiki_type == 'TechInfoDepot':
                                                        if identifier == 'model_part_num':
                                                            device.model.part_number = value
                                                        elif identifier == 'sernum':
                                                            device.model.serial_number = value
                                                        elif identifier == 'subrevision':
                                                            if value != '(??)':
                                                                device.model.subrevision = value
                                                        elif identifier == 'submodel':
                                                            device.model.submodel = value
                                                        elif identifier in ['caption', 'caption2']:
                                                            device.taglines.append(defaults.TAGLINES_REWRITE.get(value, value))

                                                        # commercial information (continued)
                                                        elif identifier == 'eoldate':
                                                            device.commercial.end_of_life_date = parse_date(value)
                                                        elif identifier in defaults.KNOWN_ASIN_IDENTIFIERS:
                                                            # verify ASIN address via regex
                                                            if defaults.REGEX_ASIN.match(value) is not None:
                                                                num_asin = defaults.KNOWN_ASIN_IDENTIFIERS.index(identifier)
                                                                device.commercial.amazon_asin[num_asin].asin = value
                                                        elif identifier in defaults.KNOWN_ASIN_COUNTRY_IDENTIFIERS:
                                                            if len(value) == 2:
                                                                num_asin = defaults.KNOWN_ASIN_COUNTRY_IDENTIFIERS.index(identifier)
                                                                device.commercial.amazon_asin[num_asin].country = value

                                                        # cpu
                                                        elif identifier in ['cpu1chip1', 'cpu2chip1']:
                                                            chip_index = int(identifier[3]) - 1
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.cpus.append(chip_result)

                                                        elif identifier in ['cpu1_type', 'cpu2_type']:
                                                            if '<!--' in value:
                                                                # TODO: fix
                                                                continue
                                                            chip_index = int(identifier[3]) - 1
                                                            try:
                                                                device.cpus[chip_index].chip_type = value
                                                            except IndexError:
                                                                continue

                                                        elif identifier in ['cpu1_type_rev', 'cpu2_type_rev']:
                                                            if '<!--' in value:
                                                                # TODO: fix
                                                                continue
                                                            chip_index = int(identifier[3]) - 1
                                                            try:
                                                                device.cpus[chip_index].chip_type_revision = value
                                                            except IndexError:
                                                                continue

                                                        # network (continued)
                                                        elif identifier == 'auto_mdix':
                                                            if value.lower() == 'yes':
                                                                device.network.mdix = 'yes'
                                                            elif value.lower() == 'no':
                                                                device.network.mdix = 'no'
                                                        elif identifier == 'sup_jumbo':
                                                            if value.lower() == 'yes':
                                                                device.network.jumbo_frames = 'yes'
                                                            elif value.lower() == 'no':
                                                                device.network.jumbo_frames = 'no'
                                                        elif identifier == 'docsisver':
                                                            if value.startswith('v'):
                                                                device.network.docsis_version = value[1:]
                                                            else:
                                                                device.network.docsis_version = value
                                                        elif identifier in ['eth1chip', 'eth2chip', 'eth3chip',
                                                                            'eth4chip', 'eth5chip', 'eth6chip']:
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.network.chips.append(chip_result)

                                                        # various OUI
                                                        elif identifier in ['rad1oui', 'rad2oui',
                                                                            'rad3oui', 'rad4oui']:
                                                            ouis = parse_oui(value.upper())
                                                            for oui_value in ouis:
                                                                radio_num = int(identifier[3:4])
                                                                device.radios[radio_num - 1].oui.append(oui_value)

                                                        # flash chips
                                                        elif identifier in ['fla1chip', 'fla2chip', 'fla3chip']:
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.flash.append(chip_result)

                                                        # switch chips
                                                        elif identifier in ['sw1chip', 'sw2chip', 'sw3chip']:
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.switch.append(chip_result)

                                                        # RAM chips
                                                        elif identifier in ['ram1chip', 'ram2chip', 'ram3chip']:
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.ram.append(chip_result)

                                                        # radio
                                                        elif identifier in ['rad1chip1', 'rad1chip2', 'rad1chip3',
                                                                            'rad2chip1', 'rad2chip2', 'rad2chip3',
                                                                            'rad3chip1', 'rad3chip2', 'rad3chip3',
                                                                            'rad4chip1', 'rad4chip2', 'rad4chip3']:
                                                            # first grab the number of the radio element from the identifier
                                                            radio_num = int(identifier[3:4])
                                                            radio_chip = parse_chip(value)
                                                            if radio_chip is not None:
                                                                device.radios[radio_num - 1].chips.append(radio_chip)

                                                        elif identifier in ['rad1mod', 'rad2mod', 'rad3mod', 'rad4mod']:
                                                            # TODO: filter entries with <!--
                                                            radio_num = int(identifier[3:4])
                                                            device.radios[radio_num - 1].module = value
                                                        elif identifier in ['rad1modif', 'rad2modif', 'rad3modif', 'rad4modif']:
                                                            # TODO: filter entries with <!--
                                                            radio_num = int(identifier[3:4])
                                                            device.radios[radio_num - 1].interface = value

                                                        # software information
                                                        elif identifier == 'stock_os_sdk':
                                                            # overwrite SDK if empty
                                                            if device.software.sdk == '':
                                                                device.software.sdk = value

                                                        # third party firmware
                                                        elif identifier in ['ddwrtsupport', 'gargoylesupport',
                                                                            'openwrtsupport', 'tomatosupport']:
                                                            continue

                                                        # web
                                                        elif identifier == 'dl':
                                                            if not '://' in value:
                                                                continue
                                                            if not value.startswith('http'):
                                                                continue
                                                            try:
                                                                # TODO: fix this check
                                                                urllib.parse.urlparse(value)
                                                            except ValueError:
                                                                continue
                                                            device.web.download_page = value
                                                        elif identifier in ['pp', 'pp2', 'pp3']:
                                                            # parse the product page value
                                                            if not '://' in value:
                                                                continue
                                                            if not value.startswith('http'):
                                                                continue
                                                            try:
                                                                # TODO: fix this check
                                                                urllib.parse.urlparse(value)
                                                            except ValueError:
                                                                continue
                                                            if '<!--' in value:
                                                                # some people only adapted the default value
                                                                # and didn't remove the comment parts.
                                                                if value.startswith('<!-- ') and value.endswith(' -->'):
                                                                    device.web.product_page.append(value[5:-4].strip())
                                                                else:
                                                                    device.web.product_page.append(value.split('<!-- ')[0].strip())
                                                            else:
                                                                device.web.product_page.append(value)
                                                        elif identifier in ['sp', 'sp2', 'supportpage']:
                                                            # parse the support page value
                                                            if not '://' in value:
                                                                continue
                                                            try:
                                                                # TODO: fix this check
                                                                urllib.parse.urlparse(value)
                                                            except ValueError:
                                                                continue
                                                            if '<!--' in value:
                                                                # some people only adapted the default value
                                                                # and didn't remove the comment parts.
                                                                if value.startswith('<!-- ') and value.endswith(' -->'):
                                                                    device.web.support_page.append(value[5:-4].strip())
                                                                else:
                                                                    device.web.support_page.append(value.split('<!-- ')[0].strip())
                                                            else:
                                                                device.web.support_page.append(value)
                                                        elif identifier == 'wikidevi':
                                                            if '<!--' in value:
                                                                # some people only adapted the default value
                                                                # and didn't remove the comment parts.
                                                                if value.startswith('<!-- ') and value.endswith(' -->'):
                                                                    device.web.support_page.append(value[5:-4].strip())
                                                                    device.web.wikidevi = value[5:-4].strip()
                                                                else:
                                                                    device.web.wikidevi = value.split('<!-- ')[0].strip()
                                                            else:
                                                                device.web.wikidevi = value
                                                        # Low quality data, ignore for now
                                                        elif identifier == 'wikipedia':
                                                            #device.web.wikipedia = value
                                                            pass

                                                        else:
                                                            if debug:
                                                                # print values, but only if they aren't already
                                                                # skipped or processed. This is useful for discovering
                                                                # default values and variants.
                                                                # TODO: also print values that weren't correctly processed
                                                                print(identifier, value, file=sys.stderr)
                                                    # process WikiDevi specific information
                                                    elif wiki_type == 'WikiDevi':
                                                        if identifier == 'asin':
                                                            if '<!--' in value:
                                                                continue
                                                            if ',' in value:
                                                                asin_split = [x for x in value.split(',') if x != '']
                                                                for a in asin_split:
                                                                    if ';' in a:
                                                                        new_asin_split = [x for x in a.split(';') if x != '']
                                                                        if len(new_asin_split) == 2:
                                                                            new_asin = Amazon_ASIN()
                                                                            if defaults.REGEX_ASIN.match(new_asin_split[0]) is not None:
                                                                                new_asin.asin = new_asin_split[0].strip()
                                                                            else:
                                                                                continue
                                                                            if new_asin_split[1].strip() in defaults.KNOWN_ASIN_COUNTRIES:
                                                                                new_asin.country = new_asin_split[1].strip()
                                                                            device.commercial.amazon_asin.append(new_asin)
                                                                        elif len(new_asin_split) == 1:
                                                                            if defaults.REGEX_ASIN.match(new_asin_split[0].strip()) is not None:
                                                                                new_asin = Amazon_ASIN()
                                                                                new_asin.asin = new_asin_split[0].strip()
                                                                                device.commercial.amazon_asin.append(new_asin)
                                                                    else:
                                                                        if defaults.REGEX_ASIN.match(a.strip()) is not None:
                                                                            new_asin = Amazon_ASIN()
                                                                            new_asin.asin = a.strip()
                                                                            device.commercial.amazon_asin.append(new_asin)
                                                            elif ';' in value:
                                                                asin_split = [x for x in value.split(';') if x != '']
                                                                if len(asin_split) == 2:
                                                                    new_asin = Amazon_ASIN()
                                                                    if defaults.REGEX_ASIN.match(asin_split[0]) is not None:
                                                                        new_asin.asin = asin_split[0].strip()
                                                                    else:
                                                                        continue
                                                                    if asin_split[1].strip() in defaults.KNOWN_ASIN_COUNTRIES:
                                                                        new_asin.country = asin_split[1].strip()
                                                                    device.commercial.amazon_asin.append(new_asin)
                                                            else:
                                                                if defaults.REGEX_ASIN.match(value) is not None:
                                                                    new_asin = Amazon_ASIN()
                                                                    new_asin.asin = value
                                                                    device.commercial.amazon_asin.append(new_asin)
                                                        # cpu
                                                        elif identifier in ['cpu1_brand']:
                                                            chip_index = int(identifier[3]) - 1
                                                            chip_result = parse_chip(value)
                                                            if chip_result is not None:
                                                                device.cpus.append(chip_result)

                                                        elif identifier in ['wi1_module', 'wi2_module', 'wi3_module', 'wi4_module']:
                                                            # first grab the number of the radio element from the identifier
                                                            radio_num = int(identifier[2:3])
                                                            device.radios[radio_num - 1].module = value
                                                        elif identifier in ['wi1_module_if', 'wi2_module_if', 'wi3_module_if', 'wi4_module_if']:
                                                            # first grab the number of the radio element from the identifier
                                                            radio_num = int(identifier[2:3])
                                                            device.radios[radio_num - 1].interface = value
                                                        else:
                                                            if debug:
                                                                # print values, but only if they aren't already
                                                                # skipped or processed. This is useful for discovering
                                                                # default values and variants.
                                                                # TODO: also print values that weren't correctly processed
                                                                print(identifier, value, file=sys.stderr)
                                        else:
                                            pass
                                    elif f.name in ['Infobox Network Adapter\n']:
                                        pass
                                    elif f.name in ['Infobox USB Hub\n']:
                                        pass

                                elif isinstance(f, mwparserfromhell.nodes.text.Text):
                                    pass
                                elif isinstance(f, mwparserfromhell.nodes.tag.Tag):
                                    pass
                                else:
                                    pass

                            if not have_valid_data:
                                continue

                            processed_devices[title] = device

                            # use the title as part of the file name as it is unique
                            if is_helper_page:
                                model_name = f"{parent_title}.json"
                            else:
                                model_name = f"{title}.json"
                            model_name = model_name.replace('/', '-')

                            new_file = True

                            json_data = json.dumps(json.loads(device.to_json()), sort_keys=True)
                            processed_json_file = wiki_device_directory / model_name

                            # first check if the file has changed if it already exists.
                            # If not, then don't add the file.
                            if processed_json_file.exists():
                                new_file = False
                                with open(processed_json_file, 'r') as json_file:
                                    try:
                                        existing_json = json.dumps(json.load(json_file))
                                        if existing_json == json_data:
                                            continue
                                    except json.decoder.JSONDecodeError:
                                        pass

                            # write to a file in the correct Git directory
                            with open(processed_json_file, 'w') as json_file:
                                json_data = json.dumps(json.loads(device.to_json()), sort_keys=True, indent=4)
                                json_file.write(json_data)

                            # Write to a Git repository to keep some history
                            if use_git:
                                # add the file
                                p = subprocess.Popen(['git', 'add', processed_json_file],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{processed_json_file} could not be added", file=sys.stderr)

                                if new_file:
                                    commit_message = f'Add {model_name}'
                                else:
                                    commit_message = f'Update {model_name}'

                                p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{processed_json_file} could not be committed", file=sys.stderr)

                            # write extra data (extracted from free text) to a separate file
                            if is_helper_page:
                                model_name = f"{parent_title}.data.json"
                            else:
                                model_name = f"{title}.data.json"

                            model_name = model_name.replace('/', '-')
                            #output_file = wiki_device_directory / model_name
                            #with output_file.open('w') as out:
                            #    out.write(json.dumps(json.loads(device.to_json()), indent=4))
                            #    out.write('\n')

    elif wiki_type == 'OpenWrt':
        bootlog_hints = ['Boot log (Factory)', 'EdgeOS Bootlog', 'Factory bootlog',
                         'Factory Bootlog', 'OEM bootlog', 'OEM Bootlog', 'OEM bootloader log',
                         'OEM bootloader bootlog', 'OEM factory reset log', 'OEM failsafe bootlog',
                         'OEM firmware bootlog', 'OEM (original firmware) bootlog',
                         'OEM (stock firmware) bootlog', 'OEM U-Boot bootlog', 'Old boot log',
                         'Original bootlog', 'Original Bootlog', 'Original firmware bootlog',
                         'Original firmware Boot log', 'Quantenna bootlog', 'Serial boot log',
                         'Stock firmware bootlog', 'Stock Firmware Bootlog', 'Stock FW bootlog',
                         'u-boot bootlog', 'U-boot bootlog', 'U-Boot bootlog', 'U-Boot log',
                         'Vendor firmware bootlog', 'Xiaomi bootlog']

        serial_page_hints = ['Serial port', 'Serial', 'How to connect to the Serial Port (UART)']

        # the OpenWrt CSV dump has 74 fields, but only a few
        # are (currently) interesting (see documentation in doc/ )
        OpenWrtDevice = namedtuple('OpenWrtDevice', 'pid, devicetype, brand, model, version, fccid, availability, whereavailable, supportedsincecommit, supportedsincerel, supportedcurrentrel, unsupported_functions, target, subtarget, packagearchitecture, bootloader, cpu, cpucores, cpumhz, flashmb, rammb, ethernet100mports, ethernetgbitports, ethernet1gports, ethernet2_5gports, ethernet5gports, ethernet10gports, sfp_ports, sfp_plus_ports, switch, vlan, modem, commentsnetworkports, wlanhardware, wlan24ghz, wlan50ghz, wlancomments, wlandriver, detachableantennas, bluetooth, usbports, sataports, commentsusbsataports, videoports, audioports, phoneports, commentsavports, serial, serialconnectionparameters, jtag, ledcount, buttoncount, gpios, powersupply, devicepage, device_techdata owrt_forum_topic_url, lede_forum_topic_url, forumsearch, gitsearch, wikideviurl, oemdevicehomepageurl, firmwareoemstockurl, firmwareopenwrtinstallurl, firmwareopenwrtupgradeurl, firmwareopenwrtsnapshotinstallurl, firmwareopenwrtsnapshotupgradeurl, installationmethods, commentinstallation, recoverymethods, commentrecovery, picture, comments, page')
        with open(input_file) as toh:
            csv_reader = csv.reader(toh, dialect='excel-tab')
            is_first_line = True
            for line in csv_reader:
                if is_first_line:
                    is_first_line = False
                    continue

                owrt = OpenWrtDevice._make(line)
                if not owrt.page.startswith('toh:hwdata:'):
                    continue

                # check if the page with hardware information was downloaded and if so,
                # load contents. The CSV and this hardware page contain different information.
                # Example: Serial connection voltage is not available in the CSV.
                owrt_page_values = {}
                if owrt.devicepage and (wiki_original_directory / owrt.page).exists():
                    with open(wiki_original_directory / owrt.page, 'r') as dp:
                        owrtpage = dp.readlines()
                        seen_techdata = False
                        for line in owrtpage:
                            if line.startswith('---- dataentry techdata ----'):
                                seen_techdata = True
                                continue
                            if not seen_techdata:
                                continue
                            if line.startswith('----'):
                                break
                            if line.startswith('Serial connection voltage_serialvoltage'):
                                voltage = line.split(':')[1].split('#')[0].strip()
                                if voltage in ['', '¿']:
                                    continue
                                if voltage == '3.3V':
                                    owrt_page_values['serial_connection_voltage'] = 3.3
                                else:
                                    owrt_page_values['serial_connection_voltage'] = float(voltage)

                # check if a device page was downloaded and if so, load contents
                devicepage = ""
                if owrt.devicepage and (wiki_original_directory / owrt.devicepage).exists():
                    with open(wiki_original_directory / owrt.devicepage, 'r') as dp:
                        devicepage = dp.read()

                # first create a Device() and fill in some of the details
                device = Device()
                device.brand = defaults.BRAND_REWRITE.get(owrt.brand, owrt.brand)
                device.model.model = owrt.model
                if owrt.version != 'NULL':
                    device.model.version = owrt.version

                device.title = owrt.page.split(':')[-1]

                device_origin = Origin()
                device_origin.data_url = owrt.page
                device_origin.origin = 'OpenWrt'
                device.origins.append(device_origin)

                if owrt.devicetype.strip() != '':
                    device_type = owrt.devicetype.strip().lower()
                    device.device_types.append(defaults.DEVICE_REWRITE.get(device_type, device_type))

                # Chips. Should be taken with a grain of salt (ha. ha.)
                # because it seems that this doesn't only cover the main
                # CPU, but also additional chips. Without adding a lot of
                # extra knowledge it is hard to make this distinction.
                if owrt.cpu not in ['¿']:
                    for cpu in owrt.cpu.split(','):
                        chip_result = parse_chip_openwrt(cpu.strip())
                        device.cpus.append(chip_result)

                # FCC information
                if owrt.fccid != 'NULL':
                    fccids = owrt.fccid.split(',')
                    for fccid in fccids:
                        valid_fcc = False
                        fcc_split = fccid.split('://')[1]
                        if '/' not in fcc_split:
                            continue

                        site, fcc_id = fcc_split.split('/', maxsplit=1)
                        if site == 'fcc.report':
                            fcc_id = fcc_id.split('/', maxsplit=1)[1]

                        fcc_id = fcc_id.upper()

                        if fcc_id.startswith('ANATEL'):
                            # Brazilian FCC equivalent
                            continue

                        fcc_id = fcc_id.replace('/', '')

                        if fcc_split.startswith('2'):
                            grantee_code = fcc_id[:5]
                            valid_fcc = True
                        else:
                            grantee_code = fcc_id[:3]
                            if grantee_code[0].isalpha():
                                valid_fcc = True

                        if valid_fcc:
                            new_fcc = FCC()
                            new_fcc.fcc_id = fcc_id.strip()
                            new_fcc.grantee = fcc_grantees.get(grantee_code, "")
                            device.regulatory.fcc_ids.append(new_fcc)

                # serial port
                if owrt.serial.lower() == 'no':
                    device.has_serial_port = 'no'
                elif owrt.serial.lower() == 'yes':
                    device.has_serial_port = 'yes'

                if device.has_serial_port == 'yes':
                    if 'serial_connection_voltage' in owrt_page_values:
                        device.serial.voltage = owrt_page_values['serial_connection_voltage']
                    if owrt.serialconnectionparameters.strip() not in ['¿', '']:
                        # this doesn't include the connector on the board or the voltage
                        baud_rate, data_parity_stop = owrt.serialconnectionparameters.strip().replace('/', ' ').split()
                        try:
                            baud_rate = int(baud_rate)
                            if baud_rate in defaults.BAUD_RATES:
                                device.serial.baud_rate = baud_rate
                            if data_parity_stop in defaults.DATA_PARITY_STOP:
                                device.serial.data_parity_stop = defaults.DATA_PARITY_STOP[data_parity_stop]
                        except:
                            pass
                else:
                    if owrt.serialconnectionparameters.strip() not in ['¿', '']:
                        # TODO: what to do here? It seems that the OpenWrt
                        # data isn't consistent here.
                        pass

                # JTAG
                if owrt.jtag.lower() == 'no':
                    device.has_jtag = 'no'
                elif owrt.jtag.lower() == 'yes':
                    device.has_jtag = 'yes'

                if owrt.wikideviurl != 'NULL':
                    wikidevi_split = owrt.wikideviurl.split('://')[1]
                    if '/' not in wikidevi_split:
                        pass
                    elif not 'wikidevi.wi-cat.ru' in wikidevi_split:
                        pass
                    else:
                        wikidevi_split = wikidevi_split.replace('index.php/', '')
                        wikidevi_name = wikidevi_split.split('/', maxsplit=1)[1]
                        device.web.wikidevi = wikidevi_name

                if owrt.bootloader not in ['¿', 'other']:
                    device.software.bootloader.manufacturer = defaults.BRAND_REWRITE.get(owrt.bootloader, owrt.bootloader)

                # third party support (OpenWrt only)
                if owrt.supportedsincecommit.strip() not in ['', 'http://¿']:
                    device.software.third_party.append('OpenWrt')
                    device.software.openwrt = 'yes'

                # now process any logs in the device page, if available
                if devicepage:
                    for i in bootlog_hints:
                        if i in devicepage:
                            bootlog = []
                            seen_start = False
                            for line in devicepage.split('\n'):
                                if line.startswith('=') and i in line:
                                    seen_start = True
                                    continue
                                if not seen_start:
                                    continue
                                if '</nowiki>' in line or '</WRAP>' in line:
                                    break
                                bootlog.append(line)
                            # parse and store the boot log.
                            # TODO: further mine the boot log
                            parse_results = parse_log("\n".join(bootlog))
                            for p in parse_results:
                                if p['type'] == 'package':
                                    found_package = Package()
                                    found_package.name = p['name']
                                    found_package.package_type = p['type']
                                    found_package.versions = p['versions']
                                    device.software.packages.append(found_package)
                                    if p['name'] == 'Linux':
                                        if device.software.os == '':
                                            device.software.os = p['name']
                                elif p['type'] == 'bootloader':
                                    found_package = Package()
                                    found_package.name = p['name']
                                    found_package.package_type = p['type']
                                    found_package.versions = p['versions']
                                    device.software.packages.append(found_package)
                                elif p['type'] == 'serial port':
                                    if device.has_serial_port == 'no':
                                        # Something strange is going on here,
                                        # most likely a data interpretation error
                                        pass
                                    elif device.has_serial_port == 'unknown':
                                        # The device actually has a serial port.
                                        device.has_serial_port = 'yes'
                                    if device.has_serial_port == 'yes':
                                        if 'baud_rate' in p:
                                            if device.serial.baud_rate == 0:
                                                device.serial.baud_rate = p['baud_rate']
                                            elif device.serial.baud_rate != p['baud_rate']:
                                                # Sigh. This shouldn't happen.
                                                pass
                                elif p['type'] == 'mtdparts':
                                    for name in sorted(set(p['names'])):
                                        partition = Partition()
                                        partition.name = name
                                        device.software.partitions.append(partition)
                    for i in serial_page_hints:
                        if i in devicepage:
                            serial_page = []
                            seen_start = False
                            for line in devicepage.split('\n'):
                                if line.startswith('=') and i == re.split('=+', line)[1].strip():
                                    seen_start = True
                                    continue
                                if not seen_start:
                                    continue
                                if line.startswith('='):
                                    break
                                serial_page.append(line)
                            if serial_page:
                                serial_result = parse_serial_openwrt("\n".join(serial_page))
                                if 'connector' in serial_result:
                                    device.serial.connector = serial_result['connector']
                                device.serial.comments = "\n".join(serial_page)
                                break

                # use the title as part of the file name as it is unique
                model_name = f"{device.title}.json"
                model_name = model_name.replace('/', '-')

                new_file = True

                json_data = json.dumps(json.loads(device.to_json()), sort_keys=True)
                processed_json_file = wiki_device_directory / model_name

                # first check if the file has changed if it already exists.
                # If not, then don't add the file.
                if processed_json_file.exists():
                    new_file = False
                    with open(processed_json_file, 'r') as json_file:
                        try:
                            existing_json = json.dumps(json.load(json_file))
                            if existing_json == json_data:
                                continue
                        except json.decoder.JSONDecodeError:
                            pass

                # write to a file in the correct Git directory
                with open(processed_json_file, 'w') as json_file:
                    json_data = json.dumps(json.loads(device.to_json()), sort_keys=True, indent=4)
                    json_file.write(json_data)

                # Write to a Git repository to keep some history
                if use_git:
                    # add the file
                    p = subprocess.Popen(['git', 'add', processed_json_file],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                    (outputmsg, errormsg) = p.communicate()
                    if p.returncode != 0:
                        print(f"{processed_json_file} could not be added", file=sys.stderr)

                    if new_file:
                        commit_message = f'Add {model_name}'
                    else:
                        commit_message = f'Update {model_name}'

                    p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                    (outputmsg, errormsg) = p.communicate()
                    if p.returncode != 0:
                        print(f"{processed_json_file} could not be committed", file=sys.stderr)



if __name__ == "__main__":
    main()
