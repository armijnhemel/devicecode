#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click
import dulwich
import dulwich.porcelain
import mwparserfromhell

import devicecode_defaults as defaults

AUTHOR = "DeviceCode <example@example.org>"

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
    price: float = 0.0
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
class Network:
    '''Networking information'''
    chips: list[Chip] = field(default_factory=list)
    jumbo_frames: str = 'unknown'
    lan_ports: int = 0
    mdix: str = 'unknown'
    docsis_version: str = ''
    # https://en.wikipedia.org/wiki/Organizationally_unique_identifier
    ethernet_oui: list[str] = field(default_factory=list)
    wireless_oui: list[str] = field(default_factory=list)

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
    model: str = ''
    interface: str = ''

    # https://en.wikipedia.org/wiki/Organizationally_unique_identifier
    oui: list[str] = field(default_factory=list)
    standard: str = ''

@dataclass_json
@dataclass
class Regulatory:
    '''Regulatory information such as FCC
       as well as certification such as Wi-Fi Certified'''
    # all dates are YYYY-MM-DD
    fcc_ids: list[str] = field(default_factory=list)
    fcc_approved_date: str = ''

    industry_canada_ids: list[str] = field(default_factory=list)

    # related to some US phone company regulations?
    us_ids: list[str] = field(default_factory=list)

    # WiFi alliance
    wifi_certified: str = ''
    wifi_certified_date: str = ''

@dataclass_json
@dataclass
class Serial:
    connector: str = ''
    populated: str = 'unknown'
    voltage: float = None
    baud_rate: int = 0
    number_of_pins: int = 0

@dataclass_json
@dataclass
class Software:
    '''Software information: stock OS/bootloader, third party support'''
    bootloader: Bootloader = field(default_factory=Bootloader)
    os: str = ''
    sdk: str = ''
    ddwrt: str = 'unknown'
    gargoyle: str = 'unknown'
    openwrt: str = 'unknown'
    tomato: str = 'unknown'
    third_party: list[str] = field(default_factory=list)

@dataclass_json
@dataclass
class Web:
    '''Various webpages associated with the device'''
    download_page: str = ''
    product_page: list[str] = field(default_factory=list)
    support_page: list[str] = field(default_factory=list)
    wikidevi: str = ''
    wikipedia: str = ''

@dataclass_json
@dataclass
class Model:
    '''Model information'''
    board_id: str = ''
    model: str = ''
    part_number: str = ''
    revision: str = ''
    serial_number: str = ''
    series: str = ''
    submodel: str = ''
    subrevision: str = ''

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

def parse_ls(ls_log):
    '''Parse output from ls'''
    pass


def parse_ps(ps_log):
    '''Parse output from ps'''

    # This is a bit hackish. Right now a rather fixed
    # output from ps is expected, with a fixed number of
    # columns. Which columns are used depends on the parameters
    # that were given to ps, so for example the output of
    # "ps aux" is different from the output of "ps e".
    # This is a TODO.
    header_seen = False
    for line in ps_log.splitlines():
        if 'PID  Uid' in line:
            header_seen = True
            continue

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
            pass
    return

def parse_log(boot_log):
    '''Parse logs, such as boot logs or serial output'''

    # store the interesting findings in a lookup table.
    # This will be a set of software packages (both open source
    # and proprietary) and functionality, as well as names of
    # source code files that were found, that could be used for
    # fingerprinting
    interesting_findings = {}

    # now try a bunch of regular expressions to find packages
    # BusyBox
    res = defaults.REGEX_BUSYBOX.findall(str(boot_log))
    if res != []:
        interesting_findings['busybox'] = set(res)

    # Linux kernel version
    res = defaults.REGEX_LINUX_VERSION.findall(str(boot_log))
    if res != []:
        interesting_findings['Linux'] = set(res)

    # CFE bootloader
    res = defaults.REGEX_CFE.findall(str(boot_log))
    if res != []:
        interesting_findings['CFE'] = set(res)

    res = defaults.REGEX_CFE_BROADCOM.findall(str(boot_log))
    if res != []:
        if 'CFE' in interesting_findings:
            interesting_findings['CFE'].update(set(res))
        else:
            interesting_findings['CFE'] = set(res)

    # Ralink U-Boot bootloader (modified U-Boot)
    res = defaults.REGEX_UBOOT_RALINK.findall(str(boot_log))
    if res != []:
        interesting_findings['Ralink U-Boot'] = set(res)

    # Adtran bootloader (proprietary)
    res = defaults.REGEX_ADTRAN_BOOTLOADER.findall(str(boot_log))
    if res != []:
        interesting_findings['adtran bootloader'] = set(res)

    # find functionality

    # find source code files

    # extract other information

    # Linux kernel command line
    res = defaults.REGEX_LINUX_KERNEL_COMMANDLINE.findall(str(boot_log))
    if res != []:
        interesting_findings['Linux kernel commandline'] = set(res)

    return interesting_findings

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
                ouis.append(oui_value.strip())
    return ouis

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


@click.command(short_help='Process TechInfoDepot or WikiDevi XML dump')
@click.option('--input', '-i', 'input_file', required=True,
              help='Wiki top level dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--output', '-o', 'output_directory', required=True, help='JSON output directory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', required=True,
              type=click.Choice(['TechInfoDepot', 'WikiDevi'], case_sensitive=False))
@click.option('--debug', is_flag=True, help='enable debug logging')
@click.option('--no-git', is_flag=True, help='do not use Git')
def main(input_file, output_directory, wiki_type, debug, no_git):
    # load XML
    with open(input_file) as wiki_dump:
        wiki_info = defusedxml.minidom.parse(wiki_dump)

    # first some checks to see if the directory for the wiki type already
    # exists and create it if it doesn't exist.
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.")
        sys.exit(1)

    if not no_git:
        # verify the output directory is a valid Git repository
        try:
            repo = dulwich.porcelain.open_repo(output_directory)
        except dulwich.errors.NotGitRepository:
            print(f"{output_directory} is not a valid Git repository, exiting", file=sys.stderr)
            sys.exit(1)

    wiki_directory = output_directory / wiki_type
    wiki_directory.mkdir(parents=True, exist_ok=True)

    wiki_device_directory = output_directory / wiki_type / 'devices'
    wiki_device_directory.mkdir(parents=True, exist_ok=True)

    # now walk the XML. It depends on the dialect (WikiDevi, TechInfoDepot)
    # how the contents should be parsed, as the pages are laid out in
    # a slightly different way.
    #
    # Each device is stored in a separate page.
    for p in wiki_info.getElementsByTagName('page'):
        title = ''
        valid_device = False

        # Walk the child elements of the page
        for child in p.childNodes:
            if child.nodeName == 'title':
                # first store the title of the page but skip
                # special pages such as 'Category' pages
                title = child.childNodes[0].data
                if title.startswith('Category:'):
                    break
            elif child.nodeName == 'revision':
                # further process the device data
                valid_device = True

                for c in child.childNodes:
                    if c.nodeName == 'text':
                        # create a new Device() for each entry
                        device = Device()
                        device.title = title

                        # grab the wiki text and parse it. This data
                        # is in the <text> element
                        wiki_text = c.childNodes[0].data
                        wikicode = mwparserfromhell.parse(wiki_text)

                        # walk the elements in the parsed wiki text.
                        # Kind of assume a fixed order here.
                        # There are different elements in the Wiki text:
                        #
                        # * headings
                        # * templates
                        # * text
                        # * tags
                        #
                        # These could all contain interesting information

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
                                if wiki_type == 'TechInfoDepot':
                                    if f.name == 'Infobox Embedded System\n':
                                        # The "Infobox" is the most interesting item
                                        # on a page, containing hardware information.
                                        #
                                        # The information is stored in so called "parameters".
                                        # These parameters consist of one or more lines,
                                        # separated by a newline. The first line always
                                        # contains the identifier and '=', followed by a
                                        # value. Subsequent lines are values belonging to
                                        # the same identifier.

                                        # First walk the params to see how many ASINs,
                                        # radios and CPUs are used. In the TechInfoDepot data
                                        # there can be multiple versions of the same data
                                        # but instead of a list the identifiers contain
                                        # a number. Example: there are multiple Amazon ASINs
                                        # associated with devices. These are called asin, asin1,
                                        # asin2, asin3, etc.

                                        num_cpus = 0
                                        num_asins = 0
                                        num_radios = 0
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
                                                elif identifier in defaults.KNOWN_RADIO_IDENTIFIERS:
                                                    num_radios = max(num_radios, int(identifier[3:4]))

                                        # create the right amount of radio elements
                                        for i in range(num_radios):
                                            device.radios.append(Radio())

                                        # create the right amount of ASINs
                                        for i in range(num_asins):
                                            device.commercial.amazon_asin.append(Amazon_ASIN())

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
                                                    # determine if the value is one of the
                                                    # default values that can be skipped
                                                    is_default = False

                                                    for default_value in defaults.DEFAULT_VALUE.get(identifier, []):
                                                        if value == default_value:
                                                            is_default = True
                                                            break

                                                    if is_default or value == '':
                                                        continue

                                                    # A few values can be safely skipped as they
                                                    # are not interesting or of very low quality.
                                                    if identifier in ['dimensions', 'estprice', 'weight',
                                                                      'image1_size', 'image2_size',
                                                                      'nvramsize', 'ram1size', 'ram2size',
                                                                      'ram3size', 'flash1size', 'flash2size',
                                                                      'flash3size', 'flash1maxsize',
                                                                      'flash2maxsize', 'cpu1spd', 'cpu1spd2',
                                                                      'cpu2spd', 'gpu1spd', 'ram1spd',
                                                                      'submodelappend']:
                                                        continue

                                                    # then process all 300+ identifiers. Note: most of
                                                    # these identifiers only have a single value, so it
                                                    # is safe to just override the default value defined in
                                                    # the dataclass. The exception here is 'addchip'.
                                                    if identifier == 'brand':
                                                        device.brand = defaults.BRAND_REWRITE.get(value, value)
                                                    elif identifier == 'boardid':
                                                        if '<!--' in value:
                                                            continue
                                                        device.model.board_id = value
                                                    elif identifier == 'model':
                                                        device.model.model = value
                                                    elif identifier == 'model_part_num':
                                                        device.model.part_number = value
                                                    elif identifier == 'revision':
                                                        device.model.revision = value
                                                    elif identifier == 'series':
                                                        device.model.series = value
                                                    elif identifier == 'sernum':
                                                        device.model.serial_number = value
                                                    elif identifier == 'subrevision':
                                                        if value != '(??)':
                                                            device.model.subrevision = value
                                                    elif identifier == 'submodel':
                                                        device.model.submodel = value
                                                    elif identifier == 'type':
                                                        device_types = list(map(lambda x: x.strip(), value.split(',')))
                                                        device.device_types= device_types
                                                    elif identifier == 'flags':
                                                        device.flags = sorted(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                    elif identifier in ['caption', 'caption2']:
                                                        device.taglines.append(value)
                                                    elif identifier in ['image1', 'image2']:
                                                        device.images.append(value)
                                                    elif identifier == 'exp_if_types':
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

                                                    # commercial information
                                                    elif identifier == 'availability':
                                                        device.commercial.availability = value
                                                    elif identifier == 'estreldate':
                                                        device.commercial.release_date = parse_date(value)
                                                    elif identifier == 'eoldate':
                                                        device.commercial.end_of_life_date = parse_date(value)
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
                                                            if ean.strip().startswith('B'):
                                                                # skip ASIN
                                                                continue
                                                            device.commercial.ean.append(ean.strip())
                                                    elif identifier == 'newegg':
                                                        eggs = value.split(',')
                                                        for egg in eggs:
                                                            device.commercial.newegg.append(egg.strip())
                                                    elif identifier in defaults.KNOWN_ASIN_IDENTIFIERS:
                                                        # verify ASIN address via regex
                                                        if defaults.REGEX_ASIN.match(value) is not None:
                                                            num_asin = defaults.KNOWN_ASIN_IDENTIFIERS.index(identifier)
                                                            device.commercial.amazon_asin[num_asin].asin = value
                                                    elif identifier in defaults.KNOWN_ASIN_COUNTRY_IDENTIFIERS:
                                                        if len(value) == 2:
                                                            num_asin = defaults.KNOWN_ASIN_COUNTRY_IDENTIFIERS.index(identifier)
                                                            device.commercial.amazon_asin[num_asin].country = value

                                                    # default values: IP, login, passwd, etc.
                                                    elif identifier == 'defaulip':
                                                        # verify IP address via regex
                                                        if defaults.REGEX_IP.match(value) is not None:
                                                            device.defaults.ip = value
                                                        else:
                                                            match value:
                                                                case 'acquired via DHCP':
                                                                    device.defaults.ip_comment = value
                                                    elif identifier == 'defaultlogin':
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
                                                    elif identifier == 'defaultpass':
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
                                                    elif identifier == 'defaultssid':
                                                        ssids = list(map(lambda x: x.strip(), value.split(',')))
                                                        device.defaults.ssids = ssids
                                                    elif identifier == 'defaultssid_regex':
                                                        ssids = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.defaults.ssid_regexes = ssids

                                                    # JTAG
                                                    elif identifier == 'jtag':
                                                        if value.lower() in ['no', 'none,']:
                                                            device.has_jtag = 'no'
                                                            continue

                                                        # TODO: parse JTAG information
                                                        jtag_fields = value.split(',')
                                                        if jtag_fields[0].lower() == 'yes':
                                                            device.has_jtag = 'yes'

                                                    # manufacturer
                                                    elif identifier == 'countrymanuf':
                                                        device.manufacturer.country = defaults.COUNTRY_REWRITE.get(value, value)
                                                    elif identifier == 'manuf':
                                                        if device.manufacturer.name == '':
                                                            device.manufacturer.name = value
                                                    elif identifier == 'manuf_model':
                                                        device.manufacturer.model = value
                                                    elif identifier == 'manuf_rev':
                                                        device.manufacturer.revision = value
                                                    elif identifier == 'is_manuf':
                                                        # if the brand is also is the ODM simply
                                                        # copy the brand. This assumes that the
                                                        # brand is already known (which has been
                                                        # the case in all data seen so far)
                                                        device.manufacturer.name = device.brand

                                                    # cpu
                                                    elif identifier in ['cpu1chip1', 'cpu2chip1']:
                                                        chip_result = parse_chip(value)
                                                        if chip_result is not None:
                                                            device.cpus.append(chip_result)

                                                    # network
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
                                                    elif identifier == 'lan_ports':
                                                        try:
                                                            device.network.lan_ports = int(value)
                                                        except ValueError:
                                                            pass
                                                    elif identifier in ['eth1chip', 'eth2chip', 'eth3chip',
                                                                        'eth4chip', 'eth5chip', 'eth6chip']:
                                                        device.network.chips.append(parse_chip(value))

                                                    # various OUI
                                                    elif identifier in ['ethoui', 'oui', 'rad1oui',
                                                                        'rad2oui', 'rad3oui', 'rad4oui']:
                                                        ouis = parse_oui(value.upper())
                                                        for oui_value in ouis:
                                                            if identifier == 'ethoui':
                                                                device.network.ethernet_oui.append(oui_value)
                                                            elif identifier == 'oui':
                                                                device.network.wireless_oui.append(oui_value)
                                                            elif identifier in['rad1oui', 'rad2oui', 'rad3oui', 'rad4oui']:
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

                                                    # additional chip
                                                    elif identifier in ['addchip']:
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
                                                        device.radios[radio_num - 1].model = value
                                                    elif identifier in ['rad1modif', 'rad2modif', 'rad3modif', 'rad4modif']:
                                                        # TODO: filter entries with <!--
                                                        radio_num = int(identifier[3:4])
                                                        device.radios[radio_num - 1].interface = value

                                                    # regulatory
                                                    elif identifier == 'fccapprovdate':
                                                        try:
                                                            device.regulatory.fcc_approved_date = parse_date(value)
                                                        except ValueError:
                                                            continue
                                                    elif identifier == 'fcc_id':
                                                        # some devices apparently can have more than one FCC id.
                                                        fcc_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.regulatory.fcc_ids = fcc_values
                                                    elif identifier == 'icid':
                                                        # some devices apparently can have more than one IC id.
                                                        icid_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.regulatory.industry_canada_ids = icid_values
                                                    elif identifier == 'us_id':
                                                        usid_values = list(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                        device.regulatory.us_ids = usid_values

                                                    # serial port. TODO: share with JTAG processing.
                                                    elif identifier == 'serial':
                                                        if value == 'no':
                                                            device.has_serial_port = 'no'
                                                            continue
                                                        # TODO: parse serial information
                                                        serial_fields = value.split(',')
                                                        if serial_fields[0].lower() == 'yes':
                                                            device.has_serial = 'yes'

                                                        # parse every single field. As there doesn't seem to
                                                        # be a fixed order to store information the only way
                                                        # is to process every single field.
                                                        serial_fields_to_process = []
                                                        for serial_field in serial_fields:
                                                            if serial_field.strip() == '':
                                                                # skip empty fields
                                                                continue
                                                            if serial_field.strip().lower() == 'yes':
                                                                continue
                                                            if serial_field.strip().lower() == 'internal':
                                                                continue
                                                            if ';' in serial_field.strip():
                                                                # fields have been concatenated with ; and
                                                                # should first be split
                                                                fs = serial_field.split(';')
                                                                for ff in fs:
                                                                    if ff.strip().strip() == '':
                                                                        # skip empty fields
                                                                        continue
                                                                    if ff.strip().lower() == 'yes':
                                                                        continue
                                                                    if ff.strip().lower() == 'internal':
                                                                        continue
                                                                    serial_fields_to_process.append(ff.strip())
                                                            else:
                                                                serial_fields_to_process.append(serial_field.strip())

                                                        for serial_field in serial_fields_to_process:
                                                            # try to find where the connector can be found
                                                            # (typically which solder pads)
                                                            regex_result = defaults.REGEX_SERIAL_CONNECTOR.match(serial_field.upper())
                                                            if regex_result is not None:
                                                                device.serial.connector = regex_result.groups()[0]
                                                                continue

                                                            # baud rates
                                                            baud_rate = None
                                                            for br in defaults.BAUD_RATES:
                                                                if str(br) in serial_field:
                                                                    baud_rate = br
                                                                    device.serial.baud_rate = baud_rate
                                                                    break

                                                            if baud_rate is not None:
                                                                # verified to be a baud rate
                                                                continue

                                                            # populated or not?
                                                            if 'populated' in serial_field:
                                                                if serial_field == 'unpopulated':
                                                                    device.serial.populated = 'no'
                                                                elif serial_field == 'populated':
                                                                    device.serial.populated = 'yes'
                                                                continue

                                                            # voltage
                                                            if serial_field.upper() in '3.3V TTL':
                                                                device.serial.voltage = 3.3
                                                                continue

                                                            # pin header
                                                            regex_result = defaults.REGEX_SERIAL_PIN_HEADER.match(serial_field)
                                                            if regex_result is not None:
                                                                device.serial.number_of_pins = int(regex_result.groups()[0])
                                                                continue

                                                            # console via RJ45?
                                                            regex_result = defaults.REGEX_SERIAL_RJ45.match(serial_field)
                                                            if regex_result is not None:
                                                                continue

                                                    # software information
                                                    elif identifier in ['stockos', 'stock_os']:
                                                        if device.software.os != '':
                                                            # TODO: parse stock OS information
                                                            device.software.os = value
                                                    elif identifier in ['stockbootloader', 'stock_bootloader']:
                                                        bootloader_split = value.split(';')

                                                        # first entry is the manufacturer. There might be cruft here.
                                                        if '<!--' in bootloader_split[0]:
                                                            # there are a few entries in the database where the data is
                                                            # actually in the comment. Sigh.
                                                            bootloader_manufacturer = bootloader_split[0].split('<')[0].strip()
                                                            device.software.bootloader.manufacturer = bootloader_manufacturer
                                                        else:
                                                            device.software.bootloader.manufacturer = bootloader_split[0]

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
                                                    elif identifier == 'stock_os_sdk':
                                                        # overwrite SDK if empty
                                                        if device.software.sdk == '':
                                                            device.software.sdk = value

                                                    # third party firmware
                                                    elif identifier in ['ddwrtsupport', 'gargoylesupport',
                                                                        'openwrtsupport', 'tomatosupport']:
                                                        continue
                                                    elif identifier == 'tpfirmware':
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
                                                        # parse the support page value
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
                                                        device.web.support_page.append(value)
                                                    elif identifier == 'wikidevi':
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
                                    else:
                                        pass
                                elif f.name.strip() in ['SCollapse', 'SCollapse2']:
                                    # alternative place for boot log, GPL info, /proc, etc.
                                    is_processed = False
                                    wiki_section_header = f.params[0].strip()
                                    for b in ['boot log', 'Boot log', 'stock boot messages']:
                                        if wiki_section_header.startswith(b):
                                            is_processed = True

                                            # parse and store the boot log.
                                            # TODO: further mine the boot log
                                            parse_result = parse_log(f.params[1].value)
                                            break
                                    if is_processed:
                                        continue
                                    if wiki_section_header.startswith('GPL info'):
                                        # there actually does not seem to be anything related
                                        # to GP source code releases in this element, but
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
                                        parse_result = parse_ls(f.params[1].value)
                                    elif wiki_section_header.startswith('ps'):
                                        # the output of ps can contain the names
                                        # of programs and executables
                                        if 'PID  Uid' in f.params[1].value:
                                            parse_result = parse_ps(f.params[1].value)
                                    elif wiki_section_header.startswith('Serial console output'):
                                        pass
                                    elif wiki_section_header.lower().startswith('serial info'):
                                        # some of the entries found in the data seem to be
                                        # serial console output, instead of serial port
                                        # information.
                                        pass
                                    else:
                                        pass
                                elif f.name == 'WiFiCert':
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
                                                device.power_supply.style = value
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

                                elif wiki_type == 'WikiDevi':
                                    # while TechInfoDepot stores everything in an
                                    # element called "Infobox", WikiDevi stores it
                                    # in several different elements.
                                    if f.name in ['Wireless embedded system\n', 'Wired embedded system\n']:
                                        pass
                                    elif f.name == 'TagLine':
                                        for param in f.params:
                                            device.taglines.append(str(param.value))
                                    elif f.name == 'ProductPage':
                                        # parse the product page value
                                        for param in f.params:
                                            value = str(param)
                                            if not '://' in value:
                                                continue
                                            if not value.startswith('http'):
                                                continue
                                            try:
                                                # TODO: fix this check
                                                urllib.parse.urlparse(value)
                                            except ValueError:
                                                continue
                                            device.web.product_page.append(value)
                            elif isinstance(f, mwparserfromhell.nodes.text.Text):
                                pass
                            elif isinstance(f, mwparserfromhell.nodes.tag.Tag):
                                pass
                            else:
                                pass

                        # Write to a Git repository to keep some history
                        # use the title as part of the file name as it is unique
                        model_name = f"{title}.json"
                        model_name = model_name.replace('/', '-')

                        new_file = True

                        json_data = json.dumps(json.loads(device.to_json()), sort_keys=True)

                        # first check if the file has changed if it already exists.
                        # If not, then don't add the file. Git has some intelligence
                        # built-in which prevents unchanged files to be committed again,
                        # which Dulwich doesn't seem to implement at the moment.
                        if (wiki_device_directory / model_name).exists():
                            new_file = False
                            with open(wiki_device_directory / model_name, 'r') as json_file:
                                existing_json = json.dumps(json.load(json_file))
                                if existing_json == json_data:
                                    continue

                        # write to a file in the correct Git directory
                        with open(wiki_device_directory / model_name, 'w') as json_file:
                            json_data = json.dumps(json.loads(device.to_json()), sort_keys=True, indent=4)
                            json_file.write(json_data)

                        if not no_git:
                            # add the file and commit
                            dulwich.porcelain.add(repo, wiki_device_directory / model_name)
                            if new_file:
                                dulwich.porcelain.commit(repo, f"Add {model_name}", committer=AUTHOR, author=AUTHOR)
                            else:
                                dulwich.porcelain.commit(repo, f"Update {model_name}", committer=AUTHOR, author=AUTHOR)

                        # write extra data (extracted from free text) to a separate file
                        model_name = f"{title}.data.json"

                        model_name = model_name.replace('/', '-')
                        #output_file = wiki_device_directory / model_name
                        #with output_file.open('w') as out:
                        #    out.write(json.dumps(json.loads(device.to_json()), indent=4))
                        #    out.write('\n')


if __name__ == "__main__":
    main()
