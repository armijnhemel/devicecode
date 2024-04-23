#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
import pathlib

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click
import mwparserfromhell

@click.command(short_help='Process TechInfoDepot XML dump')
@click.option('--input', '-i', 'input_file', required=True,
              help='Wiki top level dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--output', '-o', 'output_file', required=True, help='JSON output file',
              type=click.File('w', lazy=False))
@click.option('--wiki-type', required=True,
              type=click.Choice(['TechInfoDepot', 'WikiDevi'], case_sensitive=False))
@click.option('--debug', is_flag=True, help='enable debug logging')
def main(input_file, output_file, wiki_type, debug):
    # load XML
    with open(input_file) as wiki_dump:
        wiki_info = defusedxml.minidom.parse(wiki_dump)

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


if __name__ == "__main__":
    main()
