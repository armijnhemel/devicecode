#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import shlex
import sys

from typing import Any

import click

from rich.console import Group, group
from rich.panel import Panel
from rich import print_json
import rich.table

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.validation import Function, Number, ValidationResult, Validator
from textual.widgets import Footer, Markdown, Static, Tree, TabbedContent, TabPane, Input, Header
from textual.widgets.tree import TreeNode

#from textual.logging import TextualHandler

#logging.basicConfig(
    #level="NOTSET",
    #handlers=[TextualHandler()],
#)


class FilterValidator(Validator):
    '''Syntax validator for the filtering language.'''

    TOKEN_IDENTIFIERS = ['brand', 'chip', 'chip_vendor', 'ignore_brand',
                         'ignore_odm', 'odm', 'sort', 'type']

    def __init__(self, brands=[], odms=[]):
        self.brands = brands
        self.odms = odms

    def validate(self, value: str) -> ValidationResult:
        # split the value into tokens
        try:
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
                if token_identifier == 'brand':
                    if token_value.lower() not in self.brands:
                        return self.failure("Invalid brand")
                elif token_identifier == 'ignore_brand':
                    if token_value.lower() not in self.brands:
                        return self.failure("Invalid brand")
                elif token_identifier == 'ignore_odm':
                    if token_value.lower() not in self.odms:
                        return self.failure("Invalid ODM")
                elif token_identifier == 'odm':
                    if token_value.lower() not in self.odms:
                        return self.failure("Invalid ODM")
            return self.success()
        except ValueError:
            return self.failure('Incomplete')

class BrandTree(Tree):
    def __init__(self, brands_to_devices, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.brands_to_devices = brands_to_devices

    def build_tree(self, brands=[]):
        # build the brand_tree.
        self.reset("DeviceCode brand results")

        for brand in sorted(self.brands_to_devices.keys(), key=str.casefold):
            if brands and brand.lower() not in brands:
                continue
            # add each brand as a node. Then add each model as a leaf.
            node = self.root.add(brand, expand=False)
            for model in sorted(self.brands_to_devices[brand], key=lambda x: x['model']):
                node.add_leaf(model['model'], data=model['data'])

class OdmTree(Tree):
    def __init__(self, odm_to_devices, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.odm_to_devices = odm_to_devices

    def build_tree(self, brands=[], chip_vendors=[], odms=[]):
        # build the odm_tree.
        self.reset("DeviceCode OEM results")

        # add each manufacturer as a node. Then add each brand as a subtree
        # and each model as a leaf. Optionally filter for brands and prune.
        for odm in sorted(self.odm_to_devices.keys(), key=str.casefold):
            if odms and odm.lower() not in odms:
                continue

            # create a node with brand subnodes
            node = self.root.add(odm, expand=False)
            has_brand_leaves = False
            for brand in sorted(self.odm_to_devices[odm], key=str.casefold):
                if brands and brand.lower() not in brands:
                    continue

                # recurse into the device and add nodes for
                # devices, after filtering
                has_leaves = False
                brand_node = node.add(brand)
                for model in sorted(self.odm_to_devices[odm][brand], key=lambda x: x['model']):
                    if chip_vendors:
                        cpu_found = False
                        for cpu in model['data']['cpus']:
                            if cpu['manufacturer'].lower() in chip_vendors:
                                cpu_found = True
                                break
                        if cpu_found:
                            brand_node.add_leaf(model['model'], data=model['data'])
                            has_leaves = True
                    else:
                        brand_node.add_leaf(model['model'], data=model['data'])
                        has_leaves = True

                # check if there are any valid leaf nodes.
                # If not, remove the brand node
                if not has_leaves:
                    brand_node.remove()
                else:
                    has_brand_leaves = True

            # check if there are any valid leaf nodes.
            # If not, remove the ODM node
            if not has_brand_leaves:
                node.remove()

class DevicecodeUI(App):
    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="Quit"),
    ]

    CSS_PATH = "devicecode_tui.css"

    def __init__(self, devicecode_dir, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.devicecode_directory = devicecode_dir

    def compose(self) -> ComposeResult:
        # store a mapping of brands to devices
        brands_to_devices = {}
        odm_to_devices = {}
        brands = []
        chip_vendors = []
        odms = []

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

        for device in self.devices:
            brand_name = device['brand']
            if brand_name not in brands_to_devices:
                brands_to_devices[brand_name] = []
            model = device['model']['model']
            if device['model']['revision'] != '':
                model += " "
                model += device['model']['revision']
            brands_to_devices[brand_name].append({'model': model, 'data': device})
            brands.append(brand_name.lower())

            manufacturer_name = device['manufacturer']['name']
            if manufacturer_name == '':
                manufacturer_name = '***UNKNOWN***'
            if manufacturer_name not in odm_to_devices:
                odm_to_devices[manufacturer_name] = {}
            if brand_name not in odm_to_devices[manufacturer_name]:
                odm_to_devices[manufacturer_name][brand_name] = []
            odm_to_devices[manufacturer_name][brand_name].append({'model': model, 'data': device})
            odms.append(manufacturer_name.lower())

        # build the filter_tree.
        self.filter_tree: Tree[dict] = Tree("DeviceCode filtered results")
        self.filter_tree.show_root = False
        self.filter_tree.root.expand()

        self.brand_tree: BrandTree[dict] = BrandTree(brands_to_devices, "DeviceCode brand results")
        self.brand_tree.show_root = False
        self.brand_tree.root.expand()
        self.brand_tree.build_tree()

        self.odm_tree: OdmTree[dict] = OdmTree(odm_to_devices, "DeviceCode ODM results")
        self.odm_tree.show_root = False
        self.odm_tree.root.expand()
        self.odm_tree.build_tree()

        # Create a table with the results. The root element will
        # not have any associated data with it.
        self.device_data_area = Static(Group(self.build_meta_report(None)))
        self.regulatory_data_area = Static(Group(self.build_meta_report(None)))
        self.additional_chips_area = Static(Group(self.build_meta_report(None)))

        # Yield the elements. The UI is a container with an app grid. On the left
        # there are some tabs, each containing a tree. On the right there is a
        # an area to display the results.
        yield Header()
        with Container(id='app-grid'):
            with Container(id='left-grid'):
                yield Input(placeholder='Filter', validators=[FilterValidator(brands=brands, odms=odms)], valid_empty=True)
                with TabbedContent():
                    with TabPane('Brand view'):
                        yield self.brand_tree
                    with TabPane('ODM view'):
                        yield self.odm_tree
            with VerticalScroll(id='result-area'):
                with TabbedContent():
                    with TabPane('Device data'):
                        yield self.device_data_area
                    with TabPane('Regulatory data'):
                        yield self.regulatory_data_area
                    with TabPane('Additional chips'):
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

                brands = []
                chips = []
                chip_vendors = []
                odms = []

                for t in tokens:
                    identifier, value = t.split('=', maxsplit=1)
                    if identifier == 'brand':
                        brands.append(value.lower())
                    elif identifier == 'odm':
                        odms.append(value.lower())
                    elif identifier == 'chip':
                        chips.append(value.lower())
                    elif identifier == 'chip_vendor':
                        chip_vendors.append(value.lower())

                self.brand_tree.build_tree(brands=brands)
                self.odm_tree.build_tree(brands=brands, odms=odms, chip_vendors=chip_vendors)

    def on_tree_tree_highlighted(self, event: Tree.NodeHighlighted[None]) -> None:
        pass

    def on_tree_node_selected(self, event: Tree.NodeSelected[None]) -> None:
        '''Display the reports of a node when it is selected'''
        if event.node.data is not None:
            self.device_data_area.update(Group(self.build_meta_report(event.node.data)))
            self.regulatory_data_area.update(Group(self.build_regulatory_report(event.node.data['regulatory'])))
            self.additional_chips_area.update(Group(self.build_additional_chips_report(event.node.data['additional_chips'])))
        else:
            self.device_data_area.update()
            self.regulatory_data_area.update()
            self.additional_chips_area.update()

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed[None]) -> None:
        pass

    @group()
    def build_additional_chips_report(self, results):
        if results:
            result_table = rich.table.Table('', '', title='', show_lines=True, show_header=False, expand=True)
            for r in results:
                result_table.add_row('Description', r['description'])
                result_table.add_row('Manufacturer', r['manufacturer'])
                result_table.add_row('Model', r['model'])
                result_table.add_row('Extra info', r['extra_info'])
            yield result_table
        else:
            yield "No additional chips"

    @group()
    def build_regulatory_report(self, result):
        if result:
            meta_table = rich.table.Table('', '', title='Regulatory', show_lines=True, show_header=False, expand=True)
            meta_table.add_row('FCC date', result['fcc_date'])
            meta_table.add_row('FCC ids', '\n'.join(result['fcc_ids']))
            meta_table.add_row('Industry Canada ids', '\n'.join(result['industry_canada_ids']))
            meta_table.add_row('US ids', '\n'.join(result['us_ids']))
            meta_table.add_row('WiFi certified', result['wifi_certified'])
            meta_table.add_row('WiFi date', result['wifi_certified_date'])
            yield meta_table

    @group()
    def build_meta_report(self, result):
        if result:
            meta_table = rich.table.Table('', '', title=result['title'], show_lines=True, show_header=False)
            meta_table.add_row('Brand', result['brand'])
            meta_table.add_row('Model', str(result['model']))
            if result['taglines']:
                taglines = "\n".join(result['taglines'])
                meta_table.add_row('Taglines', taglines)
            if result['flags']:
                flags = "\n".join(result['flags'])
                meta_table.add_row('Flags', flags)

            # then display the various information parts
            meta_table.add_row('Data', str(result))
            yield meta_table

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
