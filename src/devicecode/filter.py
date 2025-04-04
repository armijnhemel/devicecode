#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import shlex

from textual.validation import ValidationResult, Validator
from textual.widgets import Input

def process_filter(event: Input.Submitted):
    '''Process filter statements: tokenize and add to right data structures'''
    result = {}

    names = ['bootloaders', 'brands', 'chips', 'chip_types', 'chip_vendors', 'connectors', 'cves',
          'cveids', 'device_types', 'fccs', 'files', 'flags', 'ignore_brands', 'ignore_odms',
          'ignore_origins', 'ips', 'jtags', 'odms', 'operating_systems', 'origins', 'packages',
          'partitions', 'passwords', 'programs', 'rootfs', 'sdks', 'serials', 'serial_baud_rates']

    for i in  names:
        result[i] = set()

    # Then add some special cases.
    result['years'] = []
    result['is_filtered'] = False
    result['overlay'] = True

    if event.validation_result is not None:
        # Input was already syntactically validated before
        # being sent here so it can be processed without any
        # extra checks.

        tokens = shlex.split(event.value.lower())

        for t in tokens:
            # First split the tokens in names and values
            # and optional parameters

            params = {}

            name_params, value = t.split('=', maxsplit=1)
            if '?' in name_params:
                name, args = name_params.split('?', maxsplit=1)
            else:
                name = name_params

            # Process each known name
            match name:
                case 'bootloader':
                    result['bootloaders'].add(value)
                case 'brand':
                    result['brands'].add(value)
                case 'chip':
                    result['chips'].add(value)
                case 'chip_type':
                    result['chip_types'].add(value)
                case 'chip_vendor':
                    result['chip_vendors'].add(value)
                case 'connector':
                    result['connectors'].add(value)
                case 'cve':
                    result['cves'].add(value)
                case 'cveid':
                    result['cveids'].add(value)
                case 'fccid':
                    result['fccs'].add(value)
                case 'flag':
                    result['flags'].add(value)
                case 'ignore_brand':
                    result['ignore_brands'].add(value)
                case 'ignore_odm':
                    result['ignore_odms'].add(value)
                case 'ignore_origin':
                    result['ignore_origins'].add(value)
                case 'file':
                    result['files'].add(value)
                case 'ip':
                    result['ips'].add(value)
                case 'odm':
                    result['odms'].add(value)
                case 'origin':
                    result['origins'].add(value)
                case 'os':
                    result['operating_systems'].add(value)
                case 'package':
                    result['packages'].add(value)
                case 'partition':
                    result['partitions'].add(value)
                case 'password':
                    result['passwords'].add(value)
                case 'program':
                    result['programs'].add(value)
                case 'rootfs':
                    result['rootfs'].add(value)
                case 'sdk':
                    result['sdks'].add(value)
                case 'serial':
                    result['serials'].add(value)
                case 'baud':
                    result['serial_baud_rates'].add(int(value))
                case 'type':
                    result['device_types'].add(value)
                case 'jtag':
                    result['jtags'].add(value)
                case 'year':
                    input_years = sorted(value.split(':', maxsplit=1))
                    if len(input_years) > 1:
                        result['years'] += list(range(int(input_years[0]), int(input_years[1]) + 1))
                    else:
                        result['years'] += [int(x) for x in input_years]

            match name:
                case 'overlays':
                    # special filtering flag
                    if value == 'off':
                        result['overlay'] = False
                case _:
                    result['is_filtered'] = True
    return result


class FilterValidator(Validator):
    '''Syntax validator for the filtering language.'''

    def __init__(self, **kwargs):
        # Known values: only these will be regarded as valid.
        self.baud_rates = kwargs.get('baud_rates', set())
        self.bootloaders = kwargs.get('bootloaders', set())
        self.brands = kwargs.get('brands', set())
        self.cveids = kwargs.get('cveids', set())
        self.odms = kwargs.get('odms', set())
        self.chips = kwargs.get('chips', set())
        self.chip_types = kwargs.get('chip_types', set())
        self.chip_vendors = kwargs.get('chip_vendors', set())
        self.connectors = kwargs.get('connectors', set())
        self.device_types = kwargs.get('types', set())
        self.fcc_ids = kwargs.get('fcc_ids', set())
        self.files = kwargs.get('files', set())
        self.ips = kwargs.get('ips', set())
        self.packages = kwargs.get('packages', set())
        self.partitions = kwargs.get('partitions', set())
        self.passwords = kwargs.get('passwords', set())
        self.rootfs = kwargs.get('rootfs', set())
        self.sdks = kwargs.get('sdks', set())
        self.token_names_params = kwargs.get('token_names', [])
        self.token_names = list(map(lambda x: x['name'], self.token_names_params))

    def validate(self, value: str) -> ValidationResult:
        try:
            # split the value into tokens
            tokens = shlex.split(value.lower())
            if not tokens:
                return self.failure("Empty string")

            # verify each token
            for t in tokens:
                if '=' not in t:
                    return self.failure("Invalid name")

                # first verify if the token is well formed
                # and if it has a valid name
                name_params, token_value = t.split('=', maxsplit=1)
                if '?' in name_params:
                    name, args = name_params.split('?', maxsplit=1)
                else:
                    name = name_params
                if name not in self.token_names:
                    return self.failure("Invalid name")

                # then check each individual token
                if name == 'bootloader':
                    if token_value not in self.bootloaders:
                        return self.failure("Invalid bootloader")
                elif name == 'brand':
                    if token_value not in self.brands:
                        return self.failure("Invalid brand")
                elif name == 'chip':
                    if token_value not in self.chips:
                        return self.failure("Invalid chip")
                elif name == 'chip_type':
                    if token_value not in self.chip_types:
                        return self.failure("Invalid chip type")
                elif name == 'chip_vendor':
                    if token_value not in self.chip_vendors:
                        return self.failure("Invalid chip vendor")
                elif name == 'connector':
                    if token_value not in self.connectors:
                        return self.failure("Invalid connector")
                elif name == 'baud':
                    try:
                        int(token_value)
                    except:
                        return self.failure("Invalid baud rate")
                    if int(token_value) not in self.baud_rates:
                        return self.failure("Invalid baud rate")
                elif name == 'cve':
                    if token_value not in ['no', 'yes']:
                        return self.failure("Invalid CVE information")
                elif name == 'cveid':
                    if token_value not in self.cveids:
                        return self.failure("Invalid CVE id")
                elif name == 'ignore_brand':
                    if token_value not in self.brands:
                        return self.failure("Invalid brand")
                elif name == 'ignore_odm':
                    if token_value not in self.odms:
                        return self.failure("Invalid ODM")
                elif name == 'fccid':
                    if token_value not in self.fcc_ids:
                        return self.failure("Invalid FCC")
                elif name == 'file':
                    if token_value not in self.files:
                        return self.failure("Invalid file")
                elif name == 'ip':
                    if token_value not in self.ips:
                        return self.failure("Invalid IP")
                elif name == 'odm':
                    if token_value not in self.odms:
                        return self.failure("Invalid ODM")
                elif name == 'password':
                    if token_value not in self.passwords:
                        return self.failure("Invalid password")
                elif name == 'package':
                    if token_value not in self.packages:
                        return self.failure("Invalid package")
                elif name == 'partition':
                    if token_value not in self.partitions:
                        return self.failure("Invalid partition")
                elif name == 'rootfs':
                    if token_value not in self.rootfs:
                        return self.failure("Invalid rootfs")
                elif name == 'sdk':
                    if token_value not in self.sdks:
                        return self.failure("Invalid SDK")
                #elif name == 'type':
                    #if token_value not in self.device_types:
                        #return self.failure("Invalid type")
                elif name == 'fcc':
                    if token_value not in ['no', 'invalid', 'yes']:
                        return self.failure("Invalid FCC information")
                elif name in ['jtag', 'serial']:
                    if token_value not in ['no', 'unknown', 'yes']:
                        return self.failure("Invalid JTAG/serial port information")
                elif name in ['origin', 'ignore_origin']:
                    if token_value not in ['techinfodepot', 'wikidevi', 'openwrt']:
                        return self.failure("Invalid origin")
                elif name == 'year':
                    years = token_value.split(':', maxsplit=1)
                    for year in years:
                        try:
                            valid_year=int(year)
                        except:
                            return self.failure("Invalid year")
                        if valid_year < 1990 or valid_year > 2040:
                            return self.failure("Invalid year")
                elif name == 'overlays':
                    if token_value not in ['off']:
                        return self.failure("Invalid overlay flag")
            return self.success()
        except ValueError:
            return self.failure('Incomplete')
