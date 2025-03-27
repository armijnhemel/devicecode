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

PART_TO_NAME = {'h': 'hardware', 'a': 'application',
                'o': 'operating system'}


@click.command(short_help='Create CPE & CVE (optional) overlay files to provide additional data')
@click.option('--cpe', '-c', 'cpe_file', required=True,
              help='CPE dictionary file', type=click.File('r'))
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--cve-directory', '-e', 'cve_directory',
              help='CVE list directory', type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
def main(cpe_file, devicecode_directory, output_directory, use_git, wiki_type, cve_directory):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if cve_directory and not cve_directory.is_dir():
        print(f"{cve_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if cve_directory and not (cve_directory / 'cves').exists():
        print(f"{cve_directory} is not a valid cvelistV5 directory, exiting.", file=sys.stderr)
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

    # https://nvd.nist.gov/general/FAQ-Sections/General-FAQs#faqLink7
    cpe_metadata = {'source': 'NVD', 'license': 'public domain',
                    'url': 'https://nvd.nist.gov/products/cpe'}

    # first process the CPE dictionary and store information
    ns = 'http://cpe.mitre.org/dictionary/2.0'
    titles_mod_to_title = {}
    cpe_title_to_cpe = {}
    product_page_to_title = {}

    for event, element in et.iterparse(cpe_file):
        if element.tag == f"{{{ns}}}generator":
            for child in element:
                if child.tag == f"{{{ns}}}timestamp":
                    cpe_metadata['timestamp'] = child.text
                elif child.tag == f"{{{ns}}}product_version":
                    cpe_metadata['product_version'] = child.text
                elif child.tag == f"{{{ns}}}schema_version":
                    cpe_metadata['schema_version'] = child.text

            # reduce memory usage
            element.clear()
        elif element.tag == f"{{{ns}}}cpe-item":
            cpe_name = element.attrib['name']
            if element.get('deprecated') == 'true':
                continue

            # only interesting for now: hardware, operating system and firmware
            if cpe_name.startswith('cpe:/h'):
                # skip firmware entries for now
                if '_firmware' in cpe_name:
                    # reduce memory usage
                    element.clear()
                    continue
                parsed_cpe = cpe.CPE(cpe_name)
            elif '_firmware' in cpe_name:
                # reduce memory usage
                element.clear()
                continue
                parsed_cpe = cpe.CPE(cpe_name)
            else:
                # reduce memory usage
                element.clear()
                continue

            if parsed_cpe.is_hardware():
                title = ''
                cpe23 = ''
                references = []
                for child in element:
                    # first get the title. This is basically the CPE 2.2 name
                    # Please note: some entries can have multiple titles in multipe
                    # languages. TODO.
                    if child.tag == f"{{{ns}}}title":
                        title = child.text.strip()
                        titles_mod_to_title[title.lower().replace(' ', '')] = title.lower()

                    # then grab the CPE 2.3 name
                    if child.tag == "{http://scap.nist.gov/schema/cpe-extension/2.3}cpe23-item":
                        cpe23 = child.attrib['name']

                    # and the references
                    if child.tag == f"{{{ns}}}references":
                        for ch in child:
                            href = ch.attrib['href']
                            reference_type = ch.text.lower()
                            if reference_type in ['product']:
                                if not href in product_page_to_title:
                                    product_page_to_title[href] = title.lower()
                            references.append({'type': reference_type, 'href': href})

                if title:
                    cpe_title_to_cpe[title.lower()] = {'cpe': cpe_name, 'cpe23': cpe23,
                                                       'references': references, 'title': title,
                                                       'part': parsed_cpe.get_part()[0],
                                                       'vendor': parsed_cpe.get_vendor()[0],
                                                       'product': parsed_cpe.get_product()[0],
                                                       'version': parsed_cpe.get_version()[0],
                                                       'update': parsed_cpe.get_update()[0],
                                                       'edition': parsed_cpe.get_edition()[0],
                                                       'language': parsed_cpe.get_language()[0],
                                                       'software_edition': parsed_cpe.get_software_edition()[0],
                                                       'target_software': parsed_cpe.get_target_software()[0],
                                                       'target_hardware': parsed_cpe.get_target_hardware()[0],
                                                       'other': parsed_cpe.get_other()[0]}
            # reduce memory usage
            element.clear()

    # keep a mapping from CPE to a list of CVEs
    cpe_to_cve = {}

    # walk the CVE data, if it exists
    for p in (cve_directory / 'cves').walk():
        parent, directories, files = p
        for f in files:
            if f.startswith('CVE'):
                with open(parent / f, 'r') as cve_file:
                    try:
                        cve_json = json.load(cve_file)
                        if cve_json['cveMetadata']['state'] == 'REJECTED':
                            continue
                        for container in cve_json['containers'].get('adp', []):
                            for affected in container.get('affected', []):
                                for cve_cpe in affected['cpes']:
                                    # TODO: first rename. Example: d-link -> dlink
                                    # Use NAME_CORRECTION in the CPE dictionary for this
                                    if cve_cpe not in cpe_to_cve:
                                        cpe_to_cve[cve_cpe] = []
                                    cpe_to_cve[cve_cpe].append(cve_json['cveMetadata']['cveId'])
                    except json.decoder.JSONDecodeError:
                        continue

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

                    write_overlay = False

                    # first the obvious check: are the names the same?
                    if device['title'].lower() in cpe_title_to_cpe:
                        write_overlay = True
                        title = device['title'].lower()
                    else:
                        mod_title = device['title'].lower().replace(' ', '')
                        if mod_title in titles_mod_to_title:
                            title = titles_mod_to_title[mod_title]
                            #write_overlay = True

                    # see if product pages match
                    if not write_overlay:
                        for product_page in device['web']['product_page']:
                            # first direct match
                            if product_page in product_page_to_title:
                                title = product_page_to_title[product_page]
                                #write_overlay = True
                                break

                            # then check for both http and https differences
                            if product_page.startswith('http://'):
                                if product_page.replace('http://', 'https://') in product_page_to_title:
                                    title = product_page_to_title[product_page.replace('http://', 'https://')]
                                    #write_overlay = True
                                    break
                            elif product_page.startswith('https://'):
                                if product_page.replace('https://', 'http://') in product_page_to_title:
                                    title = product_page_to_title[product_page.replace('https://', 'http://')]
                                    #write_overlay = True
                                    break

                    if write_overlay and title in cpe_title_to_cpe:
                        cpe_data = cpe_title_to_cpe[title]

                        overlay_data['data'] = cpe_data
                        overlay_file = overlay_directory / result_file.stem / 'cpe.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))

                        # write CVE overlay file
                        if cpe_data['cpe23'] in cpe_to_cve:
                            cve_overlay_data = {'type': 'overlay', 'name': 'cve',
                                            'data': cpe_to_cve[cpe_data['cpe23']]}
                            cve_overlay_file = overlay_directory / result_file.stem / 'cve.json'
                            cve_overlay_file.parent.mkdir(parents=True, exist_ok=True)

                            with open(cve_overlay_file, 'w') as overlay:
                                overlay.write(json.dumps(cve_overlay_data, indent=4))

                        if use_git:
                            # add the files
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

                            if cpe_data['cpe23'] in cpe_to_cve:
                                p = subprocess.Popen(['git', 'add', overlay_file],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{cve_overlay_file} could not be added", file=sys.stderr)

                                commit_message = f'Add CVE overlay for {result_file.stem}'

                                p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{cve_overlay_file} could not be committed", file=sys.stderr)

            except json.decoder.JSONDecodeError:
                pass

if __name__ == "__main__":
    main()
