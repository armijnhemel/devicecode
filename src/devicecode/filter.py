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
                       'connector': 'connectors', 'cpe': 'cpes', 'cve': 'cves', 'cveid': 'cveids',
                       'fcc': 'fccs', 'fccid': 'fccids', 'file': 'files', 'flag': 'flags',
                       'ignore_brand': 'ignore_brands', 'ignore_odm': 'ignore_odms',
                       'ignore_origin': 'ignore_origins', 'ip': 'ips', 'jtag': 'jtags',
                       'odm': 'odms', 'os': 'operating_systems', 'origin': 'origins',
                       'package': 'packages', 'partition': 'partitions', 'password': 'passwords',
                       'pcbid': 'pcbids', 'program': 'programs', 'rootfs': 'rootfs', 'sdk': 'sdks',
                       'serial': 'serials', 'baud': 'serial_baud_rates', 'type': 'device_types'}

    for name, result_name in name_to_results.items():
        result[result_name] = []

    # Then add some special cases.
    result['years'] = []
    result['is_filtered'] = False
    result['overlay'] = True

    if event.validation_result is not None:
        # Input was already validated before being sent here
        # so it can be processed without any extra checks.

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
    '''Validator for the filtering language (syntax and values).'''

    def __init__(self, data, **kwargs):
        # Known values: only these will be regarded as valid.
        self.baud_rates = data.get('baud_rates', set())
        self.bootloaders = data.get('bootloaders', set())
        self.brands = data.get('brands', set())
        self.cveids = data.get('cveids', set())
        self.odms = data.get('odms', set())
        self.chips = data.get('chips', set())
        self.chip_types = data.get('chip_types', set())
        self.chip_vendors = data.get('chip_vendors', set())
        self.connectors = data.get('connectors', set())
        self.device_types = data.get('types', set())
        self.fcc_ids = data.get('fcc_ids', set())
        self.files = data.get('files', set())
        self.ips = data.get('ips', set())
        self.packages = data.get('packages', set())
        self.partitions = data.get('partitions', set())
        self.passwords = data.get('passwords', set())
        self.pcbids = data.get('pcbids', set())
        self.rootfs = data.get('rootfs', set())
        self.sdks = data.get('sdks', set())
        self.token_names_params = kwargs.get('token_names', [])
        self.token_names = [x['name'] for x in self.token_names_params]

        # A mapping for filter error messages. These are not displayed
        # in the TUI, but they are used in the CLI.
        self.name_to_error = {}
        for i in self.token_names_params:
            self.name_to_error[i['name']] = i['error']

        # A mapping for names to parameters. This can be used to verify
        # if parameters are actually correct. Unsure if this is a useful
        # feature or not, so disable it for now.
        self.name_to_params = {}
        for i in self.token_names_params:
            if 'params' in i:
                self.name_to_params[i['name']] = i['params']

        self.verify_params = False

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
                params = {}
                name_params, token_value = t.split('=', maxsplit=1)
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
                    case 'cpe':
                        if token_value not in ['no', 'yes']:
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
                    case 'pcbid':
                        if token_value not in self.pcbids:
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

                # Then check the parameters, if enabled.
                if self.verify_params:
                    if name in self.name_to_params:
                        for p in params:
                            if p not in self.name_to_params[name]:
                                is_error = True

                if is_error:
                    return self.failure(self.name_to_error[name])
            return self.success()
        except ValueError:
            return self.failure('Incomplete')
