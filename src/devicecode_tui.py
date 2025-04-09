#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import pathlib
import sys
import webbrowser

from typing import Any

import click

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Markdown, Tree, TabbedContent, TabPane, Input, Header, DataTable

import devicecode.filter as devicecode_filter
from devicecode import dataset_composer
from devicecode import suggester as Suggester
from devicecode import defaults

PART_TO_NAME = {'h': 'hardware', 'a': 'application',
                'o': 'operating system'}


class BrandTree(Tree):

    def build_tree(self, brands_to_devices, is_filtered=False):
        '''Build the brand_tree given a collections of brands and devices.'''
        self.reset("DeviceCode brand results")
        for brand in sorted(brands_to_devices.keys(), key=str.casefold):
            # Add each brand as a node. Then add each model as a leaf.
            node = self.root.add(brand, data={'brand': brand}, expand=is_filtered)
            node_leaves = 0

            # Recurse into the devices and add nodes each device,
            # optionally with labels added to the name. Each valid leaf
            # node is decorated with the device data.
            for model in sorted(brands_to_devices[brand], key=lambda x: x['model']):
                if model['labels']:
                    node.add_leaf(f"{model['model']}  {''.join(model['labels'])}",
                                  data=model['data'])
                else:
                    node.add_leaf(f"{model['model']}", data=model['data'])
                node_leaves += 1
            node.label = f"{node.label}  ({node_leaves})"


class OdmTree(Tree):

    def build_tree(self, odm_to_devices, is_filtered=False):
        '''Build the odm_tree given a collections of ODMs, brands and devices.'''
        self.reset("DeviceCode OEM results")

        # add each manufacturer as a node. Then add each brand as a subtree
        # and each model as a leaf to the brand subtree.
        for odm in sorted(odm_to_devices.keys(), key=str.casefold):
            # create a node with brand subnodes
            node = self.root.add(odm, expand=is_filtered)
            node_leaves = 0
            for brand in sorted(odm_to_devices[odm], key=str.casefold):
                # Recurse into the devices and add nodes each device,
                # optionally with labels added to the name. Each valid leaf
                # node is decorated with the device data.
                brand_node = node.add(brand)
                brand_node_leaves = 0
                for model in sorted(odm_to_devices[odm][brand], key=lambda x: x['model']):
                    if model['labels']:
                        brand_node.add_leaf(f"{model['model']}  {''.join(model['labels'])}",
                                            data=model['data'])
                    else:
                        brand_node.add_leaf(f"{model['model']}", data=model['data'])
                    brand_node_leaves += 1
                    node_leaves += 1

                # Check if the brand node that was added actually has any leaf nodes.
                # If not, remove the brand node. This has to be done on the fly, as
                # due to any potential filtering this cannot be computed easily in
                # advance.
                if brand_node_leaves == 0:
                    brand_node.remove()
                else:
                    brand_node.label = f"{brand_node.label}  ({brand_node_leaves})"

            # check if there are any valid leaf nodes for the ODM (across all
            # the brands). If not, remove the ODM node.
            if node_leaves == 0:
                node.remove()
            node.label = f"{node.label}  ({node_leaves})"

class DevicecodeUI(App):
    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="Quit"),
    ]

    CSS_PATH = "devicecode_tui.css"

    def __init__(self, devices, overlays, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.devices = devices
        self.overlays = overlays

        # Create trees
        self.brand_tree: BrandTree[dict] = BrandTree("DeviceCode brand results")
        self.odm_tree: OdmTree[dict] = OdmTree("DeviceCode ODM results")

        # Create Markdown areas
        self.device_data_area = Markdown()
        self.regulatory_data_area = Markdown()
        self.model_data_area = Markdown()
        self.network_data_area = Markdown()
        self.serial_jtag_area = Markdown()
        self.software_area = Markdown()
        self.chips_area = Markdown()
        self.power_area = Markdown()
        self.fcc_area = Markdown()

        # Create the data tables
        self.brand_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.brand_cpu_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.brand_odm_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.odm_cpu_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.odm_connector_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.chip_vendor_connector_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')
        self.year_data_table: DataTable() = DataTable(fixed_columns=1, cursor_type='row')

        # first create a DatasetComposer object and populate it with
        # the full set of data (devices and overlays).
        self.dataset = dataset_composer.DatasetComposer(self.devices, self.overlays)

    def compose(self) -> ComposeResult:
        '''Compose the initial data set using all data.'''
        data = self.dataset.compose_data_sets()

        brands_to_devices = data['brands_to_devices']
        odm_to_devices = data['odm_to_devices']
        brand_data = data['brand_data']
        brand_odm = data['brand_odm']
        brand_cpu = data['brand_cpu']
        odm_cpu = data['odm_cpu']
        odm_connector = data['odm_connector']
        chip_vendor_connector = data['chip_vendor_connector']
        year_data = data['year_data']

        # Declare the data table column names
        self.brand_data_table.add_columns("rank", "count", "brand")
        self.brand_odm_data_table.add_columns("rank", "count", "brand", "ODM")
        self.brand_cpu_data_table.add_columns("rank", "count", "brand", "CPU brand")
        self.odm_cpu_data_table.add_columns("rank", "count", "ODM", "CPU brand")
        self.odm_connector_data_table.add_columns("rank", "count", "ODM", "connector")
        self.chip_vendor_connector_data_table.add_columns("rank", "count", "CPU", "connector")
        self.year_data_table.add_columns("rank", "count", "year")

        # Build the various datatables.
        brand_datatable_data = collections.Counter(brand_data)
        brand_odm_datatable_data = collections.Counter(brand_odm)
        brand_cpu_datatable_data = collections.Counter(brand_cpu)
        odm_cpu_datatable_data = collections.Counter(odm_cpu)
        odm_connector_data = collections.Counter(odm_connector)
        chip_vendor_connector_data = collections.Counter(chip_vendor_connector)
        year_datatable_data = collections.Counter(year_data)

        self.build_data_tables(brand_datatable_data, brand_odm_datatable_data,
                               brand_cpu_datatable_data, odm_cpu_datatable_data,
                               odm_connector_data, chip_vendor_connector_data, year_datatable_data)

        # build the various trees.
        self.brand_tree.show_root = False
        self.brand_tree.root.expand()
        self.brand_tree.build_tree(brands_to_devices)

        self.odm_tree.show_root = False
        self.odm_tree.root.expand()
        self.odm_tree.build_tree(odm_to_devices)

        # Create the input field. Use the data for the suggester and filter
        # validator so only valid known data can be entered in the input field.
        input_filter = Input(placeholder='Filter',
                    validators=[devicecode_filter.FilterValidator(data,
                                    token_names=defaults.TOKEN_NAMES)],
                    suggester=Suggester.SuggestDevices(defaults.TOKEN_NAMES, data,
                              case_sensitive=False),
                    valid_empty=True)

        # Yield all UI elements. The UI is a container with an app grid. On the
        # left there are tabs, each containing a tree. On the right there is an
        # area to display the results.
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
                    with TabPane('ODM/connector'):
                        with VerticalScroll():
                            yield self.odm_connector_data_table
                    with TabPane('CPU vendor/connector'):
                        with VerticalScroll():
                            yield self.chip_vendor_connector_data_table
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
                with TabPane('Regulatory, CPE, CVE & Commercial'):
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
        if event.validation_result and not event.validation_result.is_valid:
            return

        result = devicecode_filter.process_filter(event)

        is_filtered = result['is_filtered']

        data = self.dataset.compose_data_sets(result)

        # Build the data trees. Depending on the value of 'is_filtered' the
        # trees will be unfolded (if a filter has been applied) or not (all
        # data is displayed, with or without overlays).
        self.brand_tree.build_tree(data['brands_to_devices'], is_filtered)
        self.odm_tree.build_tree(data['odm_to_devices'], is_filtered)

        # Build the various datatables.
        brand_datatable_data = collections.Counter(data['brand_data'])
        brand_odm_datatable_data = collections.Counter(data['brand_odm'])
        brand_cpu_datatable_data = collections.Counter(data['brand_cpu'])
        odm_cpu_datatable_data = collections.Counter(data['odm_cpu'])
        odm_connector_data = collections.Counter(data['odm_connector'])
        chip_vendor_connector_data = collections.Counter(data['chip_vendor_connector'])
        year_datatable_data = collections.Counter(data['year_data'])

        self.build_data_tables(brand_datatable_data, brand_odm_datatable_data,
                               brand_cpu_datatable_data, odm_cpu_datatable_data,
                               odm_connector_data, chip_vendor_connector_data, year_datatable_data)

        # Reset the data areas to get rid of old data that might have
        # been displayed for a device that was previously selected.
        self.reset_areas()

    def build_data_tables(self, brand_datatable_data, brand_odm_datatable_data,
                          brand_cpu_datatable_data, odm_cpu_datatable_data,
                          odm_connector_data, chip_vendor_connector_data, year_datatable_data):
        '''Clear and rebuild the data tables/'''
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

    def reset_areas(self):
        '''Reset the data areas to prevent old data being displayed.'''
        self.device_data_area.update('')
        self.regulatory_data_area.update('')
        self.model_data_area.update('')
        self.network_data_area.update('')
        self.serial_jtag_area.update('')
        self.software_area.update('')
        self.chips_area.update('')
        self.power_area.update('')
        self.fcc_area.update('')

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        # TODO: often terminals (such as MATE terminal in Fedora) will
        # already open a link when clicking on it, causing the link to be opened
        # multiple times. Is this desirable?
        for i in ['https://', 'http://']:
            if event.href.startswith(i):
                webbrowser.open(event.href)
                break

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
            self.fcc_area.update(self.build_fcc_report(event.node.data.get('fcc_data', {})))
        else:
            self.reset_areas()

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

            # CPE
            if result['regulatory']['cpe'] and result['regulatory']['cpe']['cpe']:
                new_markdown += "# CPE\n"
                new_markdown += "| | |\n|--|--|\n"
                new_markdown += f"|**CPE**|{result['regulatory']['cpe']['cpe']}|\n"
                new_markdown += f"|**CPE 2.3**|{result['regulatory']['cpe']['cpe23']}|\n"

                part_full_name = PART_TO_NAME[result['regulatory']['cpe']['part']]
                new_markdown += f"|**Part**|{result['regulatory']['cpe']['part']} ({part_full_name})|\n"

            # CVE
            if result['regulatory']['cve']:
                new_markdown += "# CVE\n"
                for c in sorted(result['regulatory']['cve']):
                    new_markdown += f"[{c}](<https://www.cve.org/CVERecord?id={c}>)\n"

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
        new_markdown = ''
        if result:
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

    def build_fcc_report(self, result):
        '''Construct Markdown with information from downloaded FCC reports'''
        new_markdown = ""
        base_url = 'https://fcc.report/FCC-ID'
        if result:
            for pdf in result:
                fcc_id = pdf['fcc_id']
                pdf_name = pdf['pdf']
                new_markdown += f"# [{pdf_name}](<{base_url}/{fcc_id}/{pdf_name}>): {pdf['type']} - {pdf['description']}\n"
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
            new_markdown += "# Operating system & Third party software\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**OS** |{ result['os']}\n"
            third_parties = ", ".join(result['third_party'])
            new_markdown += f"|**Third party software** | {third_parties}\n"
            #new_markdown += f"|**DD-WRT** |{ result['ddwrt']}\n"
            #new_markdown += f"|**Gargoyle** |{ result['gargoyle']}\n"
            #new_markdown += f"|**OpenWrt** |{ result['openwrt']}\n"
            #new_markdown += f"|**Tomato** |{ result['tomato']}\n"

            # SDK
            new_markdown += "# SDK\n"
            new_markdown += "| | |\n|--|--|\n"
            new_markdown += f"|**Name** |{ result['sdk']['name']}\n"
            new_markdown += f"|**Version** |{ result['sdk']['version']}\n"
            new_markdown += f"|**Vendor** |{ result['sdk']['vendor']}\n"

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
                    new_markdown += f"|{p['name']}|{p['file_type']}|{p['user']}|{p['group']}\n"
        return new_markdown

    def build_model_report(self, result):
        '''Construct Markdown with device model information'''
        # mapping of labels to names in result['model']
        labels_model = [
            ('Model', 'model'),
            ('Part number', 'part_number'),
            ('PCB id', 'pcb_id'),
            ('Revision', 'revision'),
            ('Serial number', 'serial_number'),
            ('Series', 'series'),
            ('Submodel', 'submodel'),
            ('Subrevision', 'subrevision'),
                 ]

        # mapping of labels to names in result['manufacturer']
        labels_manufacturer = [
            ('Manufacturer', 'name'),
            ('Country', 'country'),
            ('Model', 'model'),
            ('Revision', 'revision'),
                 ]

        new_markdown = ""
        if result:
            new_markdown += "# Model information\n"
            new_markdown += "| | |\n|--|--|\n"

            for label, name in labels_model:
                new_markdown += f"|**{label}** | {result['model'][name]}\n"

            new_markdown += "# ODM information\n"
            new_markdown += "| | |\n|--|--|\n"

            for label, name in labels_manufacturer:
                new_markdown += f"|**{label}** | {result['manufacturer'][name]}\n"

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

        # mapping of labels to names in result['power_supply']
        labels = [
            ('Brand', 'brand'),
            ('Model', 'model'),
            ('Revision', 'revision'),
            ('Style', 'style'),
            ('Country', 'country'),
            ('e-level', 'e_level'),
            ('Input amperage', 'input_amperage'),
            ('Input connector', 'input_connector'),
            ('Input current', 'input_current'),
            ('Input Hz', 'input_hz'),
            ('Input voltage', 'input_voltage'),
            ('Output amperage', 'output_amperage'),
            ('Output connector', 'output_connector'),
            ('Output current', 'output_current'),
            ('Output voltage', 'output_voltage'),
                 ]

        new_markdown = ''
        if result:
            new_markdown += "# Power Supply\n"
            new_markdown += "| | |\n|--|--|\n"
            for label, name in labels:
                new_markdown += f"|**{label}** | {result['power_supply'][name]}\n"
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

            origin_to_url = {'TechInfoDepot': 'https://techinfodepot.shoutwiki.com/wiki',
                             'WikiDevi': 'https://wikidevi.wi-cat.ru',
                             'OpenWrt': 'https://openwrt.org'}

            for origin in result['origins']:
                origin_url = origin_to_url.get(origin['origin'], '')
                if origin_url:
                    origin_data_url = f"<{origin_url}/{origin['data_url']}>"
                    new_markdown += f"{origin['origin']}|{origin_data_url}\n"

        return new_markdown

@click.command(short_help='Interactive DeviceCode result browser')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
@click.option('--no-overlays', is_flag=True, help='do not apply overlay data')
def main(devicecode_directory, wiki_type, no_overlays):
    if not devicecode_directory.is_dir():
        print(f"Directory {devicecode_directory} is not a valid directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    # verify the directory names, they should be one of the following
    valid_directories = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']

    # The wiki directories should have a fixed structure. There should
    # always be a directory 'devices' (with device data). Optionally there
    # can be a directory called 'overlays' with overlay files.
    # If present the 'squashed' directory will always be chosen and
    # the other directories will be ignored.
    squashed_directory = devicecode_directory / 'squashed' / 'devices'
    if squashed_directory.exists() and not wiki_type:
        devicecode_directories = [squashed_directory]
    else:
        devicecode_directories = []
        for p in devicecode_directory.iterdir():
            if not p.is_dir():
                continue
            if not p.name in valid_directories:
                continue
            if wiki_type:
                if p.name != wiki_type:
                    continue
            devices_dir = p / 'devices'
            if not (devices_dir.exists() and devices_dir.is_dir()):
                continue
            devicecode_directories.append(devices_dir)

    if not devicecode_directories:
        print(f"No valid directories found in {devicecode_directory}, should be one of {valid_directories}.", file=sys.stderr)
        sys.exit(1)

    devices = []
    overlays = {}

    # store device data and overlays
    for devicecode_dir in devicecode_directories:
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue
            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    devices.append(device)
            except json.decoder.JSONDecodeError:
                pass

        overlays_directory = devicecode_dir.parent / 'overlays'
        if not no_overlays and overlays_directory.exists() and overlays_directory.is_dir():
            for result_file in overlays_directory.glob('**/*'):
                if not result_file.is_file():
                    continue
                device_name = result_file.parent.name
                if device_name not in overlays:
                    overlays[device_name] = []
                try:
                    with open(result_file, 'r') as wiki_file:
                        overlay = json.load(wiki_file)
                        if 'type' not in overlay:
                            continue
                        if overlay['type'] != 'overlay':
                            continue
                        overlays[device_name].append(overlay)
                except json.decoder.JSONDecodeError:
                    pass

    app = DevicecodeUI(devices, overlays)
    app.run()

if __name__ == "__main__":
    main()
