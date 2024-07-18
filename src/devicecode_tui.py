#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

from typing import Any

import click

from rich.console import Group, group
from rich.panel import Panel
from rich import print_json
import rich.table

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Footer, Markdown, Static, Tree, TabbedContent, TabPane, Input, Header
from textual.widgets.tree import TreeNode

#from textual.logging import TextualHandler

#logging.basicConfig(
    #level="NOTSET",
    #handlers=[TextualHandler()],
#)


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
        oem_to_devices = {}
        chip_vendors_to_devices = {}

        # process all the JSON files in the directory
        for result_file in self.devicecode_directory.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                     device = json.load(wiki_file)
                     brand_name = device['brand']
                     if brand_name not in brands_to_devices:
                         brands_to_devices[brand_name] = []
                     model = device['model']['model']
                     if device['model']['revision'] != '':
                         model += " "
                         model += device['model']['revision']
                     brands_to_devices[brand_name].append({'model': model})

                     manufacturer_name = device['manufacturer']['name']
                     if manufacturer_name == '':
                         manufacturer_name = '***UNKNOWN***'
                     if manufacturer_name not in oem_to_devices:
                         oem_to_devices[manufacturer_name] = {}
                     if brand_name not in oem_to_devices[manufacturer_name]:
                         oem_to_devices[manufacturer_name][brand_name] = []
                     oem_to_devices[manufacturer_name][brand_name].append({'model': model})
            except json.decoder.JSONDecodeError:
                pass

        # build the brand_tree.
        brand_tree: Tree[dict] = Tree("DeviceCode brand results")
        brand_tree.show_root = False
        brand_tree.root.expand()

        for brand in sorted(brands_to_devices.keys(), key=str.casefold):
            # add each brand as a node. Then add each model as a leaf.
            node = brand_tree.root.add(brand, expand=True)
            for model in sorted(brands_to_devices[brand], key=lambda x: x['model']):
                 model_node = node.add_leaf(model['model'])

        # build the oem_tree.
        oem_tree: Tree[dict] = Tree("DeviceCode OEM results")
        oem_tree.show_root = False
        oem_tree.root.expand()

        for manufacturer in sorted(oem_to_devices.keys(), key=str.casefold):
            # add each manufacturer as a node. Then add each brand as a subtree
            # and each model as a leaf TODO
            node = oem_tree.root.add(manufacturer, expand=True)
            for brand in sorted(oem_to_devices[manufacturer]):
                 brand_node = node.add(brand)
                 for model in sorted(oem_to_devices[manufacturer][brand], key=lambda x: x['model']):
                     model_node = brand_node.add_leaf(model['model'])

        # Create a table with the results. The root element will
        # not have any associated data with it.
        self.static_widget = Static(Group(self.build_meta_report(None)))

        # yield the elements. The UI is a container with an app grid. On the left
        # there are some tabs, each containing a tree. On the right there is a
        # an area to display the results.
        yield Header()
        with Container(id='app-grid'):
            with Container(id='left-grid'):
                with TabbedContent():
                    with TabPane('Brand view'):
                        yield brand_tree
                    with TabPane('OEM view'):
                        yield oem_tree
                    with TabPane('Filter view'):
                        yield Input(placeholder='Filter')
            with VerticalScroll(id='result-area'):
                yield self.static_widget

        # show the footer with controls
        footer = Footer()
        footer.ctrl_to_caret = False
        yield footer

    def on_tree_tree_highlighted(self, event: Tree.NodeHighlighted[None]) -> None:
        pass

    def on_tree_node_selected(self, event: Tree.NodeSelected[None]) -> None:
        '''Display the reports of a node when it is selected'''
        return
        if event.node.data is not None:
            self.static_widget.update(Group(self.build_meta_report(event.node.data)))
        else:
            self.static_widget.update()

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed[None]) -> None:
        pass

    @group()
    def build_meta_report(self, result):
        if result:
            meta_table = rich.table.Table('', '', title='Data', show_lines=True, show_header=False)
            meta_table.add_row('Path', '')
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
