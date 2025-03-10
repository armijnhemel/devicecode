#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import pathlib
import shlex
import sys
import webbrowser

from typing import Any, Iterable

import click

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.suggester import Suggester
from textual.validation import ValidationResult, Validator
from textual.widgets import Footer, Markdown, Tree, TabbedContent, TabPane, Input, Header, DataTable

import devicecode_defaults as defaults

class SuggestDevices(Suggester):
    '''A custom suggester, based on the SuggestFromList example from Textual'''

    def __init__(
        self, suggestions: Iterable[str], *, case_sensitive: bool = True,
    **kwargs) -> None:
        super().__init__(case_sensitive=case_sensitive)
        self._suggestions = list(map(lambda x: x['name'], suggestions))
        self._for_comparison = (
            self._suggestions
            if self.case_sensitive
            else [suggestion.casefold() for suggestion in self._suggestions]
        )

        # mapping of filter name to kwargs names
        suggestion_names = {'bootloader': 'bootloaders',
                            'brand': 'brands', 'ignore_brand': 'brands',
                            'chip': 'chips', 'chip_type': 'chip_types',
                            'chip_vendor': 'chip_vendors', 'fccid': 'fcc_ids',
                            'file': 'files', 'flag': 'flags', 'odm': 'odms',
                            'ignore_odm': 'odms', 'package': 'packages',
                            'partition': 'partitions', 'password': 'passwords',
                            'program': 'programs', 'rootfs': 'rootfs', 'sdk': 'sdks',
                            'type': 'types'}

        self.suggestion_table = {}
        for i in suggestion_names:
            self.suggestion_table[i] = kwargs.get(suggestion_names[i], [])

        # some values are always hardcoded
        self.suggestion_table['jtag'] = ['no', 'unknown', 'yes']
        self.suggestion_table['serial'] = ['no', 'unknown', 'yes']
        self.suggestion_table['origin'] = ['techinfodepot', 'wikidevi', 'openwrt']
        self.suggestion_table['ignore_origin'] = ['techinfodepot', 'wikidevi', 'openwrt']

    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """

        # first split the value
        check_value = value.rsplit(' ', maxsplit=1)[-1]
        if '=' in check_value:
            name_params, token_value = check_value.split('=', maxsplit=1)
            len_name_params = len(name_params) + 1
            suggestion_offset = len(check_value)-len_name_params
            name = name_params.split('?', maxsplit=1)[0]

            # then check and suggest a value. Don't ask how it works,
            # but it works. When adding a new value, don't forget to
            # correctly compute the lengths, otherwise some characters
            # will appear to have been overwritten.
            if name in self.suggestion_table:
                for idx, chk in enumerate(self.suggestion_table[name]):
                    if chk.startswith(token_value):
                        return value + self.suggestion_table[name][idx][suggestion_offset:]

        for idx, suggestion in enumerate(self._for_comparison):
            if suggestion.startswith(check_value):
                return value + self._suggestions[idx][len(check_value):]
        return None

class FilterValidator(Validator):
    '''Syntax validator for the filtering language.'''

    def __init__(self, **kwargs):
        # Known values: only these will be regarded as valid.
        self.baud_rates = kwargs.get('baud_rates', set())
        self.bootloaders = kwargs.get('bootloaders', set())
        self.brands = kwargs.get('brands', set())
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
                elif name == 'serial':
                    if token_value not in ['no', 'unknown', 'yes']:
                        return self.failure("Invalid serial port information")
                elif name == 'jtag':
                    if token_value not in ['no', 'unknown', 'yes']:
                        return self.failure("Invalid jtag port information")
                elif name == 'origin':
                    if token_value not in ['techinfodepot', 'wikidevi', 'openwrt']:
                        return self.failure("Invalid origin")
                elif name == 'ignore_origin':
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
            return self.success()
        except ValueError:
            return self.failure('Incomplete')

class BrandTree(Tree):

    def build_tree(self, brands_to_devices, is_filtered=False):
        # build the initial brand_tree.
        self.reset("DeviceCode brand results")
        for brand in sorted(brands_to_devices.keys(), key=str.casefold):
            # add each brand as a node. Then add each model as a leaf.
            node = self.root.add(brand, data={'brand': brand}, expand=is_filtered)
            node_leaves = 0

            # recurse into the device and add nodes for devices
            for model in sorted(brands_to_devices[brand], key=lambda x: x['model']):
                if model['labels']:
                    node.add_leaf(f"{model['model']}  {''.join(model['labels'])}", data=model['data'])
                else:
                    node.add_leaf(f"{model['model']}", data=model['data'])
                node_leaves += 1
            node.label = f"{node.label}  ({node_leaves})"


class OdmTree(Tree):

    def build_tree(self, odm_to_devices, is_filtered=False):
        # build the odm_tree.
        self.reset("DeviceCode OEM results")

        # add each manufacturer as a node. Then add each brand as a subtree
        # and each model as a leaf. Optionally filter for brands and prune.
        for odm in sorted(odm_to_devices.keys(), key=str.casefold):
            # create a node with brand subnodes
            node = self.root.add(odm, expand=is_filtered)
            node_leaves = 0
            for brand in sorted(odm_to_devices[odm], key=str.casefold):
                # recurse into the device and add nodes for devices
                brand_node = node.add(brand)
                brand_node_leaves = 0
                for model in sorted(odm_to_devices[odm][brand], key=lambda x: x['model']):
                    # default case
                    if model['labels']:
                        brand_node.add_leaf(f"{model['model']}  {''.join(model['labels'])}", data=model['data'])
                    else:
                        brand_node.add_leaf(f"{model['model']}", data=model['data'])
                    brand_node_leaves += 1
                    node_leaves += 1

                # check if there are any valid leaf nodes.
                # If not, remove the brand node
                if brand_node_leaves == 0:
                    brand_node.remove()
                else:
                    brand_node.label = f"{brand_node.label}  ({brand_node_leaves})"

            # check if there are any valid leaf nodes.
            # If not, remove the ODM node
            if node_leaves == 0:
                node.remove()
            node.label = f"{node.label}  ({node_leaves})"

class DevicecodeUI(App):
    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="Quit"),
    ]

    CSS_PATH = "devicecode_tui.css"

    # a list of tokens for filtering
    # This is a list of dicts.
    TOKEN_NAMES = [{'name': 'baud', 'has_params': False},
                   {'name': 'bootloader', 'has_params': True, 'params': ['version']},
                   {'name': 'brand', 'has_params': False},
                   {'name': 'chip', 'has_params': False},
                   {'name': 'chip_type', 'has_params': False},
                   {'name': 'chip_vendor', 'has_params': False},
                   {'name': 'connector', 'has_params': False},
                   {'name': 'fccid', 'has_params': False},
                   {'name': 'file', 'has_params': False},
                   {'name': 'flag', 'has_params': False},
                   {'name': 'ignore_brand', 'has_params': False},
                   {'name': 'ignore_odm', 'has_params': False},
                   {'name': 'ignore_origin', 'has_params': False},
                   {'name': 'ip', 'has_params': False},
                   {'name': 'jtag', 'has_params': True, 'params': ['populated']},
                   {'name': 'odm', 'has_params': False},
                   {'name': 'origin', 'has_params': False},
                   {'name': 'os', 'has_params': False},
                   {'name': 'package', 'has_params': False},
                   {'name': 'partition', 'has_params': False},
                   {'name': 'password', 'has_params': False},
                   {'name': 'program', 'has_params': False},
                   {'name': 'rootfs', 'has_params': False},
                   {'name': 'sdk', 'has_params': True, 'params': ['version']},
                   {'name': 'serial', 'has_params': True, 'params': ['populated']},
                   {'name': 'type', 'has_params': False},
                   {'name': 'year', 'has_params': False},
                  ]

    def __init__(self, devicecode_dirs, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.devicecode_directories = devicecode_dirs

    def compose_data_sets(self, **kwargs):
        '''Compose the data sets for devices for display, optionally filtered'''

        # Optional filters with data for devices that should
        # be displayed or ignored. If these filters are empty,
        # then the data set will be the full data (unfiltered).
        filter_baud_rates = kwargs.get('serial_baud_rates', [])
        filter_bootloaders = kwargs.get('bootloaders', [])
        filter_brands = kwargs.get('brands', [])
        filter_chips = kwargs.get('chips', [])
        filter_chip_types = kwargs.get('chip_types', [])
        filter_chip_vendors = kwargs.get('chip_vendors', [])
        filter_connectors = kwargs.get('connectors', set())
        filter_device_types = kwargs.get('types', [])
        filter_fccs = kwargs.get('fccs', [])
        filter_files = kwargs.get('files', [])
        filter_flags = kwargs.get('flags', [])
        filter_ignore_brands = kwargs.get('ignore_brands', [])
        filter_ignore_odms = kwargs.get('ignore_odms', [])
        filter_ignore_origins = kwargs.get('ignore_origins', [])
        filter_ips = kwargs.get('ips', [])
        filter_jtags = kwargs.get('jtags', [])
        filter_odms = kwargs.get('odms', [])
        filter_operating_systems = kwargs.get('operating_systems', [])
        filter_origins = kwargs.get('origins', [])
        filter_packages = kwargs.get('packages', [])
        filter_partitions = kwargs.get('partitions', [])
        filter_passwords = kwargs.get('passwords', [])
        filter_programs = kwargs.get('programs', [])
        filter_rootfs = kwargs.get('rootfs', [])
        filter_sdks = kwargs.get('sdks', [])
        filter_serials = kwargs.get('serials', [])
        filter_years = kwargs.get('years', [])

        # mapping of brands to devices
        brands_to_devices = {}

        # mapping of odms to devices
        odm_to_devices = {}

        # known baud rates
        baud_rates = set()

        # known bootloaders
        bootloaders = set()

        # known brands
        brands = set()
        brand_data = []

        # known chips
        chips = set()

        # known chip types
        chip_types = set()

        # known chip vendors
        chip_vendors = set()

        # known serial/JTAG connectors
        connectors = set()

        # known ODMS
        odms = set()

        # known FCC ids
        fcc_ids = set()

        # known files
        files = set()

        # known flags
        flags = set()

        # known default IP addresses
        ips = set()

        # known origins
        origins = set()

        # known packages
        packages = set()

        # known partitions
        partitions = set()

        # known default passwords
        passwords = set()

        # known programs
        programs = set()

        # known rootfs
        rootfs = set()

        # known SDKs
        sdks = set()

        # known device_types
        device_types = set()

        # known years
        years = set()
        year_data = []

        # Extract useful data from each of the devices for quick
        # access when building the trees and the datatables.
        brand_odm = []
        brand_cpu = []
        odm_cpu = []
        odm_connector = []
        chip_vendor_connector = []
        for device in self.devices:
            if 'title' not in device:
                continue
            if device['title'] in self.overlays:
                # apply overlays
                for overlay in self.overlays[device['title']]:
                    if overlay['name'] == 'fcc_id':
                        device['regulatory']['fcc_ids'] = overlay['data']
                    elif overlay['name'] == 'oui':
                        device['network']['ethernet_oui'] = overlay['data']['ethernet_oui']
                        device['network']['wireless_oui'] = overlay['data']['wireless_oui']
                    elif overlay['name'] == 'fcc_extracted_text':
                        device['fcc_data'] = overlay['data']
                    elif overlay['name'] == 'brand':
                        device['brand'] = overlay['data']['brand']

            if 'brand' not in device:
                continue

            brand_name = device['brand']

            # filter brands
            if filter_brands and brand_name.lower() not in filter_brands:
                continue
            if filter_ignore_brands and brand_name.lower() in filter_ignore_brands:
                continue

            # filter ODMs
            if device['manufacturer']['name'] == '':
                filter_manufacturer_name = "***unknown***"
            else:
                filter_manufacturer_name = device['manufacturer']['name'].lower()
            if filter_odms:
                if filter_manufacturer_name not in filter_odms:
                    continue
            if filter_ignore_odms:
                if filter_manufacturer_name in filter_ignore_odms:
                    continue

            if filter_device_types:
                if not set(map(lambda x: x.lower(), device['device_types'])).intersection(filter_device_types):
                    continue
            if filter_flags:
                if not set(map(lambda x: x.lower(), device['flags'])).intersection(filter_flags):
                    continue
            if filter_passwords:
                if device['defaults']['password'] not in filter_passwords:
                    continue
            if filter_bootloaders:
                if device['software']['bootloader']['manufacturer'].lower() not in filter_bootloaders:
                    continue
            if filter_jtags:
                if device['has_jtag'] not in filter_jtags:
                    continue
            if filter_operating_systems:
                if device['software']['os'].lower() not in filter_operating_systems:
                    continue
            if filter_serials:
                if device['has_serial_port'] not in filter_serials:
                    continue
            if filter_connectors:
                if device['serial']['connector'].lower() not in filter_connectors:
                    continue
            if filter_baud_rates:
                if device['serial']['baud_rate'] not in filter_baud_rates:
                    continue
            if filter_ips:
                if device['defaults']['ip'] not in filter_ips:
                    continue

            # first collect all the years that have been declared
            # in the data: FCC, wifi certified, release date
            declared_years = []
            if device['commercial']['release_date']:
                declared_years.append(int(device['commercial']['release_date'][:4]))
            for f in device['regulatory']['fcc_ids']:
                if f['fcc_date']:
                    if f['fcc_type'] in ['main', 'unknown']:
                        declared_years.append(int(f['fcc_date'][:4]))
            if device['regulatory']['wifi_certified_date']:
                declared_years.append(int(device['regulatory']['wifi_certified_date'][:4]))

            if filter_years:
                if not set(filter_years).intersection(declared_years):
                    continue

            if filter_programs:
                show_node = False
                if 'programs' in device['software']:
                    for prog in device['software']['programs']:
                        if prog['name'].lower() in filter_programs:
                            show_node = True
                            break
                if not show_node:
                    continue

            if filter_files:
                show_node = False
                if 'files' in device['software']:
                    for prog in device['software']['files']:
                        if prog['name'].lower() in filter_files:
                            show_node = True
                            break
                if not show_node:
                    continue

            if filter_chips:
                show_node = False
                for cpu in device['cpus']:
                    if cpu['model'].lower() in filter_chips:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_chip_types:
                show_node = False
                for cpu in device['cpus']:
                    if cpu['chip_type'].lower() in filter_chip_types:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_chip_vendors:
                show_node = False
                for cpu in device['cpus']:
                    if cpu['manufacturer'].lower() in filter_chip_vendors:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_ignore_origins:
                show_node = True
                for origin in device['origins']:
                    if origin['origin'].lower() in filter_ignore_origins:
                        show_node = False
                        break
                if not show_node:
                    continue

            if filter_origins:
                show_node = False
                for origin in device['origins']:
                    if origin['origin'].lower() in filter_origins:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_packages:
                show_node = False
                for package in device['software']['packages']:
                    if package['name'].lower() in filter_packages:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_partitions:
                show_node = False
                for partition in device['software']['partitions']:
                    if partition['name'].lower() in filter_partitions:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_rootfs:
                show_node = False
                for fs in device['software']['rootfs']:
                    if fs.lower() in filter_rootfs:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_sdks:
                if device['software']['sdk']['name'].lower() not in filter_sdks:
                    continue

            if filter_fccs:
                show_node = False
                for fcc_id in device['regulatory']['fcc_ids']:
                    if fcc_id['fcc_id'].lower() in filter_fccs:
                        show_node = True
                        break
                if not show_node:
                    continue

            if brand_name not in brands_to_devices:
                brands_to_devices[brand_name] = []
            model = device['model']['model']
            if device['model']['revision'] != '':
                model += " "
                model += device['model']['revision']
            if device['model']['submodel'] != '':
                model += " "
                model += device['model']['submodel']
            if device['model']['subrevision'] != '':
                model += " "
                model += device['model']['subrevision']

            device_types.update(device['device_types'])

            # compute the labels used in the leaves
            labels = set()
            for f in device['flags']:
                if "voip" in f.lower() or 'telephone' in f.lower() or " phone" in f.lower():
                    labels.add(":phone:")
            for d in device['device_types']:
                if "voip" in d.lower() or 'telephone' in d.lower() or " phone" in d.lower():
                    labels.add(":phone:")
            if 'linux' in device['software']['os'].lower():
                labels.add(":penguin:")
            if 'android' in device['software']['os'].lower():
                labels.add(":robot:")
            if 'fcc_data' in device:
                labels.add("\U000024BB")

            brands_to_devices[brand_name].append({'model': model, 'data': device, 'labels': sorted(labels)})
            brands.add(brand_name.lower())
            brand_data.append(brand_name)

            years.update(declared_years)
            year_data += declared_years

            manufacturer_name = device['manufacturer']['name']
            if manufacturer_name == '':
                manufacturer_name = '***UNKNOWN***'
            if manufacturer_name not in odm_to_devices:
                odm_to_devices[manufacturer_name] = {}
            if brand_name not in odm_to_devices[manufacturer_name]:
                odm_to_devices[manufacturer_name][brand_name] = []
            odm_to_devices[manufacturer_name][brand_name].append({'model': model, 'data': device, 'labels': sorted(labels)})
            odms.add(manufacturer_name.lower())

            if device['defaults']['ip'] != '':
                ips.add(device['defaults']['ip'])

            if device['defaults']['password'] != '':
                passwords.add(device['defaults']['password'])

            if device['software']['bootloader']['manufacturer'] != '':
                bootloaders.add(device['software']['bootloader']['manufacturer'].lower())

            if device['serial']['connector'] != '':
                connectors.add(device['serial']['connector'].lower())
                odm_connector.append((manufacturer_name, device['serial']['connector']))
            if device['serial']['baud_rate'] != 0:
                baud_rates.add(device['serial']['baud_rate'])

            for cpu in device['cpus']:
                cpu_vendor_name = cpu['manufacturer']
                chip_vendors.add(cpu_vendor_name.lower())
                if cpu['model'] != '':
                    chips.add(cpu['model'].lower())
                if cpu['chip_type'] != '':
                    chip_types.add(cpu['chip_type'].lower())
                brand_cpu.append((brand_name, cpu_vendor_name))
                odm_cpu.append((manufacturer_name, cpu_vendor_name))
                if device['serial']['connector'] != '':
                    chip_vendor_connector.append((cpu_vendor_name, device['serial']['connector']))

            for chip in device['network']['chips']:
                chip_vendor_name = chip['manufacturer']
                chip_vendors.add(chip_vendor_name.lower())

                if chip['model'] != '':
                    chips.add(chip['model'].lower())

            for chip in device['flash']:
                chip_vendor_name = chip['manufacturer']
                chip_vendors.add(chip_vendor_name.lower())

                if chip['model'] != '':
                    chips.add(chip['model'].lower())

            for fcc_id in device['regulatory']['fcc_ids']:
                fcc_ids.add(fcc_id['fcc_id'].lower())

            for package in device['software']['packages']:
                package_name = package['name'].lower()
                packages.add(package_name)

            for partition in device['software']['partitions']:
                partition_name = partition['name']
                partitions.add(partition_name.lower())

            for fs in device['software']['rootfs']:
                rootfs.add(fs.lower())

            if device['software']['sdk']:
                sdks.add(device['software']['sdk']['name'].lower())

            if 'programs' in device['software']:
                for prog in device['software']['programs']:
                    program_name = prog['name'].lower()
                    programs.add(program_name)

            if 'files' in device['software']:
                for f in device['software']['files']:
                    file_name = f['name'].lower()
                    files.add(file_name)

            brand_odm.append((brand_name, manufacturer_name))

            flags.update([x.casefold() for x in device['flags']])

        return {'brands_to_devices': brands_to_devices, 'odm_to_devices': odm_to_devices,
                'baud_rates': baud_rates, 'bootloaders': bootloaders, 'brands': brands,
                'brand_data': brand_data, 'chips': chips, 'chip_types': chip_types,
                'chip_vendors': chip_vendors, 'connectors': connectors, 'odms': odms,
                'fcc_ids': fcc_ids, 'files': files, 'flags': flags, 'ips': ips,
                'brand_odm': brand_odm, 'brand_cpu': brand_cpu, 'odm_cpu': odm_cpu,
                'odm_connector': odm_connector, 'chip_vendor_connector': chip_vendor_connector,
                'packages': packages, 'partitions': partitions, 'passwords': passwords,
                'programs': programs, 'rootfs': rootfs, 'sdks': sdks, 'types': device_types,
                'years': years, 'year_data': year_data}


    def compose(self) -> ComposeResult:
        self.devices = []
        self.overlays = {}

        # process all the JSON files in the directories,
        # right now just the TechInfoDepot one.
        for devicecode_directory in self.devicecode_directories:
            for result_file in devicecode_directory.glob('**/*'):
                if not result_file.is_file():
                    continue

                try:
                    with open(result_file, 'r') as wiki_file:
                        device = json.load(wiki_file)
                        self.devices.append(device)
                except json.decoder.JSONDecodeError:
                    pass
            overlays_directory = devicecode_directory.parent / 'overlays'
            if overlays_directory.exists() and overlays_directory.is_dir():
                for result_file in overlays_directory.glob('**/*'):
                    if not result_file.is_file():
                        continue
                    device_name = result_file.parent.name
                    if device_name not in self.overlays:
                        self.overlays[device_name] = []
                    try:
                        with open(result_file, 'r') as wiki_file:
                            overlay = json.load(wiki_file)
                            if 'type' not in overlay:
                                continue
                            if overlay['type'] != 'overlay':
                                continue
                            self.overlays[device_name].append(overlay)
                    except json.decoder.JSONDecodeError:
                        pass

        data = self.compose_data_sets()

        brands_to_devices = data['brands_to_devices']
        odm_to_devices = data['odm_to_devices']
        baud_rates = data['baud_rates']
        bootloaders = data['bootloaders']
        brands = data['brands']
        brand_data = data['brand_data']
        chips = data['chips']
        chip_types = data['chip_types']
        chip_vendors = data['chip_vendors']
        connectors = data['connectors']
        device_types = data['types']
        odms = data['odms']
        fcc_ids = data['fcc_ids']
        flags = data['flags']
        files = data['files']
        ips = data['ips']
        brand_odm = data['brand_odm']
        brand_cpu = data['brand_cpu']
        odm_cpu = data['odm_cpu']
        odm_connector = data['odm_connector']
        operating_systems = defaults.KNOWN_OS
        packages = data['packages']
        partitions = data['partitions']
        passwords = data['passwords']
        programs = data['programs']
        rootfs = data['rootfs']
        sdks = data['sdks']
        chip_vendor_connector = data['chip_vendor_connector']
        years = data['years']
        year_data = data['year_data']

        # build the various datatables.
        brand_datatable_data = collections.Counter(brand_data)
        brand_odm_datatable_data = collections.Counter(brand_odm)
        brand_cpu_datatable_data = collections.Counter(brand_cpu)
        odm_cpu_datatable_data = collections.Counter(odm_cpu)
        odm_connector_data = collections.Counter(odm_connector)
        chip_vendor_connector_data = collections.Counter(chip_vendor_connector)
        year_datatable_data = collections.Counter(year_data)

        self.brand_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.brand_data_table.add_columns("rank", "count", "brand")
        rank = 1
        for i in brand_datatable_data.most_common():
            self.brand_data_table.add_row(rank, i[1], i[0])
            rank += 1

        self.brand_odm_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.brand_odm_data_table.add_columns("rank", "count", "brand", "ODM")
        rank = 1
        for i in brand_odm_datatable_data.most_common():
            self.brand_odm_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1

        self.brand_cpu_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.brand_cpu_data_table.add_columns("rank", "count", "brand", "CPU brand")
        rank = 1
        for i in brand_cpu_datatable_data.most_common():
            self.brand_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1

        self.odm_cpu_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.odm_cpu_data_table.add_columns("rank", "count", "ODM", "CPU brand")
        rank = 1
        for i in odm_cpu_datatable_data.most_common():
            self.odm_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1

        self.odm_connector_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.odm_connector_data_table.add_columns("rank", "count", "ODM", "connector")
        rank = 1
        for i in odm_connector_data.most_common():
            self.odm_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1

        self.chip_vendor_connector_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.chip_vendor_connector_data_table.add_columns("rank", "count", "CPU", "connector")
        rank = 1
        for i in chip_vendor_connector_data.most_common():
            self.chip_vendor_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1

        self.year_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.year_data_table.add_columns("rank", "count", "year")
        rank = 1
        for i in year_datatable_data.most_common():
            self.year_data_table.add_row(rank, i[1], i[0])
            rank += 1

        # build the various trees.
        self.brand_tree: BrandTree[dict] = BrandTree("DeviceCode brand results")
        self.brand_tree.show_root = False
        self.brand_tree.root.expand()
        self.brand_tree.build_tree(brands_to_devices)

        self.odm_tree: OdmTree[dict] = OdmTree("DeviceCode ODM results")
        self.odm_tree.show_root = False
        self.odm_tree.root.expand()
        self.odm_tree.build_tree(odm_to_devices)

        # Create a table with the results. The root element will
        # not have any associated data with it.
        self.device_data_area = Markdown()
        self.regulatory_data_area = Markdown()
        self.model_data_area = Markdown()
        self.network_data_area = Markdown()
        self.serial_jtag_area = Markdown()
        self.software_area = Markdown()
        self.chips_area = Markdown()
        self.power_area = Markdown()
        self.fcc_area = Markdown()

        # input field
        input_filter = Input(placeholder='Filter',
                            validators=[FilterValidator(bootloaders=bootloaders, brands=brands,
                                            baud_rates=baud_rates, odms=odms, chips=chips,
                                            chip_types=chip_types, chip_vendors=chip_vendors,
                                            connectors=connectors, fcc_ids=fcc_ids, files=files,
                                            ips=ips, packages=packages, partitions=partitions,
                                            passwords=passwords, programs=programs, rootfs=rootfs,
                                            sdks=sdks, types=device_types,
                                            token_names=self.TOKEN_NAMES)],
                            suggester=SuggestDevices(self.TOKEN_NAMES, case_sensitive=False,
                            baud_rates=sorted(baud_rates),
                            bootloaders=sorted(bootloaders), brands=sorted(brands),
                            chips=sorted(chips), chip_types=sorted(chip_types),
                            chip_vendors=sorted(chip_vendors), connectors=sorted(connectors),
                            odms=sorted(odms), operating_systems=sorted(operating_systems),
                            fcc_ids=sorted(fcc_ids), files=sorted(files), flags=sorted(flags),
                            packages=sorted(packages), partitions=sorted(partitions),
                            passwords=sorted(passwords), programs=sorted(programs),
                            rootfs=sorted(rootfs), sdks=sorted(sdks), types=sorted(device_types)),
                            valid_empty=True)

        # Yield the elements. The UI is a container with an app grid. On the left
        # there are some tabs, each containing a tree. On the right there is a
        # an area to display the results.
        yield Header()
        with Container(id='app-grid'):
            with Container(id='left-grid'):
                yield input_filter
                with TabbedContent():
                    with TabPane('Brand view'):
                        yield self.brand_tree
                    with TabPane('ODM view'):
                        yield self.odm_tree
                    with TabPane('Year'):
                        with VerticalScroll():
                            yield self.year_data_table
                    with TabPane('Brand'):
                        with VerticalScroll():
                            yield self.brand_data_table
                    with TabPane('Brand/ODM'):
                        with VerticalScroll():
                            yield self.brand_odm_data_table
                    with TabPane('Brand/CPU vendor'):
                        with VerticalScroll():
                            yield self.brand_cpu_data_table
                    with TabPane('ODM/CPU vendor'):
                        with VerticalScroll():
                            yield self.odm_cpu_data_table
                    '''
                    with TabPane('ODM/connector'):
                        with VerticalScroll():
                            yield self.odm_connector_data_table
                    with TabPane('CPU vendor/connector'):
                        with VerticalScroll():
                            yield self.chip_vendor_connector_data_table
                    '''
            with TabbedContent(id='result-tabs'):
                with TabPane('Device'):
                    with VerticalScroll():
                        yield self.device_data_area
                with TabPane('Model & ODM'):
                    with VerticalScroll():
                        yield self.model_data_area
                with TabPane('Network'):
                    with VerticalScroll():
                        yield self.network_data_area
                with TabPane('Regulatory & Commercial'):
                    with VerticalScroll():
                        yield self.regulatory_data_area
                with TabPane('Serial & JTAG'):
                    with VerticalScroll():
                        yield self.serial_jtag_area
                with TabPane('Software'):
                    with VerticalScroll():
                        yield self.software_area
                with TabPane('Chips'):
                    with VerticalScroll():
                        yield self.chips_area
                with TabPane('Power'):
                    with VerticalScroll():
                        yield self.power_area
                with TabPane('FCC documents'):
                    with VerticalScroll():
                        yield self.fcc_area

        # show the footer with controls
        yield Footer()

    @on(Input.Submitted)
    def process_filter(self, event: Input.Submitted) -> None:
        '''Filter values and create new trees, datatables, and
           refresh data areas'''
        bootloaders = []
        brands = []
        chips = []
        chip_types = []
        chip_vendors = []
        connectors = set()
        device_types = []
        fccs = []
        files = []
        flags = []
        ignore_brands = []
        ignore_odms = []
        ignore_origins = []
        ips = []
        jtags = []
        odms = []
        operating_systems = []
        origins = []
        packages = []
        partitions = []
        passwords = []
        programs = []
        rootfs = []
        sdks = []
        serials = []
        serial_baud_rates = []
        years = []
        is_filtered = False
        refresh = False

        if event.validation_result is None:
            refresh = True
        else:
            if event.validation_result.is_valid:
                is_filtered = True
                refresh = True
                # input was already syntactically validated.
                tokens = shlex.split(event.value.lower())

                for t in tokens:
                    name_params, value = t.split('=', maxsplit=1)
                    if '?' in name_params:
                        name, args = name_params.split('?', maxsplit=1)
                    else:
                        name = name_params
                    if name == 'bootloader':
                        bootloaders.append(value)
                    elif name == 'brand':
                        brands.append(value)
                    elif name == 'chip':
                        chips.append(value)
                    elif name == 'chip_type':
                        chip_types.append(value)
                    elif name == 'chip_vendor':
                        chip_vendors.append(value)
                    elif name == 'connector':
                        connectors.add(value)
                    elif name == 'fccid':
                        fccs.append(value)
                    elif name == 'flag':
                        flags.append(value)
                    elif name == 'ignore_brand':
                        ignore_brands.append(value)
                    elif name == 'ignore_odm':
                        ignore_odms.append(value)
                    elif name == 'ignore_origin':
                        ignore_origins.append(value)
                    elif name == 'file':
                        files.append(value)
                    elif name == 'ip':
                        ips.append(value)
                    elif name == 'odm':
                        odms.append(value)
                    elif name == 'origin':
                        origins.append(value)
                    elif name == 'os':
                        operating_systems.append(value)
                    elif name == 'package':
                        packages.append(value)
                    elif name == 'partition':
                        partitions.append(value)
                    elif name == 'password':
                        passwords.append(value)
                    elif name == 'program':
                        programs.append(value)
                    elif name == 'rootfs':
                        rootfs.append(value)
                    elif name == 'sdk':
                        sdks.append(value)
                    elif name == 'serial':
                        serials.append(value)
                    elif name == 'baud':
                        serial_baud_rates.append(int(value))
                    elif name == 'type':
                        device_types.append(value)
                    elif name == 'jtag':
                        jtags.append(value)
                    elif name == 'year':
                        input_years = sorted(value.split(':', maxsplit=1))
                        if len(input_years) > 1:
                            years += list(range(int(input_years[0]), int(input_years[1]) + 1))
                        else:
                            years += [int(x) for x in input_years]

        if refresh:
            filtered_data = self.compose_data_sets(bootloaders=bootloaders, brands=brands,
                                odms=odms, chips=chips, chip_types=chip_types,
                                chip_vendors=chip_vendors, connectors=connectors, fccs=fccs,
                                files=files, flags=flags, ignore_brands=ignore_brands,
                                ignore_odms=ignore_odms, ignore_origins=ignore_origins, ips=ips,
                                jtags=jtags, operating_systems=operating_systems, origins=origins,
                                passwords=passwords, packages=packages, partitions=partitions,
                                programs=programs, rootfs=rootfs, sdks=sdks, serials=serials,
                                serial_baud_rates=serial_baud_rates, years=years,
                                types=device_types)

            self.brand_tree.build_tree(filtered_data['brands_to_devices'], is_filtered)
            self.odm_tree.build_tree(filtered_data['odm_to_devices'], is_filtered)

            # build the various datatables.
            brand_datatable_data = collections.Counter(filtered_data['brand_data'])
            brand_odm_datatable_data = collections.Counter(filtered_data['brand_odm'])
            brand_cpu_datatable_data = collections.Counter(filtered_data['brand_cpu'])
            odm_cpu_datatable_data = collections.Counter(filtered_data['odm_cpu'])
            odm_connector_data = collections.Counter(filtered_data['odm_connector'])
            chip_vendor_connector_data = collections.Counter(filtered_data['chip_vendor_connector'])
            year_datatable_data = collections.Counter(filtered_data['year_data'])

            # clear and rebuild the data tables
            self.brand_data_table.clear()
            rank = 1
            for i in brand_datatable_data.most_common():
                self.brand_data_table.add_row(rank, i[1], i[0])
                rank += 1

            self.brand_odm_data_table.clear()
            rank = 1
            for i in brand_odm_datatable_data.most_common():
                self.brand_odm_data_table.add_row(rank, i[1], i[0][0], i[0][1])
                rank += 1

            self.brand_cpu_data_table.clear()
            rank = 1
            for i in brand_cpu_datatable_data.most_common():
                self.brand_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
                rank += 1

            self.odm_cpu_data_table.clear()
            rank = 1
            for i in odm_cpu_datatable_data.most_common():
                self.odm_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
                rank += 1

            self.odm_connector_data_table.clear()
            rank = 1
            for i in odm_connector_data.most_common():
                self.odm_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
                rank += 1

            self.chip_vendor_connector_data_table.clear()
            rank = 1
            for i in chip_vendor_connector_data.most_common():
                self.chip_vendor_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
                rank += 1

            self.year_data_table.clear()
            rank = 1
            for i in year_datatable_data.most_common():
                self.year_data_table.add_row(rank, i[1], i[0])
                rank += 1

            # reset the data areas to prevent old data being displayed
            self.device_data_area.update('')
            self.regulatory_data_area.update('')
            self.model_data_area.update('')
            self.network_data_area.update('')
            self.serial_jtag_area.update('')
            self.software_area.update('')
            self.chips_area.update('')
            self.power_area.update('')

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        # TODO: often terminals (such as MATE terminal in Fedora) will
        # already open a link when clicking on it, causing the link to be opened
        # multiple times. Is this desirable?
        if event.href.startswith('http://') or event.href.startswith('https://'):
            webbrowser.open(event.href)

    def on_tree_tree_highlighted(self, event: Tree.NodeHighlighted[None]) -> None:
        pass

    def on_tree_node_selected(self, event: Tree.NodeSelected[None]) -> None:
        '''Display the reports of a node when it is selected'''
        if event.node.data is not None and 'title' in event.node.data:
            self.device_data_area.update(self.build_device_report(event.node.data))
            self.model_data_area.update(self.build_model_report(event.node.data))
            self.network_data_area.update(self.build_network_report(event.node.data['network']))
            self.regulatory_data_area.update(self.build_regulatory_report(event.node.data))
            self.serial_jtag_area.update(self.build_serial_jtag_report(event.node.data))
            self.software_area.update(self.build_software_report(event.node.data['software']))
            self.chips_area.update(self.build_chips_report(event.node.data))
            self.power_area.update(self.build_power_report(event.node.data))
            self.fcc_area.update(self.build_fcc_document_report(event.node.data.get('fcc_data', {})))
        else:
            self.device_data_area.update('')
            self.regulatory_data_area.update('')
            self.model_data_area.update('')
            self.network_data_area.update("")
            self.serial_jtag_area.update('')
            self.software_area.update('')
            self.chips_area.update('')
            self.power_area.update('')
            self.fcc_area.update('')

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed[None]) -> None:
        pass

    def build_chips_report(self, results):
        '''Construct Markdown with chip related information'''
        if results:
            new_markdown = ''
            if results['cpus']:
                new_markdown += f"# Main chips ({len(results['cpus'])})\n"
                new_markdown += "| | |\n|--|--|\n"
                for r in results['cpus']:
                    new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                    new_markdown += f"| **Model** | {r['model']}|\n"
                    new_markdown += f"| **Type** | {r['chip_type']}|\n"
                    new_markdown += f"| **Revision** | {r['chip_type_revision']}|\n"
                    #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                    new_markdown += "| | |\n"
            if results['flash']:
                new_markdown += f"# Flash chips ({len(results['flash'])})\n"
                new_markdown += "| | |\n|--|--|\n"
                for r in results['flash']:
                    new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                    new_markdown += f"| **Model** | {r['model']}|\n"
                    #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                    new_markdown += "| | |\n"
            if results['network']:
                if results['network']['chips']:
                    new_markdown += f"# Network chips ({len(results['network']['chips'])})\n"
                    new_markdown += "| | |\n|--|--|\n"
                    for r in results['network']['chips']:
                        new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                        new_markdown += f"| **Model** | {r['model']}|\n"
                        #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                        new_markdown += "| | |\n"
            if results['switch']:
                new_markdown += f"# Switch chips ({len(results['switch'])})\n"
                new_markdown += "| | |\n|--|--|\n"
                for r in results['switch']:
                    new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                    new_markdown += f"| **Model** | {r['model']}|\n"
                    #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                    new_markdown += "| | |\n"
            if results['radios']:
                radios = []
                for r in results['radios']:
                    if r['chips']:
                        radios += r['chips']
                if radios:
                    new_markdown += f"# Radio chips ({len(radios)})\n"
                    new_markdown += "| | |\n|--|--|\n"
                    for r in radios:
                        new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                        new_markdown += f"| **Model** | {r['model']}|\n"
                        #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                        new_markdown += "| | |\n"
            if results['additional_chips']:
                new_markdown += f"# Additional chips ({len(results['additional_chips'])})\n"
                new_markdown += "| | |\n|--|--|\n"
                for r in results['additional_chips']:
                    new_markdown += f"| **Description** | {r['description']}|\n"
                    new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                    new_markdown += f"| **Model** | {r['model']}|\n"
                    #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                    new_markdown += "| | |\n"
            return new_markdown
        return "No known chips"

    def build_regulatory_report(self, result):
        '''Construct Markdown with regulatory and commercial information
           such as FCC ids, Amazon article numbers, WiFi certification, etc.'''
        new_markdown = ""
        if result:
            new_markdown += "# Regulatory\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Industry Canada ids** | {', '.join(result['regulatory']['industry_canada_ids'])}\n"
            new_markdown += f"|**US ids** | {', '.join(result['regulatory']['us_ids'])}\n"
            new_markdown += f"|**WiFi certified** |{ result['regulatory']['wifi_certified']}\n"
            new_markdown += f"|**WiFi date** | {result['regulatory']['wifi_certified_date']}\n"

            # FCC
            if result['regulatory']['fcc_ids']:
                new_markdown += "# FCC\n"
                new_markdown += "|FCC id|date|type|grantee|\n|--|--|--|--|\n"
                for fcc in result['regulatory']['fcc_ids']:
                    fcc_id = fcc['fcc_id']
                    fcc_date = fcc['fcc_date']
                    fcc_type = fcc['fcc_type']
                    grantee = fcc.get('grantee', '')
                    new_markdown += f"|[{fcc_id}](<https://fcc.report/FCC-ID/{fcc_id}>)|{fcc_date}|{fcc_type}|{grantee}|\n"

            # Commercial information
            new_markdown += "# Commercial\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Availability** | {result['commercial']['availability']}\n"
            new_markdown += f"|**Release date** | {result['commercial']['release_date']}\n"
            eans = ", ".join(result['commercial']['ean'])
            new_markdown += f"|**International Article Number** | {eans}\n"
            upcs = ", ".join(result['commercial']['upc'])
            new_markdown += f"|**Universal Product Code** | {upcs}\n"
            neweggs = ", ".join(result['commercial']['newegg'])
            new_markdown += f"|**Newegg item number** | {neweggs}\n"
            new_markdown += f"|**Deal Extreme item number** | {result['commercial']['deal_extreme']}\n"

        return new_markdown

    def build_serial_jtag_report(self, result):
        '''Construct Markdown with serial port and JTAG information'''
        if result:
            new_markdown = ''
            if result['has_jtag'] == 'yes':
                new_markdown += "# JTAG\n"
                new_markdown += "| | |\n|--|--|\n"
                if result['jtag']['baud_rate'] != 0:
                    new_markdown += f"|**Baud rate** | {result['jtag']['baud_rate']}\n"
                else:
                    new_markdown += "|**Baud rate** |\n"
                new_markdown += f"|**Connector** |{ result['jtag']['connector']}\n"
                if result['jtag']['number_of_pins'] != 0:
                    new_markdown += f"|**Number of pins** | {result['jtag']['number_of_pins']}\n"
                else:
                    new_markdown += "|**Number of pins** | \n"
                new_markdown += f"|**Populated** | {result['jtag']['populated']}\n"
                if result['jtag']['voltage']:
                    new_markdown += f"|**Voltage** | {result['jtag']['voltage']}\n"
                else:
                    new_markdown += "|**Voltage** |\n"
            if result['has_serial_port'] == 'yes':
                new_markdown += "# Serial port\n"
                new_markdown += "| | |\n|--|--|\n"
                if result['serial']['baud_rate'] != 0:
                    new_markdown += f"|**Baud rate** | {result['serial']['baud_rate']}\n"
                else:
                    new_markdown += "|**Baud rate** |\n"
                new_markdown += f"|**Connector** |{ result['serial']['connector']}\n"
                if result['serial']['number_of_pins'] != 0:
                    new_markdown += f"|**Number of pins** | {result['serial']['number_of_pins']}\n"
                else:
                    new_markdown += "|**Number of pins** | \n"
                new_markdown += f"|**Populated** | {result['serial']['populated']}\n"
                if result['serial']['data_parity_stop']:
                    new_markdown += f"|**Data/parity/stop** | {result['serial']['data_parity_stop']}\n"
                else:
                    new_markdown += "|**Data/parity/stop** |\n"
                if result['serial']['voltage']:
                    new_markdown += f"|**Voltage** | {result['serial']['voltage']}\n"
                else:
                    new_markdown += "|**Voltage** |\n"
                if result['serial']['comments']:
                    new_markdown += f"|**Comments** | {result['serial']['comments']}\n"
                else:
                    new_markdown += "|**Comments** |\n"
            return new_markdown
        return "No serial information"

    def build_fcc_document_report(self, result):
        '''Construct Markdown with information from downloaded FCC reports'''
        new_markdown = ""
        if result:
            for pdf in result:
                fcc_id = pdf['fcc_id']
                pdf_name = pdf['pdf']
                new_markdown += f"# [{pdf_name}](<https://fcc.report/FCC-ID/{fcc_id}/{pdf_name}>): {pdf['type']} - {pdf['description']}\n"
                new_markdown += "| Page | Type | Hint | Extra data|\n|--|--|--|--|\n"
                for hint in pdf['hints']:
                    page = hint['page']
                    for hint_result in hint['results']:
                        extra_data = hint_result.get('extra_data', '')
                        new_markdown += f"|{page} | {hint_result['type']} | {hint_result['value']} | {extra_data} |\n"
        return new_markdown

    def build_software_report(self, result):
        '''Construct Markdown with software related information, such as
           bootloader, packages, partitions, file names, etcetera'''
        new_markdown = ""
        if result:
            # bootloader
            new_markdown += "# Bootloader\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Name** |{ result['bootloader']['manufacturer']}\n"
            new_markdown += f"|**Version** |{ result['bootloader']['version']}\n"
            new_markdown += f"|**Modified** |{ result['bootloader']['vendor_modified']}\n"
            extra_infos = ", ".join(result['bootloader']['extra_info'])
            new_markdown += f"|**Extra info** | {extra_infos}\n"

            # software
            new_markdown += "# Operating system, SDK & Third party software\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**OS** |{ result['os']}\n"
            new_markdown += f"|**SDK** |{ result['sdk']['name']}\n"
            third_parties = ", ".join(result['third_party'])
            new_markdown += f"|**Third party software** | {third_parties}\n"
            #new_markdown += f"|**DD-WRT** |{ result['ddwrt']}\n"
            #new_markdown += f"|**Gargoyle** |{ result['gargoyle']}\n"
            #new_markdown += f"|**OpenWrt** |{ result['openwrt']}\n"
            #new_markdown += f"|**Tomato** |{ result['tomato']}\n"

            # Partitions
            new_markdown += "# Partitions\n"
            new_markdown += "|Name|\n|--|\n"
            for p in result['partitions']:
                new_markdown += f"| {p['name']} |\n"

            # rootfs
            new_markdown += "# Rootfs\n"
            new_markdown += "|Name|\n|--|\n"
            for p in result['rootfs']:
                new_markdown += f"| {p} |\n"

            # packages
            new_markdown += "# Packages\n"
            new_markdown += "|Name|Version|Type|\n|--|--|--|\n"
            for p in result['packages']:
                versions = ", ".join(p['versions'])
                new_markdown += f"| {p['name']} | {versions} | {p['package_type']}\n"

            # Programs
            if 'programs' in result:
                new_markdown += "# Programs\n"
                new_markdown += "| | |\n|--|--|\n"
                for p in result['programs']:
                    new_markdown += f"|**Name** |{p['name']}\n"
                    new_markdown += f"|**Full name** |{p['full_name']}\n"
                    new_markdown += f"|**Parameters** |{' '.join( p['parameters'])}\n"
                    new_markdown += f"|**Origin** |{p['origin']}\n"
                    new_markdown += "||\n"
            # Files
            if 'files' in result:
                new_markdown += "# Files\n"
                new_markdown += "|Name|Type|User|Group|\n|--|--|--|--|\n"
                for p in result['files']:
                    new_markdown += f"| {p['name']} | {p['file_type']}| {p['user']} | {p['group']}\n"
        return new_markdown

    def build_model_report(self, result):
        '''Construct Markdown with device model information'''
        new_markdown = ""
        if result:
            new_markdown += "# Model information\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Model** | {result['model']['model']}\n"
            new_markdown += f"|**Part number** |{ result['model']['part_number']}\n"
            new_markdown += f"|**PCB id** | {result['model']['pcb_id']}\n"
            new_markdown += f"|**Revision** | {result['model']['revision']}\n"
            new_markdown += f"|**Serial number** | {result['model']['serial_number']}\n"
            new_markdown += f"|**Series** | {result['model']['series']}\n"
            new_markdown += f"|**Submodel** | {result['model']['submodel']}\n"
            new_markdown += f"|**Subrevision** | {result['model']['subrevision']}\n"

            new_markdown += "# ODM information\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Manufacturer** | {result['manufacturer']['name']}\n"
            new_markdown += f"|**Country** | {result['manufacturer']['country']}\n"
            new_markdown += f"|**Model** | {result['manufacturer']['model']}\n"
            new_markdown += f"|**Revision** | {result['manufacturer']['revision']}\n"
        return new_markdown

    def build_network_report(self, result):
        '''Construct Markdown with network information'''
        new_markdown = ''
        if result:
            new_markdown += "# Network information\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**DOCSIS version** | {result['docsis_version']}\n"
            new_markdown += f"|**LAN ports** | {result['lan_ports']}\n"

            # OUIs
            ethernet_oui_values = []
            for e in result['ethernet_oui']:
                if e['name'] != '':
                    ethernet_oui_values.append(f"{e['oui']} ({e['name']})")
                else:
                    ethernet_oui_values.append(e['oui'])
            ethernet_ouis = ", ".join(ethernet_oui_values)
            new_markdown += f"|**Ethernet OUI** | {ethernet_ouis}\n"

            wireless_oui_values = []
            for e in result['wireless_oui']:
                if e['name'] != '':
                    wireless_oui_values.append(f"{e['oui']} ({e['name']})")
                else:
                    wireless_oui_values.append(e['oui'])
            wireless_ouis = ", ".join(wireless_oui_values)
            new_markdown += f"|**Wireless OUI** | {wireless_ouis}\n"

            if result['chips']:
                new_markdown += f"# Network chips ({len(result['chips'])})\n"
                new_markdown += "| | |\n|--|--|\n"
                for r in result['chips']:
                    new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                    new_markdown += f"| **Model** | {r['model']}|\n"
                    #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                    new_markdown += "| | |\n"
        return new_markdown

    def build_power_report(self, result):
        '''Construct Markdown with power supply information'''
        new_markdown = ''
        if result:
            new_markdown += "# Power Supply\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Brand** | {result['power_supply']['brand']}\n"
            new_markdown += f"|**Model** | {result['power_supply']['model']}\n"
            new_markdown += f"|**Revision** | {result['power_supply']['revision']}\n"
            new_markdown += f"|**Style** | {result['power_supply']['style']}\n"
            new_markdown += f"|**Country** | {result['power_supply']['country']}\n"
            new_markdown += f"|**e-level** | {result['power_supply']['e_level']}\n"
            new_markdown += f"|**Input amperage** | {result['power_supply']['input_amperage']}\n"
            new_markdown += f"|**Input connector** | {result['power_supply']['input_connector']}\n"
            new_markdown += f"|**Input current** | {result['power_supply']['input_current']}\n"
            new_markdown += f"|**Input Hz** | {result['power_supply']['input_hz']}\n"
            new_markdown += f"|**Input voltage** | {result['power_supply']['input_voltage']}\n"
            new_markdown += f"|**Output amperage** | {result['power_supply']['output_amperage']}\n"
            new_markdown += f"|**Output connector** | {result['power_supply']['output_connector']}\n"
            new_markdown += f"|**Output current** | {result['power_supply']['output_current']}\n"
            new_markdown += f"|**Output voltage** | {result['power_supply']['output_voltage']}\n"
        return new_markdown

    def build_device_report(self, result):
        '''Construct Markdown with top level device information'''
        new_markdown = ""
        if result:
            new_markdown = "| | |\n|--|--|\n"
            new_markdown += f"|**Title** | {result['title']}\n"
            new_markdown += f"|**Brand** | {result['brand']}\n"

            declared_years = set()
            if result['commercial']['release_date']:
                declared_years.add(result['commercial']['release_date'][:4])
            for f in result['regulatory']['fcc_ids']:
                if f['fcc_date']:
                    if f['fcc_type'] in ['main', 'unknown']:
                        declared_years.add(f['fcc_date'][:4])
            if result['regulatory']['wifi_certified_date']:
                declared_years.add(result['regulatory']['wifi_certified_date'][:4])

            estimated_years = ", ".join(sorted(declared_years))
            new_markdown += f"|**Estimated year** | {estimated_years}\n"

            # Taglines, flags, device types
            taglines = ", ".join(result['taglines'])
            new_markdown += f"|**Taglines** | {taglines}\n"
            device_types = ", ".join(result['device_types'])
            new_markdown += f"|**Device types** | {device_types}\n"
            flags = ", ".join(result['flags'])
            new_markdown += f"|**Flags** | {flags}\n"

            # Web sites
            product_pages = " , ".join(result['web']['product_page'])
            new_markdown += f"|**Product pages** | {product_pages}\n"
            support_pages = " , ".join(result['web']['support_page'])
            new_markdown += f"|**Support pages** | {support_pages}\n"

            # Default values
            new_markdown += f"|**IP address** | {result['defaults']['ip']}\n"
            new_markdown += f"|**IP address comment** | {result['defaults']['ip_comment']}\n"
            logins = " , ".join(result['defaults']['logins'])
            new_markdown += f"|**Logins** | {logins}\n"
            new_markdown += f"|**Login comment** | {result['defaults']['logins_comment']}\n"
            new_markdown += f"|**Password** | {result['defaults']['password']}\n"
            new_markdown += f"|**Password comment** | {result['defaults']['password_comment']}\n"

            new_markdown += "# Data origin\n"
            new_markdown += "|Origin|URL|\n|--|--|\n"

            for origin in result['origins']:
                if origin['origin'] == 'TechInfoDepot':
                    origin_data_url = f" <https://techinfodepot.shoutwiki.com/wiki/{origin['data_url']}>"
                elif origin['origin'] == 'WikiDevi':
                    origin_data_url = f" <https://wikidevi.wi-cat.ru/{origin['data_url']}>"
                elif origin['origin'] == 'OpenWrt':
                    origin_data_url = f" <https://openwrt.org/{origin['data_url']}>"
                else:
                    continue
                new_markdown += f"{origin['origin']}|{origin_data_url}\n"

        return new_markdown

@click.command(short_help='Interactive DeviceCode result browser')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
def main(devicecode_directory, wiki_type):
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    # verify the directory names, they should be one of the following
    valid_directory_names = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']

    # Inside these directories a directory called 'devices' should always
    # be present. Optionally there can be a directory called 'overlays'
    # with overlay files.
    # If available the 'squashed' directory will always be preferred.

    squashed_directory = devicecode_directory / 'squashed'
    if squashed_directory.exists() and not wiki_type:
        devicecode_dirs = [squashed_directory]
    else:
        devicecode_dirs = []
        for p in devicecode_directory.iterdir():
            if not p.is_dir():
                continue
            if not p.name in valid_directory_names:
                continue
            if wiki_type:
                if p.name != wiki_type:
                    continue
            devices_dir = p / 'devices'
            if not (devices_dir.exists() and devices_dir.is_dir()):
                continue
            devicecode_dirs.append(devices_dir)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    app = DevicecodeUI(devicecode_dirs)
    app.run()

if __name__ == "__main__":
    main()
