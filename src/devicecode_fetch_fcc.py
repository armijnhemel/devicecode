#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import re
import sys
import time

import click
import requests

# FCC ids can only consist of letters, numbers and hyphens
RE_FCC_ID = re.compile(r'[\w\d\-]+$')

# time in seconds to sleep in "gentle mode"
SLEEP_INTERVAL = 2

TIMEOUT = 60

@click.command(short_help='Download FCC documents')
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--fcc-grantees', '-g', 'grantees',
              help='file with known FCC grantee codes (one per line)',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('--verbose', is_flag=True, help='be verbose')
@click.option('--force', is_flag=True, help='always force downloads')
@click.option('--gentle', is_flag=True, help=f'pause {SLEEP_INTERVAL} seconds between downloads')
def main(fccids, output_directory, grantees, verbose, force, gentle):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    fcc_grantees = set()
    if grantees is not None:
        with open(grantees, 'r') as grantee:
            for g in grantee:
                fcc_grantees.add(g.strip())

    ids = []

    for fccid in fccids:
        # TODO: more sanity checks here, like length, or perhaps limit
        # it to known FCC ids found in the various Wikis
        if RE_FCC_ID.match(fccid) is None:
            print(f"Invalid FCC id '{fccid}', skipping.", file=sys.stderr)
            continue

        if fcc_grantees != set():
            if fccid.startswith('2'):
                grantee = fccid[:5].upper()
            else:
                grantee = fccid[:3].upper()
            if grantee not in fcc_grantees:
                print(f"Unknown grantee '{grantee}', skipping FCC id '{fccid}'.", file=sys.stderr)
                continue

        ids.append(fccid.upper())

    if not ids:
        print("No valid FCC ids found, exiting.", file=sys.stderr)
        sys.exit(1)

    # then download the data from one of the FCC clone sites.
    # It seems that fcc.report is the most useful one (least junk
    # on the website, and fairly easy to parse.
    base_url = 'https://fcc.report'

    # set a User Agent for each user request. This is just to be nice
    # for the people that are running the website, and identify that
    # connections were made using a script, so they can block in case
    # the script is misbehaving. I don't want to hammer their website.
    user_agent_string = "DeviceCode-FCCReportCrawler/0.1"
    headers = {'user-agent': user_agent_string,
              }

    # store 404s
    fcc_id_404 = []
    downloaded_documents = 0
    processed_fccids = 0

    for fccid in ids:
        # create a subdirectory, use the FCC id as a path component
        store_directory = output_directory/fccid
        store_directory.mkdir(parents=True, exist_ok=True)

        try:
            # grab stuff from fcc report
            if verbose:
                print(f"Downloading main page for {fccid}")
            request = requests.get(f'{base_url}/FCC-ID/{fccid}',
                                   headers=headers, timeout=TIMEOUT)

            # now first check the headers to see if it is OK to do more requests
            if request.status_code != 200:
                if request.status_code == 401:
                    print("Denied by fcc.report, exiting", file=sys.stderr)
                    sys.exit(1)
                elif request.status_code == 404:
                    # record entries that are not available
                    fcc_id_404.append(fccid)
                elif request.status_code == 500:
                    print("Server error, exiting", file=sys.stderr)
                    sys.exit(1)
                continue

            # now process the results. Parse, grab the names of
            # the PDFs plus descriptions, then download the PDFs and
            # store the results, along with the description in a simple
            # tag/value format, in JSON.
            result = request.text
            if result == '':
                continue

            pdfs_descriptions = []
            in_table = False
            pdf_name = ''
            description = ''
            for line in result.splitlines():
                # keep a bit of state and only look at the interesting lines.
                # This is a bit ugly but hey, it works.
                if '<th>File Name</th><th>Document Type</th>' in line:
                    in_table = True
                    description = line.rsplit('<td>', maxsplit=1)[1][:-5]
                    continue
                if not in_table:
                    continue

                if fccid in line and line.startswith('</tr>') and pdf_name == '':
                    # get the description
                    description = line.rsplit('<td>', maxsplit=1)[1][:-5]
                elif line.startswith('<td>') and '.pdf' in line:
                    # extract the file name
                    _, pdf_name, _ = line.split('"', maxsplit=2)
                    pdf_basename = pdf_name.rsplit('/', maxsplit=1)[1]

                    # store the pdf/description combination
                    pdfs_descriptions.append((f'{base_url}/{pdf_name}', pdf_basename, description))

                    # reset the pdf name
                    pdf_name = ''

            if not pdfs_descriptions:
                continue

            with open(store_directory/'index.html', 'w') as output:
                output.write(result)

            # now download the individual PDF files and write them
            # to the directory for this FCC entry

            for pdf_url, pdf_basename, _ in pdfs_descriptions:
                # verify if there already was data downloaded for this
                # particular device by checking the contents of the result first
                # and skipping it there were no changes.
                if not force and (store_directory/pdf_basename).exists():
                    continue

                if verbose:
                    print(f"* downloading {pdf_url}")
                if gentle:
                    time.sleep(SLEEP_INTERVAL)
                request = requests.get(pdf_url, headers=headers, timeout=TIMEOUT)

                with open(store_directory/pdf_basename, 'wb') as output:
                    output.write(request.content)
                downloaded_documents += 1

            if verbose:
                print(f"* writing PDF/description mapping for {fccid}\n")
            with open(store_directory/'descriptions.json', 'w') as output:
                output.write(json.dumps(pdfs_descriptions, indent=4))
            processed_fccids += 1

        except Exception:
            pass

    if verbose:
        print("Statistics")
        print(f"* processed {processed_fccids} FCC ids")
        print(f"* downloaded {downloaded_documents} documents\n")


if __name__ == "__main__":
    main()
