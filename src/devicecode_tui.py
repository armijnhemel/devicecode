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


class SuggestDevices(Suggester):
    '''A custom suggester, based on the SuggestFromList example from Textual'''

    def __init__(
        self, suggestions: Iterable[str], *, case_sensitive: bool = True,
    **kwargs) -> None:
        super().__init__(case_sensitive=case_sensitive)
        self._suggestions = list(suggestions)
        self._for_comparison = (
            self._suggestions
            if self.case_sensitive
            else [suggestion.casefold() for suggestion in self._suggestions]
        )
        self.bootloaders = kwargs.get('bootloaders', [])
        self.brands = kwargs.get('brands', [])
        self.chip_vendors = kwargs.get('chip_vendors', [])
        self.flags = kwargs.get('flags', [])
        self.odms = kwargs.get('odms', [])

    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """

        serial_values = ['no', 'unknown', 'yes']

        # first split the value
        check_value = value.rsplit(' ', maxsplit=1)[-1]
        if check_value.startswith('odm='):
            for idx, chk in enumerate(self.odms):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.odms[idx][len(check_value)-4:]
        elif check_value.startswith('ignore_odm='):
            for idx, chk in enumerate(self.odms):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.odms[idx][len(check_value)-11:]
        elif check_value.startswith('ignore_brand='):
            for idx, chk in enumerate(self.brands):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.brands[idx][len(check_value)-13:]
        elif check_value.startswith('brand='):
            for idx, chk in enumerate(self.brands):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.brands[idx][len(check_value)-6:]
        elif check_value.startswith('bootloader='):
            for idx, chk in enumerate(self.bootloaders):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.bootloaders[idx][len(check_value)-11:]
        elif check_value.startswith('chip_vendor='):
            for idx, chk in enumerate(self.chip_vendors):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.chip_vendors[idx][len(check_value)-12:]
        elif check_value.startswith('flag='):
            for idx, chk in enumerate(self.flags):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + self.flags[idx][len(check_value)-5:]
        elif check_value.startswith('serial='):
            for idx, chk in enumerate(serial_values):
                if chk.startswith(check_value.rsplit('=', maxsplit=1)[-1]):
                    return value + serial_values[idx][len(check_value)-7:]

        for idx, suggestion in enumerate(self._for_comparison):
            if suggestion.startswith(check_value):
                return value + self._suggestions[idx][len(check_value):]
        return None

class FilterValidator(Validator):
    '''Syntax validator for the filtering language.'''

    TOKEN_IDENTIFIERS = ['bootloader', 'brand', 'chip', 'chip_vendor', 'connector',
                         'flag', 'ignore_brand', 'ignore_odm', 'odm', 'password',
                         'serial', 'type', 'year']

    def __init__(self, **kwargs):
        self.bootloaders = kwargs.get('bootloaders', set())
        self.brands = kwargs.get('brands', set())
        self.odms = kwargs.get('odms', set())
        self.chip_vendors = kwargs.get('chip_vendors', set())
        self.connectors = kwargs.get('connectors', set())

    def validate(self, value: str) -> ValidationResult:
        try:
            # split the value into tokens
            tokens = shlex.split(value)
            if not tokens:
                return self.failure("Empty string")

            # verify each token
            for t in tokens:
                if '=' not in t:
                    return self.failure("Invalid identifier")
                token_identifier, token_value = t.split('=', maxsplit=1)
                if token_identifier not in self.TOKEN_IDENTIFIERS:
                    return self.failure("Invalid identifier")
                if token_value == '':
                    return self.failure("Invalid identifier")
                elif token_identifier == 'bootloader':
                    if token_value.lower() not in self.bootloaders:
                        return self.failure("Invalid bootloader")
                elif token_identifier == 'brand':
                    if token_value.lower() not in self.brands:
                        return self.failure("Invalid brand")
                elif token_identifier == 'chip_vendor':
                    if token_value.lower() not in self.chip_vendors:
                        return self.failure("Invalid chip vendor")
                elif token_identifier == 'connector':
                    if token_value.lower() not in self.connectors:
                        return self.failure("Invalid connector")
                elif token_identifier == 'ignore_brand':
                    if token_value.lower() not in self.brands:
                        return self.failure("Invalid brand")
                elif token_identifier == 'ignore_odm':
                    if token_value.lower() not in self.odms:
                        return self.failure("Invalid ODM")
                elif token_identifier == 'odm':
                    if token_value.lower() not in self.odms:
                        return self.failure("Invalid ODM")
                elif token_identifier == 'serial':
                    if token_value.lower() not in ['no', 'unknown', 'yes']:
                        return self.failure("Invalid serial port information")
                elif token_identifier == 'year':
                    try:
                        year=int(token_value)
                    except:
                        return self.failure("Invalid year")
                    if year < 1990 or year > 2040:
                        return self.failure("Invalid year")
            return self.success()
        except ValueError:
            return self.failure('Incomplete')

class BrandTree(Tree):
    def __init__(self, brands_to_devices, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.brands_to_devices = brands_to_devices

    def build_tree(self, **kwargs):
        # build the brand_tree.
        self.reset("DeviceCode brand results")

        bootloaders = kwargs.get('bootloaders', [])
        brands = kwargs.get('brands', [])
        chip_vendors = kwargs.get('chip_vendors', [])
        connectors = kwargs.get('connectors', set())
        flags = kwargs.get('flags', [])
        ignore_brands = kwargs.get('ignore_brands', [])
        ignore_odms = kwargs.get('ignore_odms', [])
        odms = kwargs.get('odms', [])
        passwords = kwargs.get('passwords', [])
        serials = kwargs.get('serials', [])
        years = kwargs.get('years', [])

        expand = False
        if brands or chip_vendors or connectors or flags or ignore_brands or \
            ignore_odms or odms or passwords or serials or years:
            expand = True

        for brand in sorted(self.brands_to_devices.keys(), key=str.casefold):
            if brands and brand.lower() not in brands:
                continue
            if ignore_brands and brand.lower() in ignore_brands:
                continue

            # add each brand as a node. Then add each model as a leaf.
            node = self.root.add(brand, expand=expand)

            # recurse into the device and add nodes for
            # devices, after filtering
            node_leaves = 0
            for model in sorted(self.brands_to_devices[brand], key=lambda x: x['model']):
                if odms:
                    if model['data']['manufacturer']['name'].lower() not in odms:
                        continue
                if ignore_odms:
                    if model['data']['manufacturer']['name'].lower() in ignore_odms:
                        continue
                if flags:
                    if not set(map(lambda x: x.lower(), model['data']['flags'])).intersection(flags):
                        continue
                if passwords:
                    if model['data']['defaults']['password'] not in passwords:
                        continue
                if bootloaders:
                    if model['data']['software']['bootloader']['manufacturer'].lower() not in bootloaders:
                        continue
                if serials:
                    if model['data']['has_serial_port'] not in serials:
                        continue
                if connectors:
                    if model['data']['serial']['connector'].lower() not in connectors:
                        continue
                if years:
                    # first collect all the years that have been declared
                    # in the data: FCC, wifi certified, release date
                    declared_years = []
                    if model['data']['commercial']['release_date']:
                        declared_years.append(int(model['data']['commercial']['release_date'][:4]))
                    if model['data']['regulatory']['fcc_date']:
                        declared_years.append(int(model['data']['regulatory']['fcc_date'][:4]))
                    if model['data']['regulatory']['wifi_certified_date']:
                        declared_years.append(int(model['data']['regulatory']['wifi_certified_date'][:4]))
                    if not set(years).intersection(declared_years):
                        continue
                if chip_vendors:
                    cpu_found = False
                    for cpu in model['data']['cpus']:
                        if cpu['manufacturer'].lower() in chip_vendors:
                            cpu_found = True
                            break
                    if cpu_found:
                        node.add_leaf(model['model'], data=model['data'])
                        node_leaves += 1
                else:
                    node.add_leaf(model['model'], data=model['data'])
                    node_leaves += 1

            # check if there are any valid leaf nodes.
            # If not, remove the brand node
            if node_leaves == 0:
                node.remove()
            node.label = f"{node.label} ({node_leaves})"


class OdmTree(Tree):
    def __init__(self, odm_to_devices, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.odm_to_devices = odm_to_devices

    def build_tree(self, **kwargs):
        # build the odm_tree.
        self.reset("DeviceCode OEM results")

        bootloaders = kwargs.get('bootloaders', [])
        brands = kwargs.get('brands', [])
        chip_vendors = kwargs.get('chip_vendors', [])
        connectors = kwargs.get('connectors', set())
        flags = kwargs.get('flags', [])
        ignore_brands = kwargs.get('ignore_brands', [])
        ignore_odms = kwargs.get('ignore_odms', [])
        odms = kwargs.get('odms', [])
        passwords = kwargs.get('passwords', [])
        serials = kwargs.get('serials', [])
        years = kwargs.get('years', [])

        expand = False
        if brands or chip_vendors or connectors or flags or ignore_brands or \
            ignore_odms or odms or passwords or serials or years:
            expand = True

        # add each manufacturer as a node. Then add each brand as a subtree
        # and each model as a leaf. Optionally filter for brands and prune.
        for odm in sorted(self.odm_to_devices.keys(), key=str.casefold):
            if odms and odm.lower() not in odms:
                continue
            if ignore_odms and odm.lower() in ignore_odms:
                continue

            # create a node with brand subnodes
            node = self.root.add(odm, expand=expand)
            node_leaves = 0
            for brand in sorted(self.odm_to_devices[odm], key=str.casefold):
                if brands and brand.lower() not in brands:
                    continue
                if ignore_brands and brand.lower() in ignore_brands:
                    continue

                # recurse into the device and add nodes for
                # devices, after filtering
                brand_node = node.add(brand)
                brand_node_leaves = 0
                for model in sorted(self.odm_to_devices[odm][brand], key=lambda x: x['model']):
                    if flags:
                        if not set(map(lambda x: x.lower(), model['data']['flags'])).intersection(flags):
                            continue
                    if passwords:
                        if model['data']['defaults']['password'] not in passwords:
                            continue
                    if bootloaders:
                        if model['data']['software']['bootloader']['manufacturer'].lower() not in bootloaders:
                            continue
                    if serials:
                        if model['data']['has_serial_port'] not in serials:
                            continue
                    if connectors:
                        if model['data']['serial']['connector'].lower() not in connectors:
                            continue
                    if years:
                        # first collect all the years that have been declared
                        # in the data: FCC, wifi certified, release date
                        declared_years = []
                        if model['data']['commercial']['release_date']:
                            declared_years.append(int(model['data']['commercial']['release_date'][:4]))
                        if model['data']['regulatory']['fcc_date']:
                            declared_years.append(int(model['data']['regulatory']['fcc_date'][:4]))
                        if model['data']['regulatory']['wifi_certified_date']:
                            declared_years.append(int(model['data']['regulatory']['wifi_certified_date'][:4]))
                        if not set(years).intersection(declared_years):
                            continue
                    if chip_vendors:
                        cpu_found = False
                        for cpu in model['data']['cpus']:
                            if cpu['manufacturer'].lower() in chip_vendors:
                                cpu_found = True
                                break
                        if cpu_found:
                            brand_node.add_leaf(model['model'], data=model['data'])
                            brand_node_leaves += 1
                            node_leaves += 1
                    else:
                        brand_node.add_leaf(model['model'], data=model['data'])
                        brand_node_leaves += 1
                        node_leaves += 1

                # check if there are any valid leaf nodes.
                # If not, remove the brand node
                if brand_node_leaves == 0:
                    brand_node.remove()
                else:
                    brand_node.label = f"{brand_node.label} ({brand_node_leaves})"

            # check if there are any valid leaf nodes.
            # If not, remove the ODM node
            if node_leaves == 0:
                node.remove()
            node.label = f"{node.label} ({node_leaves})"

class DevicecodeUI(App):
    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="Quit"),
    ]

    CSS_PATH = "devicecode_tui.css"
    TOKEN_IDENTIFIERS = ['bootloader', 'brand', 'chip', 'chip_vendor', 'connector',
                         'flag', 'ignore_brand', 'ignore_odm', 'odm', 'password',
                         'serial', 'type', 'year']

    def __init__(self, devicecode_dir, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.devicecode_directory = devicecode_dir

    def compose(self) -> ComposeResult:
        # store a mapping of brands to devices
        brands_to_devices = {}
        odm_to_devices = {}
        bootloaders = set()
        brands = set()
        chip_vendors = set()
        connectors = set()
        odms = set()
        flags = set()

        self.devices = []

        # process all the JSON files in the directory
        for result_file in self.devicecode_directory.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    self.devices.append(device)
            except json.decoder.JSONDecodeError:
                pass

        brand_odm = []
        brand_cpu = []
        odm_cpu = []
        odm_connector = []
        chip_connector = []
        for device in self.devices:
            brand_name = device['brand']
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
            brands_to_devices[brand_name].append({'model': model, 'data': device})
            brands.add(brand_name.lower())

            manufacturer_name = device['manufacturer']['name']
            if manufacturer_name == '':
                manufacturer_name = '***UNKNOWN***'
            if manufacturer_name not in odm_to_devices:
                odm_to_devices[manufacturer_name] = {}
            if brand_name not in odm_to_devices[manufacturer_name]:
                odm_to_devices[manufacturer_name][brand_name] = []
            odm_to_devices[manufacturer_name][brand_name].append({'model': model, 'data': device})
            odms.add(manufacturer_name.lower())

            if device['software']['bootloader']['manufacturer'] != '':
                bootloaders.add(device['software']['bootloader']['manufacturer'].lower())

            if device['serial']['connector'] != '':
                connectors.add(device['serial']['connector'].lower())
                odm_connector.append((manufacturer_name, device['serial']['connector']))

            for cpu in device['cpus']:
                cpu_vendor_name = cpu['manufacturer']
                chip_vendors.add(cpu_vendor_name.lower())
                brand_cpu.append((brand_name, cpu_vendor_name))
                odm_cpu.append((manufacturer_name, cpu_vendor_name))
                if device['serial']['connector'] != '':
                    chip_connector.append((cpu_vendor_name, device['serial']['connector']))

            brand_odm.append((brand_name, manufacturer_name))

            flags.update([x.casefold() for x in device['flags']])

        brand_odm_datatable_data = collections.Counter(brand_odm)
        brand_cpu_datatable_data = collections.Counter(brand_cpu)
        odm_cpu_datatable_data = collections.Counter(odm_cpu)
        odm_connector_data = collections.Counter(odm_connector)
        chip_connector_data = collections.Counter(chip_connector)

        # build the various trees.
        self.brand_tree: BrandTree[dict] = BrandTree(brands_to_devices, "DeviceCode brand results")
        self.brand_tree.show_root = False
        self.brand_tree.root.expand()
        self.brand_tree.build_tree()

        self.odm_tree: OdmTree[dict] = OdmTree(odm_to_devices, "DeviceCode ODM results")
        self.odm_tree.show_root = False
        self.odm_tree.root.expand()
        self.odm_tree.build_tree()

        self.brand_odm_data_table: DataTable() = DataTable()
        self.brand_odm_data_table.add_columns("rank", "count", "brand", "ODM")
        rank = 1
        for i in brand_odm_datatable_data.most_common():
            self.brand_odm_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1
        self.brand_odm_data_table.fixed_columns = 1

        self.brand_cpu_data_table: DataTable() = DataTable()
        self.brand_cpu_data_table.add_columns("rank", "count", "brand", "CPU brand")
        rank = 1
        for i in brand_cpu_datatable_data.most_common():
            self.brand_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1
        self.brand_cpu_data_table.fixed_columns = 1

        self.odm_cpu_data_table: DataTable() = DataTable()
        self.odm_cpu_data_table.add_columns("rank", "count", "ODM", "CPU brand")
        rank = 1
        for i in odm_cpu_datatable_data.most_common():
            self.odm_cpu_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1
        self.odm_cpu_data_table.fixed_columns = 1

        self.odm_connector_data_table: DataTable() = DataTable()
        self.odm_connector_data_table.add_columns("rank", "count", "ODM", "connector")
        rank = 1
        for i in odm_connector_data.most_common():
            self.odm_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1
        self.odm_connector_data_table.fixed_columns = 1

        self.chip_connector_data_table: DataTable() = DataTable()
        self.chip_connector_data_table.add_columns("rank", "count", "CPU", "connector")
        rank = 1
        for i in chip_connector_data.most_common():
            self.chip_connector_data_table.add_row(rank, i[1], i[0][0], i[0][1])
            rank += 1
        self.chip_connector_data_table.fixed_columns = 1

        # Create a table with the results. The root element will
        # not have any associated data with it.
        self.device_data_area = Markdown()
        self.regulatory_data_area = Markdown()
        self.model_data_area = Markdown()
        self.serial_area = Markdown()
        self.software_area = Markdown()
        self.additional_chips_area = Markdown()

        # Yield the elements. The UI is a container with an app grid. On the left
        # there are some tabs, each containing a tree. On the right there is a
        # an area to display the results.
        yield Header()
        with Container(id='app-grid'):
            with Container(id='left-grid'):
                yield Input(placeholder='Filter',
                            validators=[FilterValidator(bootloaders=bootloaders, brands=brands, odms=odms, chip_vendors=chip_vendors, connectors=connectors)],
                            suggester=SuggestDevices(self.TOKEN_IDENTIFIERS, case_sensitive=False,
                            bootloaders=sorted(bootloaders), brands=sorted(brands), chip_vendors=sorted(chip_vendors),
                            connectors=sorted(connectors), odms=sorted(odms),
                            flags=sorted(flags)), valid_empty=True)
                with TabbedContent():
                    with TabPane('Brand view'):
                        yield self.brand_tree
                    with TabPane('ODM view'):
                        yield self.odm_tree
                    with TabPane('Brand/ODM table'):
                        with VerticalScroll():
                            yield self.brand_odm_data_table
                    with TabPane('Brand/CPU table'):
                        with VerticalScroll():
                            yield self.brand_cpu_data_table
                    with TabPane('ODM/CPU table'):
                        with VerticalScroll():
                            yield self.odm_cpu_data_table
                    with TabPane('ODM/connector table'):
                        with VerticalScroll():
                            yield self.odm_connector_data_table
                    with TabPane('CPU/connector table'):
                        with VerticalScroll():
                            yield self.chip_connector_data_table
            with TabbedContent(id='result-tabs'):
                with TabPane('Device data'):
                    with VerticalScroll():
                        yield self.device_data_area
                with TabPane('Model & ODM'):
                    with VerticalScroll():
                        yield self.model_data_area
                with TabPane('Regulatory'):
                    with VerticalScroll():
                        yield self.regulatory_data_area
                with TabPane('Serial port'):
                    with VerticalScroll():
                        yield self.serial_area
                with TabPane('Software'):
                    with VerticalScroll():
                        yield self.software_area
                with TabPane('Additional chips'):
                    with VerticalScroll():
                        yield self.additional_chips_area

        # show the footer with controls
        footer = Footer()
        footer.ctrl_to_caret = False
        yield footer

    @on(Input.Submitted)
    def process_filter(self, event: Input.Submitted) -> None:
        '''Process the filter, create new tree'''
        if event.validation_result is None:
            self.brand_tree.build_tree()
            self.odm_tree.build_tree()
        else:
            if event.validation_result.is_valid:
                # input was already syntactically validated.
                tokens = shlex.split(event.value)

                bootloaders = []
                brands = []
                chips = []
                chip_vendors = []
                connectors = set()
                flags = []
                ignore_brands = []
                ignore_odms = []
                odms = []
                passwords = []
                serials = []
                years = []

                for t in tokens:
                    identifier, value = t.split('=', maxsplit=1)
                    if identifier == 'bootloader':
                        bootloaders.append(value.lower())
                    elif identifier == 'brand':
                        brands.append(value.lower())
                    elif identifier == 'chip':
                        chips.append(value.lower())
                    elif identifier == 'chip_vendor':
                        chip_vendors.append(value.lower())
                    elif identifier == 'connector':
                        connectors.add(value.lower())
                    elif identifier == 'flag':
                        flags.append(value.lower())
                    elif identifier == 'ignore_brand':
                        ignore_brands.append(value.lower())
                    elif identifier == 'ignore_odm':
                        ignore_odms.append(value.lower())
                    elif identifier == 'odm':
                        odms.append(value.lower())
                    elif identifier == 'password':
                        passwords.append(value.lower())
                    elif identifier == 'serial':
                        serials.append(value.lower())
                    elif identifier == 'year':
                        years.append(int(value))

                self.brand_tree.build_tree(bootloaders=bootloaders, brands=brands, odms=odms, chips=chips,
                                           chip_vendors=chip_vendors, connectors=connectors, flags=flags,
                                           ignore_brands=ignore_brands, ignore_odms=ignore_odms,
                                           passwords=passwords, serials=serials, years=years)
                self.odm_tree.build_tree(bootloaders=bootloaders, brands=brands, odms=odms, chips=chips,
                                         chip_vendors=chip_vendors, connectors=connectors, flags=flags,
                                         ignore_brands=ignore_brands, ignore_odms=ignore_odms,
                                         passwords=passwords, serials=serials, years=years)

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        if event.href.startswith('https://'):
            webbrowser.open(event.href)

    def on_tree_tree_highlighted(self, event: Tree.NodeHighlighted[None]) -> None:
        pass

    def on_tree_node_selected(self, event: Tree.NodeSelected[None]) -> None:
        '''Display the reports of a node when it is selected'''
        if event.node.data is not None:
            self.device_data_area.update(self.build_meta_report(event.node.data))
            self.model_data_area.update(self.build_model_report(event.node.data))
            self.regulatory_data_area.update(self.build_regulatory_report(event.node.data['regulatory']))
            if event.node.data['has_serial_port'] == 'yes':
                self.serial_area.update(self.build_serial_report(event.node.data['serial']))
            else:
                self.serial_area.update('')
            self.software_area.update(self.build_software_report(event.node.data['software']))
            self.additional_chips_area.update(self.build_additional_chips_report(event.node.data['additional_chips']))
        else:
            self.device_data_area.update('')
            self.regulatory_data_area.update('')
            self.model_data_area.update('')
            self.serial_area.update('')
            self.software_area.update('')
            self.additional_chips_area.update('')

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed[None]) -> None:
        pass

    def build_additional_chips_report(self, results):
        if results:
            new_markdown = "| | |\n|--|--|\n"
            for r in results:
                new_markdown += f"| **Description** | {r['description']}|\n"
                new_markdown += f"| **Manufacturer** | {r['manufacturer']}|\n"
                new_markdown += f"| **Model** | {r['model']}|\n"
                #new_markdown += f"| **Extra info** | {r['extra_info']}|\n"
                new_markdown += "| | |\n"
            return new_markdown
        return "No known additional chips"

    def build_regulatory_report(self, result):
        if result:
            new_markdown = "| | |\n|--|--|\n"
            new_markdown += f"|**FCC date** | {result['fcc_date']}\n"
            fcc_ids = ''
            if result['fcc_ids']:
                fcc_id = result['fcc_ids'][0]
                fcc_ids = f"[{fcc_id}](<https://fcc.report/FCC-ID/{fcc_id}>)"

                for f in result['fcc_ids'][1:]:
                    fcc_ids += f", [{f}](<https://fcc.report/FCC-ID/{f}>)"
            new_markdown += f"|**FCC ids** | {fcc_ids}\n"
            new_markdown += f"|**Industry Canada ids** | {', '.join(result['industry_canada_ids'])}\n"
            new_markdown += f"|**US ids** | {', '.join(result['us_ids'])}\n"
            new_markdown += f"|**WiFi certified** |{ result['wifi_certified']}\n"
            new_markdown += f"|**WiFi date** | {result['wifi_certified_date']}\n"
            return new_markdown

    def build_serial_report(self, result):
        if result:
            new_markdown = "| | |\n|--|--|\n"
            if result['baud_rate'] != 0:
                new_markdown += f"|**Baud rate** | {result['baud_rate']}\n"
            else:
                new_markdown += "|**Baud rate** |\n"
            new_markdown += f"|**Connector** |{ result['connector']}\n"
            if result['number_of_pins'] != 0:
                new_markdown += f"|**Number of pins** | {result['number_of_pins']}\n"
            else:
                new_markdown += "|**Number of pins** | \n"
            new_markdown += f"|**Populated** | {result['populated']}\n"
            if result['voltage']:
                new_markdown += f"|**Voltage** | {result['voltage']}\n"
            else:
                new_markdown += "|**Voltage** |\n"
            return new_markdown

    def build_software_report(self, result):
        if result:
            # bootloader
            new_markdown = "# Bootloader\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Name** |{ result['bootloader']['manufacturer']}\n"
            new_markdown += f"|**Version** |{ result['bootloader']['version']}\n"
            new_markdown += f"|**Modified** |{ result['bootloader']['vendor_modified']}\n"
            extra_infos = ", ".join(result['bootloader']['extra_info'])
            new_markdown += f"|**Extra info** | {extra_infos}\n"

            # software
            new_markdown += "# Software\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**OS** |{ result['os']}\n"
            new_markdown += f"|**SDK** |{ result['sdk']}\n"
            third_parties = ", ".join(result['third_party'])
            new_markdown += f"|**Third party software** | {third_parties}\n"
            #new_markdown += f"|**DD-WRT** |{ result['ddwrt']}\n"
            #new_markdown += f"|**Gargoyle** |{ result['gargoyle']}\n"
            #new_markdown += f"|**OpenWrt** |{ result['openwrt']}\n"
            #new_markdown += f"|**Tomato** |{ result['tomato']}\n"
            return new_markdown

    def build_model_report(self, result):
        if result:
            new_markdown = "# Model information\n"
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

    def build_meta_report(self, result):
        if result:
            new_markdown = "| | |\n|--|--|\n"
            new_markdown += f"|**Title** | {result['title']}\n"
            new_markdown += f"|**Brand** | {result['brand']}\n"

            # Taglines, flags, device types
            taglines = ", ".join(result['taglines'])
            new_markdown += f"|**Taglines** | {taglines}\n"
            flags = ", ".join(result['flags'])
            new_markdown += f"|**Flags** | {flags}\n"
            device_types = ", ".join(result['device_types'])
            new_markdown += f"|**Device types** | {device_types}\n"

            # Commercial information
            new_markdown += f"|**Availability** | {result['commercial']['availability']}\n"
            new_markdown += f"|**Release date** | {result['commercial']['release_date']}\n"
            eans = ", ".join(result['commercial']['ean'])
            new_markdown += f"|**International Article Number** | {eans}\n"
            upcs = ", ".join(result['commercial']['upc'])
            new_markdown += f"|**Universal Product Code** | {upcs}\n"

            # Web sites
            product_pages = " , ".join(result['web']['product_page'])
            new_markdown += f"|**Product pages** | {product_pages}\n"
            support_pages = " , ".join(result['web']['support_page'])
            new_markdown += f"|**Support pages** | {support_pages}\n"

            # Misc
            new_markdown += f"|**Data** | {result}\n"
            new_markdown += f"|**Data origin** | {result['wiki_type']}\n"
            return new_markdown

@click.command(short_help='Interactive DeviceCode result browser')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
def main(devicecode_directory):
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    app = DevicecodeUI(devicecode_directory)
    app.run()

if __name__ == "__main__":
    main()
