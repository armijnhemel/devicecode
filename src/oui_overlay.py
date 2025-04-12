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


@click.command(short_help='Create OUI overlay files to provide additional data')
@click.option('--manufacturer', '-m', 'manufacturer_file', required=True,
              help='Wireshark manufacturer file with OUI ids', type=click.File('r'))
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
def main(manufacturer_file, devicecode_directory, output_directory, use_git, wiki_type):
    if not output_directory.is_dir():
        raise click.ClickException(f"Directory {output_directory} is not a valid directory.")

    if not devicecode_directory.is_dir():
        raise click.ClickException(f"Directory {devicecode_directory} is not a valid directory.")

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

    ouis = {}
    for line in manufacturer_file:
        if line.startswith('#'):
            continue
        if line.startswith('00:00:00'):
            continue
        oui, manufacturer_short, manufacturer_full = line.strip().split(maxsplit=2)
        ouis[oui] = {'name_short': manufacturer_short, 'name': manufacturer_full}

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

    # Then walk all the result files, check the Wireshark OUI ids
    # and optionally create overlays
    for p in devicecode_dirs:
        devicecode_dir = p / 'devices'
        overlay_directory = output_directory / p.name / 'overlays'

        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r', encoding='utf-8') as wiki_file:
                    device = json.load(wiki_file)
                    if 'network' not in device:
                        continue

                    overlay_data = {'type': 'overlay', 'name': 'oui', 'source': 'wireshark',
                                    'license': 'GPL-2.0',
                                    'url': 'https://www.wireshark.org/download/automated/data/manuf'}
                    write_overlay = False
                    ethernet_oui_overlays = []
                    wireless_oui_overlays = []

                    for e in device['network']['ethernet_oui']:
                        orig_oui = e['oui']
                        if orig_oui not in ouis:
                            ethernet_oui_overlays.append(e)
                            continue
                        e['name'] = ouis[orig_oui].get('name', '')
                        e['name_short'] = ouis[orig_oui].get('name_short', '')
                        ethernet_oui_overlays.append(e)
                        write_overlay = True
                    for e in device['network']['wireless_oui']:
                        orig_oui = e['oui']
                        if orig_oui not in ouis:
                            wireless_oui_overlays.append(e)
                            continue
                        e['name'] = ouis[orig_oui].get('name', '')
                        e['name_short'] = ouis[orig_oui].get('name_short', '')
                        wireless_oui_overlays.append(e)
                        write_overlay = True

                    if write_overlay:
                        overlay_data['data'] = {'ethernet_oui': ethernet_oui_overlays, 'wireless_oui': wireless_oui_overlays}
                        overlay_file = overlay_directory / result_file.stem / 'network_oui.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w', encoding='utf-8') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))
                        if use_git:
                            # add the file
                            p = subprocess.Popen(['git', 'add', overlay_file],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be added", file=sys.stderr)

                            commit_message = f'Add OUI overlay for {result_file.stem}'

                            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be committed", file=sys.stderr)

            except json.decoder.JSONDecodeError:
                pass

if __name__ == "__main__":
    main()
