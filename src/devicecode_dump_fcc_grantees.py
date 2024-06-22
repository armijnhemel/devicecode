#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import pathlib
import sys

# import XML processing that guards against several XML attacks
import defusedxml.minidom

import click

@click.command(short_help='Dump known FCC grantees')
@click.option('--input', '-i', 'input_file', required=True,
              help='FCC grantee dump file',
              type=click.Path('r', path_type=pathlib.Path))
def main(input_file):
    # load XML
    with open(input_file, encoding='ISO-8859-1') as fcc_dump:
        fcc_xml = defusedxml.minidom.parse(fcc_dump)

    # walk the XML and print the extracted grantee code
    for p in fcc_xml.getElementsByTagName('grantee_code'):
        print(p.childNodes[0].data)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
