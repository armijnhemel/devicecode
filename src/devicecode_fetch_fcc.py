#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import re
import sys

import click
import requests

# FCC ids can only consist of letters, numbers and hyphens
RE_FCC_ID = re.compile(r'[\w\d\-]+$')

@click.command(short_help='Download FCC documents')
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--fcc-grantees', '-g', 'grantees',
              help='file with known FCC grantee codes (one per line)',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('--debug', is_flag=True, help='enable debug logging')
@click.option('--force', is_flag=True, help='always force downloads')
def main(fccids, output_directory, grantees, debug, force):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.")
        sys.exit(1)

    fcc_grantees = set()
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
    base_url = 'https://fcc.report/'

    # set a User Agent for each user request. This is just to be nice
    # for the people that are running the website, and identify that
    # connections were made using a script, so they can block in case
    # the script is misbehaving. I don't want to hammer their website.
    user_agent_string = "FccReportCrawler/0.1"
    headers = {'user-agent': user_agent_string,
              }

    # store 404s
    fcc_id_404 = []

    for fccid in ids:
        # create a subdirectory, use the FCC id as a path component
        store_directory = output_directory/fccid
        store_directory.mkdir(parents=True, exist_ok=True)

        try:
            # grab stuff from fcc report
            request = requests.get(f'{base_url}/FCC-ID/{fccid}',
                                   headers=headers)

            # now first check the headers to see if it is OK to do more requests
            if request.status_code != 200:
                if request.status_code == 401:
                    print("Denied by fcc.report, exiting", file=sys.stderr)
                    sys.exit(1)
                elif request.status_code == 404:
                    # TODO: record entries that are not available
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

                    # store the pdf/description combination
                    pdfs_descriptions.append((pdf_name, description))

                    # reset the pdf name
                    pdf_name = ''

            if not pdfs_descriptions:
                continue

            with open(store_directory/'index.html', 'w') as output:
                output.write(result)

            # now download the individual PDF files and write them
            # to the directory for this FCC entry

            for pdf, description in pdfs_descriptions:
                # verify if there already was data downloaded for this
                # particular device by checking the contents of the result first
                # and skipping it there were no changes.
                pdf_basename = pdf.rsplit('/', maxsplit=1)[1]

                if not force and (store_directory/pdf_basename).exists():
                    continue

                request = requests.get(f'{base_url}/{pdf}',
                                       headers=headers)

                with open(store_directory/pdf_basename, 'wb') as output:
                    output.write(request.content)

            with open(store_directory/'descriptions.json', 'w') as output:
                output.write(json.dumps(pdfs_descriptions))


        except Exception as e:
            #print(e)
            pass


if __name__ == "__main__":
    main()