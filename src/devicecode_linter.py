#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import sys

import click

# import XML processing that guards against several XML attacks
import defusedxml.minidom

@click.command(short_help='Check and report old data no longer present in the XML dump')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--input', '-i', 'input_file', required=True,
              help='Wiki top level dump file',
              type=click.Path('r', path_type=pathlib.Path))
@click.option('--remove', is_flag=True, help='remove old files (WARNING! BE CAREFUL!)')
@click.option('--wiki-type', required=True,
              type=click.Choice(['TechInfoDepot', 'WikiDevi'], case_sensitive=False))
def main(devicecode_directory, input_file, wiki_type, remove):
    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    # load XML
    with open(input_file) as wiki_dump:
        wiki_info = defusedxml.minidom.parse(wiki_dump)

    devices_dir = devicecode_directory / wiki_type / 'devices'
    originals_dir = devicecode_directory / wiki_type / 'original'

    if not devices_dir.exists() and not devices_dir.is_dir():
        print(f"{devices_dir} is not a valid directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not originals_dir.exists() and not originals_dir.is_dir():
        print(f"{originals_dir} is not a valid directory, exiting.", file=sys.stderr)
        sys.exit(1)

    known_titles = set()

    # now walk the XML. It depends on the dialect (WikiDevi, TechInfoDepot)
    # how the contents should be parsed, as the pages are laid out in
    # a slightly different way.
    #
    # Each device is stored in a separate page.
    for p in wiki_info.getElementsByTagName('page'):
        title = ''

        # Walk the child elements of the page
        for child in p.childNodes:
            if child.nodeName == 'title':
                # first store the title of the page but skip
                # special pages such as 'Category' pages
                # (TechInfoDepot only)
                title = child.childNodes[0].data
                if title.startswith('Category:'):
                    break
                if title.startswith('List of '):
                    break

            elif child.nodeName == 'ns':
                # devices can only be found in namespace 0 in both
                # techinfodepot and wikidevi.
                namespace = int(child.childNodes[0].data)
                if namespace != 0:
                    break

                known_titles.add(title)

    old_devices = []
    for devices_file in devices_dir.glob('**/*'):
        if devices_file.stem not in known_titles:
            # as an extra sanity check read the JSON and extract the title
            with open(devices_file, 'r') as json_file:
                device_data = json.load(json_file)
                if device_data['title'] not in known_titles:
                    old_devices.append(devices_file.name)

    for old_device in sorted(old_devices):
        print(f"Old device file: {old_device}")
        if remove:
            originals_file = (originals_dir/old_device).with_suffix('.xml')
            print(f"removing {devices_dir/old_device}")
            print(f"removing {originals_file}\n")
            (devices_dir/old_device).unlink()
            originals_file.unlink()


if __name__ == "__main__":
    main()
