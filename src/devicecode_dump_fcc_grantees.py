#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click

@click.command(short_help='Dump known FCC grantees')
@click.option('--input', '-i', 'input_file', required=True,
              help='FCC grantee dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--output', '-o', 'output_file', required=True,
              help='output file', type=click.File('w'))
def main(input_file, output_file):
    # load XML
    with open(input_file, encoding='ISO-8859-1') as fcc_dump:
        fcc_xml = defusedxml.minidom.parse(fcc_dump)

    grantees = {}

    # walk the XML and print the extracted grantee code
    for p in fcc_xml.getElementsByTagName('Row'):
        for ch in p.childNodes:
            if ch.nodeName == 'grantee_code':
                grantee_code = ch.childNodes[0].data
            elif ch.nodeName == 'grantee_name':
                grantees[grantee_code] = ch.childNodes[0].data


    # dump results as JSON
    output_file.write(json.dumps(grantees, indent=4))

if __name__ == "__main__":
    main()
