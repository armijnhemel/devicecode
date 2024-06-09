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
    extra_info: str = ''

@dataclass_json
@dataclass
class Commercial:
    '''Various commercial information, such as price, barcode
       information for web shops (NewEgg, Amazon, etc.)'''
    amazon_asin: list[Amazon_ASIN] = field(default_factory=list)
    availability: str = ''
    deal_extreme: str = ''
    ean: str = ''
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
class Device:
    '''Top level class holding device information'''
    additional_chips: list[Chip] = field(default_factory=list)
    brand: str = ''
    captions: list[str] = field(default_factory=list)
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
    network: Network = field(default_factory=Network)
    model: str = ''
    part_number: str = ''
    power: Power = field(default_factory=Power)
    power_supply: PowerSupply = field(default_factory=PowerSupply)
    radios: list[Radio] = field(default_factory=list)
    ram: list[Chip] = field(default_factory=list)
    regulatory: Regulatory = field(default_factory=Regulatory)
    revision: str = ''
    serial: Serial = field(default_factory=Serial)
    serial_number: str = ''
    series: str = ''
    software: Software = field(default_factory=Software)
    submodel: str = ''
    subrevision: str = ''
    web: Web = field(default_factory=Web)

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


@click.command(short_help='Process TechInfoDepot XML dump')
@click.option('--input', '-i', 'input_file', required=True,
              help='Wiki top level dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--output', '-o', 'output_directory', required=True, help='JSON output directory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', required=True,
              type=click.Choice(['TechInfoDepot', 'WikiDevi'], case_sensitive=False))
@click.option('--debug', is_flag=True, help='enable debug logging')
def main(input_file, output_directory, wiki_type, debug):
    # load XML
    with open(input_file) as wiki_dump:
        wiki_info = defusedxml.minidom.parse(wiki_dump)

    # first some checks to see if the directory for the wiki type already
    # exists and create it if it doesn't exist.
    if not output_directory.is_dir():
        print("%s is not a directory, exiting." % output_directory)
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
                                                identifier = param_elems[0].split('=', maxsplit=1)[0].strip()

                                                if identifier in defaults.KNOWN_ASIN_IDENTIFIERS:
                                                    num_asins = max(num_asins, defaults.KNOWN_ASIN_IDENTIFIERS.index(identifier) + 1)
                                                elif identifier in defaults.KNOWN_RADIO_IDENTIFIERS:
                                                    num_radios = max(num_radios, int(identifier[3:4]))

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
                                                                      'image1_size', 'image2_size']:
                                                        continue

                                                    # then process all 300+ identifiers. Note: most of
                                                    # these identifiers only have a single value, so it
                                                    # is safe to just override the default value defined in
                                                    # the dataclass. The exception here is 'addchip'.
                                                    if identifier == 'brand':
                                                        device.brand = defaults.BRAND_REWRITE.get(value, value)
                                                    elif identifier == 'model':
                                                        device.model = value
                                                    elif identifier == 'model_part_num':
                                                        device.part_number = value
                                                    elif identifier == 'revision':
                                                        device.revision = value
                                                    elif identifier == 'series':
                                                        device.series = value
                                                    elif identifier == 'sernum':
                                                        device.serial_number = value
                                                    elif identifier == 'subrevision':
                                                        if value != '(??)':
                                                            device.subrevision = value
                                                    elif identifier == 'submodel':
                                                        device.submodel = value
                                                    elif identifier == 'type':
                                                        device_types = list(map(lambda x: x.strip(), value.split(',')))
                                                        device.device_types= device_types
                                                    elif identifier == 'flags':
                                                        device.flags = sorted(filter(lambda x: x!='', map(lambda x: x.strip(), value.split(','))))
                                                    elif identifier in ['caption', 'caption2']:
                                                        device.captions.append(value.strip())
                                                    elif identifier in ['image1', 'image2']:
                                                        device.images.append(value.strip())
                                                    elif identifier == 'exp_if_types':
                                                        if value.strip() == 'none':
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
                                                    elif identifier == 'newegg':
                                                        eggs = value.split(',')
                                                        for egg in eggs:
                                                            device.commercial.newegg.append(egg.strip())
                                                    elif identifier in defaults.KNOWN_ASIN_IDENTIFIERS:
                                                        # verify ASIN address via regex
                                                        if defaults.REGEX_ASIN.match(value) is not None:
                                                            pass

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
                                                        device.manufacturer.name = value
                                                    elif identifier == 'manuf_model':
                                                        device.manufacturer.model = value
                                                    elif identifier == 'manuf_rev':
                                                        device.manufacturer.revision = value
                                                    elif identifier == 'is_manuf':
                                                        pass

                                                    # cpu
                                                    elif identifier in ['cpu1chip1', 'cpu2chip1']:
                                                        chip_result = parse_chip(value.strip())
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
                                                    elif identifier in ['ethoui', 'oui', 'rad1oui',
                                                                        'rad2oui', 'rad3oui', 'rad4oui']:
                                                        ethoui_values = value.upper().split(',')
                                                        for ethoui in ethoui_values:
                                                            for oui_value in ethoui.split(';'):
                                                                if oui_value.strip() == '':
                                                                    continue
                                                                if defaults.REGEX_OUI.match(oui_value.strip()) is not None:
                                                                    if identifier == 'ethoui':
                                                                        device.network.ethernet_oui.append(oui_value.strip())
                                                                    elif identifier == 'oui':
                                                                        device.network.wireless_oui.append(oui_value.strip())
                                                                    elif identifier in['rad1oui', 'rad2oui', 'rad3oui', 'rad4oui']:
                                                                        radio_num = int(identifier[3:4])
                                                                        device.radios[radio_num - 1].oui.append(oui_value.strip())
                                                    elif identifier in ['eth1chip', 'eth2chip', 'eth3chip',
                                                                        'eth4chip', 'eth5chip', 'eth6chip']:
                                                        parse_chip(value.strip())

                                                    # flash
                                                    elif identifier in ['fla1chip', 'fla2chip', 'fla3chip']:
                                                        parse_chip(value.strip())

                                                    # switch
                                                    elif identifier in ['sw1chip', 'sw2chip', 'sw3chip']:
                                                        parse_chip(value.strip())

                                                    # RAM
                                                    elif identifier in ['ram1chip', 'ram2chip', 'ram3chip']:
                                                        parse_chip(value.strip())

                                                    # additional chip
                                                    #elif identifier in ['addchip']:
                                                        # here the first entry *should* be a description
                                                        #parse_chip(value.strip())

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
                                                        parse_chip(value.strip())

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
                                                        for serial_field in serial_fields:
                                                            if serial_field.strip() == '':
                                                                # skip empty fields
                                                                continue
                                                            if serial_field.lower() == 'yes':
                                                                continue
                                                            if serial_field.lower() == 'internal':
                                                                continue
                                                            if ';' in serial_field.strip():
                                                                # fields have been concatenated with ; and
                                                                # should be added and processed separately
                                                                pass

                                                            # try to find where the connector can be found
                                                            # (typically which solder pads)
                                                            regex_result = defaults.REGEX_SERIAL_CONNECTOR.match(serial_field.strip().upper())
                                                            if regex_result is not None:
                                                                device.serial.connector = regex_result.groups()[0]
                                                                continue

                                                            # baud rates
                                                            baud_rate = None
                                                            for br in defaults.BAUD_RATES:
                                                                if str(br) in serial_field.strip():
                                                                    baud_rate = br
                                                                    device.serial.baud_rate = baud_rate
                                                                    break

                                                            if baud_rate is not None:
                                                                continue

                                                            # populated or not?
                                                            if 'populated' in serial_field:
                                                                if serial_field.strip() == 'unpopulated':
                                                                    device.serial.populated = 'no'
                                                                elif serial_field.strip() == 'populated':
                                                                    device.serial.populated = 'yes'
                                                                continue

                                                            # voltage
                                                            if serial_field.strip().upper() in '3.3V TTL':
                                                                device.serial.voltage = 3.3
                                                                continue

                                                            # pin header
                                                            regex_result = defaults.REGEX_SERIAL_PIN_HEADER.match(serial_field.strip())
                                                            if regex_result is not None:
                                                                continue

                                                            # console via RJ45?
                                                            regex_result = defaults.REGEX_SERIAL_RJ45.match(serial_field.strip())
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
                                                    #elif identifier == 'wikipedia':
                                                    #    device.web.wikipedia = value

                                                    else:
                                                        if debug:
                                                            # print values, but only if they aren't already
                                                            # skipped or processed. This is useful for discovering
                                                            # default values and variants.
                                                            # TODO: also print values that weren't correctly processed
                                                            print(identifier, value, file=sys.stderr)
                                    elif f.name == 'SCollapse':
                                        # alternative place for boot log, GPL info, /proc, etc.
                                        is_boot = False
                                        for b in ['boot log', 'Boot log', 'stock boot messages']:
                                            if f.params[0].startswith(b):
                                                is_boot = True

                                                # parse and store the boot log.
                                                # TODO: further mine the boot log
                                                #print(type(f.params[1].value))
                                                break
                                        if is_boot:
                                            continue
                                        #print(f.params[0], len(f.params[1:]))
                                    elif f.name == 'hasPowerSupply\n':
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

                                    elif f.name == 'WiFiCert':
                                        if len(f.params) >= 2:
                                            wifi_cert, wifi_cert_date = f.params[:2]
                                            device.regulatory.wifi_certified = str(wifi_cert.value)
                                            wifi_cert_date = str(wifi_cert_date.value)
                                            device.regulatory.wifi_certified_date = parse_date(wifi_cert_date)
                                        pass
                                    else:
                                        pass
                                elif isinstance(f, mwparserfromhell.nodes.text.Text):
                                    pass
                                elif isinstance(f, mwparserfromhell.nodes.tag.Tag):
                                    pass
                                else:
                                    pass


                        # TODO: write to a Git repository to keep some history
                        # use the title as part of the file name as it is unique
                        model_name = f"{title}.json"

                        model_name = model_name.replace('/', '-')
                        output_file = wiki_device_directory / model_name
                        with output_file.open('w') as out:
                            out.write(json.dumps(json.loads(device.to_json()), indent=4))
                            out.write('\n')


if __name__ == "__main__":
    main()
