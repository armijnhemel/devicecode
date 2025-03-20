#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import os
import pathlib
import shutil
import subprocess
import sys

import click
import cpe

# import XML processing that guards against several XML attacks
import defusedxml.ElementTree as et


@click.command(short_help='Create CPE overlay files to provide additional data')
@click.option('--cpe', '-c', 'cpe_file', required=True,
              help='CPE dictionary file', type=click.File('r'))
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
def main(cpe_file, devicecode_directory, output_directory, use_git, wiki_type):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if use_git:
        if shutil.which('git') is None:
            print("'git' program not installed, exiting.", file=sys.stderr)
            sys.exit(1)

        cwd = os.getcwd()

        os.chdir(output_directory)

        # verify the output directory is a valid Git repository
        p = subprocess.Popen(['git', 'status', output_directory],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (outputmsg, errormsg) = p.communicate()
        if p.returncode == 128:
            print(f"{output_directory} is not a Git repository, exiting.", file=sys.stderr)
            sys.exit(1)

    # verify the directory names, they should be one of the following
    valid_directory_names = ['TechInfoDepot', 'WikiDevi', 'OpenWrt']

    # Inside these directories a directory called 'devices' should always
    # be present. Optionally there can be a directory called 'overlays'
    # with overlay files.

    devicecode_dirs = []
    for p in devicecode_directory.iterdir():
        if wiki_type:
            if p.name != wiki_type:
                continue

        if not p.is_dir():
            continue
        if not p.name in valid_directory_names:
            continue

        devices_dir = p / 'devices'
        if not (devices_dir.exists() and devices_dir.is_dir()):
            continue
        devicecode_dirs.append(p)

        # create the overlay directories
        overlay_directory = output_directory / p.name / 'overlays'
        overlay_directory.mkdir(exist_ok=True)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    cpe_title_to_cpe = {}

    # https://nvd.nist.gov/general/FAQ-Sections/General-FAQs#faqLink7
    cpe_metadata = {'source': 'NVD', 'license': 'public domain',
                    'url': 'https://nvd.nist.gov/products/cpe'}

    # first process the CPE dictionary and store information
    ns = 'http://cpe.mitre.org/dictionary/2.0'
    titles_mod_to_title = {}

    for event, element in et.iterparse(cpe_file):
        if element.tag == f"{{{ns}}}generator":
            for child in element:
                if child.tag == f"{{{ns}}}timestamp":
                    cpe_metadata['timestamp'] = child.text
                elif child.tag == f"{{{ns}}}product_version":
                    cpe_metadata['product_version'] = child.text
                elif child.tag == f"{{{ns}}}schema_version":
                    cpe_metadata['schema_version'] = child.text
        elif element.tag == f"{{{ns}}}cpe-item":
            cpe_name = element.attrib['name']

            # only interesting for now: hardware, operating system and firmware
            if cpe_name.startswith('cpe:/h'):
                # skip firmware entries for now
                if '_firmware' in cpe_name:
                    continue
                parsed_cpe = cpe.CPE(cpe_name)
            elif '_firmware' in cpe_name:
                continue
                parsed_cpe = cpe.CPE(cpe_name)
            else:
                continue

            if parsed_cpe.is_hardware():
                title = ''
                cpe23 = ''
                references = []
                for child in element:
                    # first get the title. This is basically the CPE 2.2 name
                    if child.tag == f"{{{ns}}}title":
                        title = child.text.strip()
                        titles_mod_to_title[title.lower().replace(' ', '')] = title.lower()

                    # then grab the CPE 2.3 name
                    if child.tag == "{{http://scap.nist.gov/schema/cpe-extension/2.3}}cpe23-item":
                        cpe23 = child.attrib['name']

                    # and the references
                    if child.tag == f"{{{ns}}}references":
                        for ch in child:
                            references.append({'type': ch.text.lower(), 'href': ch.attrib['href']})

                if title:
                    cpe_title_to_cpe[title.lower()] = {'name': cpe_name, 'cpe23': cpe23,
                                                       'references': references, 'title': title}

    # Then walk all the result files, check the names of the devices
    # and optionally create overlays
    for p in devicecode_dirs:
        devicecode_dir = p / 'devices'
        overlay_directory = output_directory / p.name / 'overlays'

        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)

                    overlay_data = {'type': 'overlay', 'name': 'cpe',
                                    'metadata': cpe_metadata}

                    # first the obvious check: are the names the same?
                    if device['title'].lower() in cpe_title_to_cpe:
                        cpe_data = {}
                        write_overlay = True
                    else:
                        mod_title = device['title'].lower().replace(' ', '')
                        if mod_title in titles_mod_to_title:
                            cpe_data = {}
                            write_overlay = True

                    write_overlay = False

                    if write_overlay:
                        overlay_file = overlay_directory / result_file.stem / 'cpe.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))
                        if use_git:
                            # add the file
                            p = subprocess.Popen(['git', 'add', overlay_file],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be added", file=sys.stderr)

                            commit_message = f'Add CPE overlay for {result_file.stem}'

                            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be committed", file=sys.stderr)

            except json.decoder.JSONDecodeError:
                pass

if __name__ == "__main__":
    main()
