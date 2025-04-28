#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import csv
import datetime
import json
import os
import pathlib
import re
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
@click.option('--cve-directory', '-e', 'cve_directory', help='CVE list directory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--use-git', is_flag=True, help='use Git (not recommended, see documentation)')
@click.option('--wiki-type', type=click.Choice(['TechInfoDepot', 'WikiDevi', 'OpenWrt'],
              case_sensitive=False))
@click.option('--exploitdb', 'exploitdb', help='Exploit-DB results directory',
              type=click.Path(path_type=pathlib.Path, exists=True))
def main(cpe_file, devicecode_directory, output_directory, use_git, wiki_type, cve_directory,
         exploitdb):
    if not output_directory.is_dir():
        raise click.ClickException(f"Directory {output_directory} is not a valid directory.")

    if not devicecode_directory.is_dir():
        raise click.ClickException(f"Directory {devicecode_directory} is not a valid directory.")

    if cve_directory and not cve_directory.is_dir():
        raise click.ClickException(f"Directory {cve_directory} is not a valid directory.")

    is_cvelist5 = False
    is_fkie_cad_nvd = False
    if cve_directory and (cve_directory / 'cves').exists():
        is_cvelist5 = True
    elif cve_directory and (cve_directory / '_state.csv').exists():
        is_fkie_cad_nvd = True

    #if not (is_cvelist5 or is_fkie_cad_nvd):
    if not is_cvelist5:
        #print(f"{cve_directory} is not a valid cvelistV5 or FKIE-cad nvd directory, exiting.",
        print(f"{cve_directory} is not a valid cvelistV5 directory, exiting.",
              file=sys.stderr)
        sys.exit(1)

    if exploitdb and not exploitdb.is_dir():
        raise click.ClickException(f"Directory {exploitdb} is not a valid directory.")

    if exploitdb and not (exploitdb / 'files_exploits.csv').exists():
        print(f"{exploitdb} is not a valid Exploit-DB directory, exiting.", file=sys.stderr)
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
        overlay_directory.mkdir(parents=True, exist_ok=True)

    if not devicecode_dirs:
        print(f"No valid directories found in {devicecode_directory}, should contain one of {valid_directory_names}.", file=sys.stderr)
        sys.exit(1)

    # https://nvd.nist.gov/general/FAQ-Sections/General-FAQs#faqLink7
    cpe_metadata = {'source': 'NVD', 'license': 'public domain',
                    'url': 'https://nvd.nist.gov/products/cpe'}

    # first process the CPE dictionary and store information
    ns = 'http://cpe.mitre.org/dictionary/2.0'
    scap_ns = 'http://scap.nist.gov/schema/cpe-extension/2.3'
    titles_mod_to_title = {}
    cpe_title_to_cpe = {}
    product_page_to_title = {}

    cpe23_rewrite = {}

    # keep a mapping from CPE to a list of CVEs
    cpe_to_cve = {}

    # keep a mapping from device to a list of CVEs. This is for
    # devices for which there is no CPE, but for which a match
    # could be found using the title.
    device_title_to_cve = {}

    # keep a mapping from CPEs to a list of exploits (via CVEs)
    cpe_to_exploit = {}

    # a list of known CVE ids
    cve_ids = set()

    if cve_directory:
        if is_cvelist5:
            # parse the delta.json file for the time stamp
            delta_json = cve_directory / 'cves' / 'delta.json'
            if not delta_json.exists():
                print(f"{delta_json} is not a valid cvelistV5 delta file, exiting.", file=sys.stderr)
                sys.exit(1)
            with open(delta_json, 'r', encoding='utf-8') as cve_file:
                try:
                    cve_json = json.load(cve_file)
                except json.decoder.JSONDecodeError:
                    print(f"{delta_json} is not a valid cvelistV5 delta file, exiting.",
                          file=sys.stderr)
                    sys.exit(1)
                cve_metadata = {'timestamp': cve_json['fetchTime']}
        else:
            with open(cve_directory / '_state.csv', encoding='utf-8') as cve_csv:
                csv_reader = csv.reader(cve_csv)
                is_first_line = True
                latest_timestamp = None
                latest_timestamp_string = ''
                for line in csv_reader:
                    if is_first_line:
                        is_first_line = False
                        continue
                    timestamp = datetime.datetime.fromisoformat(line[4])
                    if not latest_timestamp:
                        latest_timestamp = timestamp
                        latest_timestamp_string = line[4]
                    elif latest_timestamp < timestamp:
                        latest_timestamp = timestamp
                        latest_timestamp_string = line[4]
                cve_metadata = {'timestamp': latest_timestamp_string}

        if is_cvelist5:
            cve_dir = cve_directory / 'cves'
        else:
            cve_dir = cve_directory

        # walk the CVE data, if it exists
        for p in cve_dir.walk():
            parent, _, files = p
            for f in files:
                if f.startswith('CVE'):
                    with open(parent / f, 'r', encoding='utf-8') as cve_file:
                        try:
                            cve_json = json.load(cve_file)
                            if cve_json['cveMetadata']['state'] == 'REJECTED':
                                continue
                            cve_ids.add(pathlib.Path(f).stem)
                        except json.decoder.JSONDecodeError:
                            continue

    cve_to_exploit = {}
    if exploitdb:
        with open(exploitdb / 'files_exploits.csv', encoding='utf-8') as exploits:
            csv_reader = csv.reader(exploits)
            is_first_line = True
            for line in csv_reader:
                if is_first_line:
                    is_first_line = False
                    continue
                exploit = line[1]
                cves = line[11].split(';')
                for cve in cves:
                    if re.match(r'CVE-\d{4}-\d{4,5}', cve):
                        if cve not in cve_to_exploit:
                            cve_to_exploit[cve] = set()
                        cve_to_exploit[cve].add(exploit)

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
            is_deprecated = False
            if element.get('deprecated') == 'true':
                is_deprecated = True

            # only interesting for now: hardware, operating system
            # and CPEs specific to firmware.
            if cpe_name.startswith('cpe:/h'):
                # skip firmware entries for now
                if '_firmware' in cpe_name:
                    # These entries are tricky, as it isn't always
                    # clear for which device they are meant. For example:
                    #
                    # cpe:/h:huawei:huawei_firmware:v5500r001c00
                    #
                    # or would require more parsing effort to find model and version number:
                    #
                    # cpe:/h:lenovo:thinkagile_mx650_v3_firmware:-
                    #
                    # or have spelling errors:
                    #
                    # cpe:/h:lenovo:thinkagile_mx630_v3_intergrated_system_firmware:-

                    # reduce memory usage
                    element.clear()
                    continue
                parsed_cpe = cpe.CPE(cpe_name)
            elif '_firmware' in cpe_name:
                # reduce memory usage
                element.clear()
                continue
                #parsed_cpe = cpe.CPE(cpe_name)
            else:
                # reduce memory usage
                element.clear()
                continue

            if parsed_cpe.is_hardware():
                cpe23 = ''
                references = []
                cves = []
                titles = set()
                for child in element:
                    # first get the title. This is basically the CPE 2.2 name
                    # Please note: some entries can have multiple titles in multipe
                    # languages and data is duplicated for every title.
                    if not is_deprecated and child.tag == f"{{{ns}}}title":
                        title = child.text.strip()
                        titles_mod_to_title[title.lower().replace(' ', '')] = title.lower()
                        titles.add(title)

                    # then grab the CPE 2.3 name
                    if child.tag == f'{{{scap_ns}}}cpe23-item':
                        cpe23 = child.attrib['name']
                        if is_deprecated:
                            # Sometimes the CPEs have been renamed because people used
                            # different/wrong names. Example: d-link -> dlink
                            # The CPE dictionary contains hints about which ones were renamed
                            # namely the NAME_CORRECTION attribute (but only for cpe23)
                            # As this is only used for rewriting CVEs (that *mostly* use the
                            # CPE 2.3 schema except entries from Red Hat) this is not a problem.
                            dep_child = child.find(f'{{{scap_ns}}}deprecation')
                            if dep_child is not None:
                                dep_rewrite = dep_child.find(f'{{{scap_ns}}}deprecated-by')
                                if dep_rewrite.attrib['type'] == 'NAME_CORRECTION':
                                    cpe23_rewrite[cpe23] = dep_rewrite.attrib['name']
                            break

                    # and the references
                    if child.tag == f"{{{ns}}}references":
                        for ch in child:
                            href = ch.attrib['href']
                            reference_type = ch.text.lower()
                            references.append({'type': reference_type, 'href': href})

                            # Then process advisories, as there are sometimes CVE
                            # identifiers or other identifiers in there. Please
                            # note that these references are not necessarily correct
                            # so cross correlate them with a list of known valid CVE
                            # ids, which will only work if all valid CVEs are known.
                            if 'advisory' in reference_type.lower():
                                # try to extract a known CVE identifier
                                cve_res = re.findall(r'CVE-\d{4}-\d{4,5}', href)
                                for c in sorted(set(cve_res)):
                                    if c in cve_ids:
                                        cves.append(c)

                for title in titles:
                    # sometimes titles are duplicated in the CPE data
                    # for some reason (usually data entry errors). Skip
                    # duplicates, although this might mean missing out
                    # on some data. This needs a much cleaner solution.
                    # TODO.
                    if title.lower() in cpe_title_to_cpe:
                        continue

                    for reference in references:
                        if reference['type'] in ['product']:
                            if not reference['href'] in product_page_to_title:
                                product_page_to_title[reference['href']] = title.lower()

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

                    if cves:
                        if cpe23 not in cpe_to_cve:
                            cpe_to_cve[cpe23] = []
                        cpe_to_cve[cpe23] += cves
                        for c in cves:
                            if c in cve_to_exploit:
                                if cpe23 not in cpe_to_exploit:
                                    cpe_to_exploit[cpe23] = []
                                cpe_to_exploit[cpe23] += cve_to_exploit[c]

            # reduce memory usage
            element.clear()

    if cve_directory:
        # walk the CVE data again. This adds some overhead
        # to the system, but since these scripts aren't run
        # very frequently it is probably OK.
        for p in (cve_directory / 'cves').walk():
            parent, _, files = p
            for f in files:
                if f.startswith('CVE'):
                    if pathlib.Path(f).stem not in cve_ids:
                        continue
                    with open(parent / f, 'r', encoding='utf-8') as cve_file:
                        try:
                            cve_json = json.load(cve_file)
                            for container in cve_json['containers'].get('adp', []):
                                for affected in container.get('affected', []):
                                    for cve_cpe in affected['cpes']:
                                        cpe23 = cpe23_rewrite.get(cve_cpe, cve_cpe)
                                        if cpe23 not in cpe_to_cve:
                                            cpe_to_cve[cpe23] = []
                                        cpe_to_cve[cpe23].append(cve_json['cveMetadata']['cveId'])
                            if 'cna' in cve_json['containers']:
                                for affected in cve_json['containers']['cna'].get('affected', []):
                                    if 'vendor' in affected and 'product' in affected:
                                        if affected['vendor'] != 'n/a' and affected['product'] != 'n/a':
                                            affected_title = f"{affected['vendor']} {affected['product']}"
                                            if affected_title not in device_title_to_cve:
                                                device_title_to_cve[affected_title] = []
                                            device_title_to_cve[affected_title].append(cve_json['cveMetadata']['cveId'])
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
                with open(result_file, 'r', encoding='utf-8') as wiki_file:
                    device = json.load(wiki_file)

                    overlay_data = {'type': 'overlay', 'name': 'cpe',
                                    'metadata': cpe_metadata}

                    write_overlay = False

                    # first the obvious check: are the names the same?
                    if device['title'].lower() in cpe_title_to_cpe:
                        title = device['title'].lower()
                        write_overlay = True
                    else:
                        # then check if the modified title (so without spaces) is the same
                        mod_title = device['title'].lower().replace(' ', '')
                        if mod_title in titles_mod_to_title:
                            title = titles_mod_to_title[mod_title]
                            write_overlay = True

                    # see if product pages match
                    if not write_overlay:
                        for product_page in device['web']['product_page']:
                            # first direct match
                            if product_page in product_page_to_title:
                                title = product_page_to_title[product_page]
                                write_overlay = True
                                break

                            # then check for both http and https versions
                            if product_page.startswith('http://'):
                                replaced = product_page.replace('http://', 'https://')
                            elif product_page.startswith('https://'):
                                replaced = product_page.replace('https://', 'http://')
                            else:
                                continue
                            if replaced in product_page_to_title:
                                title = product_page_to_title[replaced]
                                write_overlay = True
                                break

                    if write_overlay and title in cpe_title_to_cpe:
                        cpe_data = cpe_title_to_cpe[title]

                        overlay_data['data'] = cpe_data
                        overlay_file = overlay_directory / result_file.stem / 'cpe.json'
                        overlay_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(overlay_file, 'w', encoding='utf-8') as overlay:
                            overlay.write(json.dumps(overlay_data, indent=4))

                        if use_git:
                            # add the files
                            p = subprocess.Popen(['git', 'add', overlay_file],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be added", file=sys.stderr)

                            commit_message = f'Add CPE overlay for {result_file.stem}'

                            p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 close_fds=True)
                            (outputmsg, errormsg) = p.communicate()
                            if p.returncode != 0:
                                print(f"{overlay_file} could not be committed", file=sys.stderr)

                        cve_overlay_data = {}

                        # write CVE overlay file
                        if cpe_data['cpe23'] in cpe_to_cve:
                            cve_data = set(cpe_to_cve[cpe_data['cpe23']])
                            if device['title'] in device_title_to_cve:
                                cve_data.update( device_title_to_cve[device['title']])
                            cve_overlay_data = {'type': 'overlay', 'name': 'cve',
                                                'metadata': cve_metadata,
                                                'data': sorted(cve_data)}
                        elif device['title'] in device_title_to_cve:
                            cve_data = set(device_title_to_cve[device['title']])
                            cve_overlay_data = {'type': 'overlay', 'name': 'cve',
                                                'metadata': cve_metadata,
                                                'data': sorted(cve_data)}

                        if cve_overlay_data:
                            cve_overlay_file = overlay_directory / result_file.stem / 'cve.json'
                            cve_overlay_file.parent.mkdir(parents=True, exist_ok=True)

                            with open(cve_overlay_file, 'w', encoding='utf-8') as overlay:
                                overlay.write(json.dumps(cve_overlay_data, indent=4))

                            if use_git:
                                p = subprocess.Popen(['git', 'add', cve_overlay_file],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                     close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{cve_overlay_file} could not be added", file=sys.stderr)

                                commit_message = f'Add CVE overlay for {result_file.stem}'

                                p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                     close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{cve_overlay_file} could not be committed",
                                          file=sys.stderr)

                        exploit_overlay_data = {}

                        # write exploit overlay file
                        if cpe_data['cpe23'] in cpe_to_exploit:
                            exploits = set(cpe_to_exploit[cpe_data['cpe23']])
                            if device['title'] in device_title_to_cve:
                                cve_data = set(device_title_to_cve[device['title']])
                                for cve in cve_data:
                                    if cve in cve_to_exploit:
                                        exploits.update(cve_to_exploit[cve])
                            exploit_overlay_data = {'type': 'overlay', 'name': 'exploitdb',
                                                'data': sorted(exploits)}
                        else:
                            if device['title'] in device_title_to_cve:
                                cve_data = set(device_title_to_cve[device['title']])
                                exploits = set()
                                for cve in cve_data:
                                    if cve in cve_to_exploit:
                                        exploits.update(cve_to_exploit[cve])
                                if exploits:
                                    exploit_overlay_data = {'type': 'overlay', 'name': 'exploitdb',
                                                        'data': sorted(exploits)}

                        if exploit_overlay_data:
                            exploit_overlay_file = overlay_directory / result_file.stem / 'exploitdb.json'
                            exploit_overlay_file.parent.mkdir(parents=True, exist_ok=True)
                            with open(exploit_overlay_file, 'w', encoding='utf-8') as overlay:
                                overlay.write(json.dumps(exploit_overlay_data, indent=4))

                            if use_git:
                                p = subprocess.Popen(['git', 'add', exploit_overlay_file],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                     close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{exploit_overlay_file} could not be added", file=sys.stderr)

                                commit_message = f'Add Exploit-DB overlay for {result_file.stem}'

                                p = subprocess.Popen(['git', 'commit', "-m", commit_message],
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                     close_fds=True)
                                (outputmsg, errormsg) = p.communicate()
                                if p.returncode != 0:
                                    print(f"{exploit_overlay_file} could not be committed",
                                          file=sys.stderr)

            except json.decoder.JSONDecodeError:
                pass

if __name__ == "__main__":
    main()
