#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import shlex

from textual.validation import ValidationResult, Validator


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
