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

@click.command(short_help='Create FCC overlay files to provide additional data')
@click.option('--directory', '-d', 'devicecode_directory',
              help='DeviceCode results directory', required=True,
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, overlays will be stored in a subdirectory called \'overlay\'',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--fcc-grantees', '-g', 'grantees', required=True,
              help='file with known FCC grantee codes',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--report-only', '-r', is_flag=True, help='report only')
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
def main(devicecode_directory, output_directory, grantees, report_only, use_git):
    if not report_only and not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    if not devicecode_directory.is_dir():
        print(f"{devicecode_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    fcc_grantees = {}
    with open(grantees, 'r') as grantee:
        try:
            fcc_grantees = json.load(grantee)
        except json.decoder.JSONDecodeError:
            pass

    if use_git:
        if shutil.which('git') is None:
            print("'git' program not installed, exiting.", file=sys.stderr)
            sys.exit(1)

        os.chdir(output_directory)

        # verify the output directory is a valid Git repository
        p = subprocess.Popen(['git', 'status', output_directory],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (outputmsg, errormsg) = p.communicate()
        if p.returncode == 128:
            print(f"{output_directory} is not a Git repository, exiting.", file=sys.stderr)
            sys.exit(1)

    # verify the directory names, they should be one of the following:
    valid_directory_names = ['TechInfoDepot', 'WikiDevi']
    processed_fcc_directory = devicecode_directory / 'FCC'

    # Inside these directories a directory called 'devices' should always
    # be present. Optionally there can be a directory called 'overlays'
    # with overlay files.

    devicecode_dirs = []
    for p in devicecode_directory.iterdir():
        if not p.is_dir():
            continue
        if not p.name in valid_directory_names:
            continue
        devices_dir = p / 'devices'
        if not (devices_dir.exists() and devices_dir.is_dir()):
            continue
        devicecode_dirs.append(p)

        if not report_only:
            overlay_directory = output_directory / p.name / 'overlays'
            overlay_directory.mkdir(parents=True, exist_ok=True)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    # Then walk all the result files, check the FCC ids and optionally create overlays
    for p in devicecode_dirs:
        devicecode_dir = p / 'devices'
        overlay_directory = output_directory / p.name / 'overlays'
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue

            try:
                with open(result_file, 'r') as wiki_file:
                    device = json.load(wiki_file)
                    if 'regulatory' not in device:
                        continue
                    fcc_ids = device['regulatory']['fcc_ids']
                    if not fcc_ids:
                        continue

                    fcc_id_overlay_data = {'type': 'overlay', 'name': 'fcc_id', 'source': 'fcc'}
                    write_fcc_id_overlay = False
                    overlay_fcc_ids = []

                    fcc_extract_text_overlay_data = {'type': 'overlay', 'name': 'fcc_extracted_text', 'source': 'fcc'}
                    write_fcc_extracted_text = False
                    overlay_fcc_extracted_text = []

                    for f in fcc_ids:
                        fcc_id = f['fcc_id']
                        fcc_date = f['fcc_date']
                        if fcc_date == '':
                            if report_only:
                                print(f"No FCC date defined for {fcc_id}")
                                continue

                        dates = []

                        # check if the FCC id is for the brand (meaning it is the main FCC id)
                        is_main_fcc = False
                        if fcc_id.startswith('2'):
                            grantee_code = fcc_id[:5]
                        else:
                            grantee_code = fcc_id[:3]

                        if grantee_code in fcc_grantees:
                            if device['brand'].lower() in fcc_grantees[grantee_code].lower():
                                is_main_fcc = True

                        grantee_name = fcc_grantees.get(grantee_code, '')

                        if (processed_fcc_directory / fcc_id).is_dir():
                            is_modular = False

                            # load the file with approved dates, if it exists
                            descriptions_file = processed_fcc_directory / fcc_id / 'descriptions.json'
                            if descriptions_file.exists():
                                with open(descriptions_file, 'r') as desc:
                                    descriptions = json.load(desc)

                                # check if the device ifself is a module
                                for d in device['device_types']:
                                    if 'module' in d.lower():
                                        is_modular = True
                                        break

                            approved_file = processed_fcc_directory / fcc_id / 'approved_dates.json'
                            if approved_file.exists():
                                with open(approved_file, 'r') as approved:
                                    dates += json.load(approved)

                                # if there is no date at all create an overlay with
                                # the earliest date defined as the FCC date.
                                if fcc_date == '':
                                    fcc_type = 'unknown'
                                    if is_main_fcc:
                                        if not is_modular and descriptions['modular']:
                                            # there is an extra module
                                            fcc_type = 'auxiliary'
                                        else:
                                            fcc_type = 'main'
                                    else:
                                        if not is_modular and descriptions['modular']:
                                            # there is an extra module
                                            fcc_type = 'auxiliary'
                                    if dates:
                                        overlay = {'fcc_date': dates[0], 'fcc_id': fcc_id,
                                                   'fcc_type': fcc_type, 'license': 'CC0-1.0',
                                                   'grantee': grantee_name}
                                    else:
                                        overlay = {'fcc_date': '', 'fcc_id': fcc_id,
                                                   'fcc_type': fcc_type, 'license': 'CC0-1.0',
                                                   'grantee': grantee_name}

                                    overlay_fcc_ids.append(overlay)
                                elif fcc_date not in dates:
                                    # possibly wrong date, fix in the overlay (TODO)
                                    # copy the existing data to the overlay data
                                    if is_main_fcc:
                                        if not is_modular and descriptions['modular']:
                                            # there is an extra module
                                            f['fcc_type'] = 'auxiliary'
                                        else:
                                            f['fcc_type'] = 'main'
                                    else:
                                        if not is_modular and descriptions['modular']:
                                            # there is an extra module
                                            f['fcc_type'] = 'auxiliary'
                                    if len(dates) == 1:
                                        f['fcc_date'] = dates[0]
                                    f['license'] = 'CC0-1.0'
                                    f['grantee'] = grantee_name
                                    overlay_fcc_ids.append(f)
                                else:
                                    # copy the existing data to the overlay data
                                    if is_main_fcc:
                                        if not is_modular and descriptions['modular']:
                                            # there is an extra module
                                            f['fcc_type'] = 'auxiliary'
                                        else:
                                            f['fcc_type'] = 'main'
                                    else:
                                        if descriptions['modular']:
                                            # there is an extra module
                                            f['fcc_type'] = 'auxiliary'
                                    f['license'] = 'CC0-1.0'
                                    f['grantee'] = grantee_name
                                    overlay_fcc_ids.append(f)
                                write_fcc_id_overlay=True

                            for d in descriptions['data']:
                                text_data_file = processed_fcc_directory / fcc_id / d['name'] / 'text.json'
                                if is_main_fcc:
                                    if text_data_file.exists():
                                        with open(text_data_file, 'r') as text_data:
                                            text_hints = json.load(text_data)
                                            overlay_fcc_extracted_text.append({'fcc_id': fcc_id, 'pdf': d['name'], 'type': d['type'], 'description': d['description'], 'hints': text_hints})
                                            write_fcc_extracted_text = True
                        else:
                            if report_only:
                                print(f"FCC data missing for {fcc_id}")
                                continue
                            # copy the existing data to the overlay data
                            if is_main_fcc:
                                f['fcc_type'] = 'main'
                                f['license'] = 'CC0-1.0'
                                f['grantee'] = grantee_name
                                write_fcc_id_overlay=True
                            overlay_fcc_ids.append(f)

                    if report_only:
                        write_fcc_id_overlay = False
                        write_fcc_extracted_text = False

                    if write_fcc_id_overlay:
                        fcc_id_overlay_data['data'] = overlay_fcc_ids
                        overlay_file = overlay_directory / result_file.stem / 'fcc_id.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(fcc_id_overlay_data, indent=4))
                        if use_git:
                            # add the file
                            p = subprocess.Popen(['git', 'add', overlay_file],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be added", file=sys.stderr)

                            commit_message = f'Add FCC overlay for {result_file.stem}'

                            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be committed", file=sys.stderr)

                    if write_fcc_extracted_text:
                        fcc_extract_text_overlay_data['data'] = overlay_fcc_extracted_text
                        overlay_file = overlay_directory / result_file.stem / 'fcc_extracted.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w') as overlay:
                            overlay.write(json.dumps(fcc_extract_text_overlay_data, indent=4))
                        if use_git:
                            # add the file
                            p = subprocess.Popen(['git', 'add', overlay_file],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be added", file=sys.stderr)

                            commit_message = f'Add FCC overlay for {result_file.stem}'

                            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be committed", file=sys.stderr)

            except json.decoder.JSONDecodeError:
                pass



if __name__ == "__main__":
    main()
