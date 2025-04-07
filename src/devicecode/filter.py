#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import shlex

from textual.validation import ValidationResult, Validator
from textual.widgets import Input

def process_filter(event: Input.Submitted):
    '''Process filter statements: tokenize and add to right data structures'''
    result = {}

    # A mapping of token names to names used in the result dict.
    name_to_results = {'bootloader': 'bootloaders', 'brand': 'brands', 'chip': 'chips',
                       'chip_type': 'chip_types', 'chip_vendor': 'chip_vendors',
                       'connector': 'connectors', 'cve': 'cves', 'cveid': 'cveids',
                       'fccid': 'fccs', 'file': 'files', 'flag': 'flags',
                       'ignore_brand': 'ignore_brands', 'ignore_odm': 'ignore_odms',
                       'ignore_origin': 'ignore_origins', 'ip': 'ips', 'jtag': 'jtags',
                       'odm': 'odms', 'os': 'operating_systems', 'origin': 'origins',
                       'package': 'packages', 'partition': 'partitions', 'password': 'passwords',
                       'program': 'programs', 'rootfs': 'rootfs', 'sdk': 'sdks',
                       'serial': 'serials', 'baud': 'serial_baud_rates', 'type': 'device_types'}

    for name, result_name in name_to_results.items():
        result[result_name] = []

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
                split_args = args.split(';')
                for split_arg in split_args:
                    if ':' in split_arg:
                        param_name, param_value = split_arg.split(':', maxsplit=1)
                        if param_name and param_value:
                            params[param_name] = param_value
            else:
                name = name_params

            # Process each known name. First the generic case
            # that's all the same.
            if name in name_to_results:
                result[name_to_results[name]].append((value, params))
                result['is_filtered'] = True

            # Then the special cases.
            match name:
                case 'year':
                    input_years = sorted(value.split(':', maxsplit=1))
                    if len(input_years) > 1:
                        result['years'] += list(range(int(input_years[0]), int(input_years[1]) + 1))
                    else:
                        #result['years'] += [(int(x), params) for x in input_years]
                        result['years'] += [int(x) for x in input_years]
                    result['is_filtered'] = True
                case 'overlays':
                    # special filtering flag
                    if value == 'off':
                        result['overlay'] = False
    return result


class FilterValidator(Validator):
    '''Syntax validator for the filtering language.'''

    # A mapping for filter error messages. These are most likely
    # never seen by a user but could come in handy for debugging.
    NAME_TO_ERROR = {'bootloader': 'Invalid bootloader',
                     'brand': 'Invalid brand', 'ignore_brand': 'Invalid brand',
                     'chip': 'Invalid chip',
                     'chip_type': 'Invalid chip type',
                     'chip_vendor': 'Invalid chip vendor',
                     'connector': 'Invalid connector',
                     'baud': 'Invalid baud rate',
                     'cve': 'Invalid CVE information',
                     'cveid': 'Invalid CVE id',
                     'fcc': 'Invalid FCC information',
                     'fccid': 'Invalid FCC',
                     'file': 'Invalid file',
                     'ip': 'Invalid IP',
                     'odm': 'Invalid ODM',
                     'ignore_odm': 'Invalid ODM',
                     'origin': 'Invalid origin',
                     'ignore_origin': 'Invalid origin',
                     'overlays': 'Invalid overlay flag',
                     'package': 'Invalid package',
                     'partition': 'Invalid partition',
                     'password': 'Invalid password',
                     'rootfs': 'Invalid rootfs',
                     'sdk': 'Invalid SDK',
                     'type': 'Invalid device type',
                     'jtag': 'Invalid JTAG/serial port information',
                     'serial': 'Invalid JTAG/serial port information',
                     'year': 'Invalid year',
                    }

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
            # Split the value into individual tokens
            tokens = shlex.split(value.lower())
            if not tokens:
                return self.failure("Empty string")

            # Verify each token
            for t in tokens:
                if '=' not in t:
                    return self.failure("Invalid name")

                # Verify if the token is well formed
                # and if it has a valid name.
                name_params, token_value = t.split('=', maxsplit=1)
                if '?' in name_params:
                    name, args = name_params.split('?', maxsplit=1)
                else:
                    name = name_params
                if name not in self.token_names:
                    return self.failure("Invalid name")

                is_error = False

                # Then check each individual token.
                match name:
                    case 'bootloader':
                        if token_value not in self.bootloaders:
                            is_error = True
                    case 'brand' | 'ignore_brand':
                        if token_value not in self.brands:
                            is_error = True
                    case 'chip':
                        if token_value not in self.chips:
                            is_error = True
                    case 'chip_type':
                        if token_value not in self.chip_types:
                            is_error = True
                    case 'chip_vendor':
                        if token_value not in self.chip_vendors:
                            is_error = True
                    case 'connector':
                        if token_value not in self.connectors:
                            is_error = True
                    case 'baud':
                        try:
                            if int(token_value) not in self.baud_rates:
                                is_error = True
                        except:
                            is_error = True
                    case 'cve':
                        if token_value not in ['no', 'yes']:
                            is_error = True
                    case 'cveid':
                        if token_value not in self.cveids:
                            is_error = True
                    case 'fccid':
                        if token_value not in self.fcc_ids:
                            is_error = True
                    case 'file':
                        if token_value not in self.files:
                            is_error = True
                    case 'ip':
                        if token_value not in self.ips:
                            is_error = True
                    case 'odm' | 'ignore_odm':
                        if token_value not in self.odms:
                            is_error = True
                    case 'password':
                        if token_value not in self.passwords:
                            is_error = True
                    case 'package':
                        if token_value not in self.packages:
                            is_error = True
                    case 'partition':
                        if token_value not in self.partitions:
                            is_error = True
                    case 'rootfs':
                        if token_value not in self.rootfs:
                            is_error = True
                    case 'sdk':
                        if token_value not in self.sdks:
                            is_error = True
                    #case 'type':
                        #if token_value not in self.device_types:
                            #is_error = True
                    case 'fcc':
                        if token_value not in ['no', 'invalid', 'yes']:
                            is_error = True
                    case 'jtag' | 'serial':
                        if token_value not in ['no', 'unknown', 'yes']:
                            is_error = True
                    case 'origin' | 'ignore_origin':
                        if token_value not in ['techinfodepot', 'wikidevi', 'openwrt']:
                            is_error = True
                    case 'year':
                        years = token_value.split(':', maxsplit=1)
                        for year in years:
                            try:
                                valid_year=int(year)
                                if valid_year < 1990 or valid_year > 2040:
                                    is_error = True
                            except:
                                is_error = True
                    case 'overlays':
                        if token_value not in ['off']:
                            is_error = True

                if is_error:
                    return self.failure(self.NAME_TO_ERROR[name])
            return self.success()
        except ValueError:
            return self.failure('Incomplete')
