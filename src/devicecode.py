#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
import pathlib
import sys

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click
import mwparserfromhell

import devicecode_defaults as defaults

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

                for c in child.childNodes:
                    if c.nodeName == 'text':
                        # grab the wiki text and parse it. This data
                        # is in the <text> element
                        wiki_text = c.childNodes[0].data
                        wikicode = mwparserfromhell.parse(wiki_text)

                        # walk the elements in the parsed wiki text.
                        # Kind of assume a fixed order here.
                        # There are different elements in the Wiki text:
                        #
                        # * headings
                        # * templates
                        # * text
                        # * tags
                        #
                        # These could all contain interesting information

                        for f in wikicode.filter(recursive=False):
                            if isinstance(f, mwparserfromhell.nodes.heading.Heading):
                                # the heading itself doesn't contain data that
                                # needs to be stored, but it provides insights of what
                                # information follows as content
                                pass
                            elif isinstance(f, mwparserfromhell.nodes.template.Template):
                                if f.name.strip() == 'TIDTOC':
                                    # this element contains no interesting information
                                    continue
                                if wiki_type == 'TechInfoDepot':
                                    if f.name == 'Infobox Embedded System\n':
                                        # The "Infobox" is the most interesting item
                                        # on a page, containing hardware information.
                                        #
                                        # The information is stored in so called "parameters".
                                        # These parameters consist of one or more lines,
                                        # separated by a newline. The first line always
                                        # contains the identifier and '=', followed by a
                                        # value. Subsequent lines are values belonging to
                                        # the same identifier.

                                        for param in f.params:
                                            if '=' in param:
                                                # some elements are a list, the first one
                                                # will always contain the identifier
                                                param_elems = param.strip().split('\n')
                                                identifier, value = param_elems[0].split('=', maxsplit=1)

                                                param_values = []

                                                # remove superfluous spaces
                                                identifier = identifier.strip()
                                                param_values.append(value.strip())
                                                for p in param_elems[1:]:
                                                    param_values.append(p.strip())

                                                for p in param_values:
                                                    # determine if the value is one of the
                                                    # default values that can be skipped
                                                    is_default = False

                                                    for default_value in defaults.DEFAULT_VALUE.get(identifier, []):
                                                        if p == default_value:
                                                            is_default = True
                                                            break

                                                    if is_default or p == '':
                                                        continue

                                                    if debug:
                                                        # print values, but only if they aren't already
                                                        # skipped. This is useful for discovering default
                                                        # values and variants.
                                                        print(identifier, p, file=sys.stderr)




if __name__ == "__main__":
    main()
