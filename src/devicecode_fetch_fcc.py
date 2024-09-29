#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import datetime
import hashlib
import json
import pathlib
import re
import sys
import time

import click
import requests

# FCC ids can only consist of letters, numbers and hyphens
RE_FCC_ID = re.compile(r'[\w\d\-]+$')
RE_DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')

# time in seconds to sleep in "gentle mode"
SLEEP_INTERVAL = 2

TIMEOUT = 60

@click.command(short_help='Download FCC documents')
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--fcc-grantees', '-g', 'grantees',
              help='file with known FCC grantee codes',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('--verbose', is_flag=True, help='be verbose')
@click.option('--force', is_flag=True, help='always force downloads')
@click.option('--gentle', is_flag=True, help=f'pause {SLEEP_INTERVAL} seconds between downloads')
@click.option('--no-pdf', is_flag=True, help='do not download PDFs, just metadata')
@click.option('--no-download', is_flag=True,
              help='do not download any data, only reprocess already downloaded data')
def main(fccids, output_directory, grantees, verbose, force, gentle, no_pdf, no_download):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.", file=sys.stderr)
        sys.exit(1)

    fcc_grantees = {}
    if grantees is not None:
        with open(grantees, 'r') as grantee:
            try:
                fcc_grantees = json.load(grantee)
            except json.decoder.JSONDecodeError:
                pass
    ids = []

    for fccid in fccids:
        # TODO: more sanity checks here, like length, or perhaps limit
        # it to known FCC ids found in the various Wikis
        if RE_FCC_ID.match(fccid) is None:
            print(f"Invalid FCC id '{fccid}', skipping.", file=sys.stderr)
            continue

        if fcc_grantees:
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

    # store possible invalid FCC ids
    fcc_id_404 = []
    fcc_id_invalid = []
    downloaded_documents = 0
    processed_fccids = 0

    # Loop over all FCC ids to download the index file and PDF
    # files, compute SHA256 checksums of the PDF files and extract
    # some metadata.
    #
    # In case all data has already been downloaded and the
    # descriptions.json format changes, there is no need to
    # redownload data and --no-download can be used to process
    # the already downloaded data.
    for fcc_id in ids:
        try:
            store_directory = output_directory/fcc_id
            if not no_download:
                # grab stuff from fcc report
                if verbose:
                    print(f"Downloading main page for {fcc_id}")
                request = requests.get(f'{base_url}/FCC-ID/{fcc_id}',
                                       headers=headers, timeout=TIMEOUT)

                # now first check the headers to see if it is OK to do more requests
                if request.status_code != 200:
                    if request.status_code == 401:
                        print("Denied by fcc.report, exiting", file=sys.stderr)
                        sys.exit(1)
                    elif request.status_code == 404:
                        # record entries that are not available
                        fcc_id_404.append(fcc_id)
                    elif request.status_code == 500:
                        print("Server error, exiting", file=sys.stderr)
                        sys.exit(1)
                    continue

                result = request.text
                if result == '':
                    continue
            if no_download:
                if (store_directory / 'index.html').exists():
                    with open((store_directory / 'index.html'), 'r') as index_html:
                        result = index_html.read()
                else:
                    continue

            # now process the results. Parse, grab the names of
            # the PDFs plus descriptions, then download the PDFs and
            # store the results, along with the description in a simple
            # tag/value format, in JSON.

            pdfs_descriptions = []
            in_table = False
            is_modular = False
            pdf_name = ''
            description = ''
            document_type = ''
            approved_dates = []
            failed_dates = []
            current_date = ''
            for line in result.splitlines():
                # keep a bit of state and only look at the interesting lines.
                # This is a bit ugly but hey, it works.
                if '<span class="label label-success">APPROVED</span>' in line:
                    res = RE_DATE.search(line)
                    if res:
                        approved_dates.append(res.groups()[0])
                if '<span class="label label-danger">FAILED</span>' in line:
                    res = RE_DATE.search(line)
                    if res:
                        failed_dates.append(res.groups()[0])
                if '<th>File Name</th><th>Document Type</th>' in line:
                    in_table = True
                    document_type = line.rsplit('<td>', maxsplit=1)[1][:-5]
                    description = line.rsplit('<td>', maxsplit=1)[0][:-9].rsplit('>', maxsplit=1)[1]
                    continue
                if not in_table:
                    continue

                if fcc_id in line and line.startswith('</tr>') and pdf_name == '':
                    # get the document_type and description
                    document_type = line.rsplit('<td>', maxsplit=1)[1][:-5]
                    description = line.rsplit('<td>', maxsplit=1)[0][:-9].rsplit('>', maxsplit=1)[1]
                elif line.startswith('<td>'):
                    # first extract the date
                    try:
                        current_date = datetime.datetime.strptime(line[4:-5], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    if '.pdf' in line:
                        # extract the file name
                        _, pdf_name, _ = line.split('"', maxsplit=2)
                        pdf_basename = pdf_name.rsplit('/', maxsplit=1)[1]
                        if 'modular' in description.lower():
                            is_modular = True
                        elif 'module request' in description.lower():
                            is_modular = True
                        elif 'module approval' in description.lower():
                            is_modular = True

                        # store the pdf/description combination
                        pdfs_descriptions.append({'url': f'{base_url}/{pdf_name}',
                                                  'name': pdf_basename, 'type': document_type,
                                                  'description': description, 'date': current_date})

                        # reset the pdf name
                        pdf_name = ''

            if not pdfs_descriptions:
                fcc_id_invalid.append(fcc_id)
                continue

            if not no_download:
                # create the subdirectory, use the FCC id as a path component
                store_directory.mkdir(parents=True, exist_ok=True)

                with open(store_directory/'index.html', 'w') as output:
                    output.write(result)

                # now download the individual PDF files and write them
                # to the directory for this FCC entry

                if not no_pdf:
                    for pdf in pdfs_descriptions:
                        # verify if there already was data downloaded for this
                        # particular device by checking the contents of the result first
                        # and skipping it there were no changes.
                        if not force and (store_directory/pdf['name']).exists():
                            continue

                        if verbose:
                            print(f"* downloading {pdf['url']}")
                        if gentle:
                            time.sleep(SLEEP_INTERVAL)
                        request = requests.get(pdf['url'], headers=headers, timeout=TIMEOUT)

                        with open(store_directory/pdf['name'], 'wb') as output:
                            output.write(request.content)
                        downloaded_documents += 1

            pdfs_descriptions = sorted(pdfs_descriptions, key=lambda x: x['date'])
            # compute SHA256 of any PDF files that were downloaded. This
            # is regardless of the --no-pdf option was given (as that
            # might have been used just to update the metadata).
            for pdf in pdfs_descriptions:
                # verify if there already was data downloaded for this
                # particular device by checking the contents of the result first
                # and skipping it there were no changes.
                if (store_directory/pdf['name']).exists():
                    with open(store_directory/pdf['name'], 'rb') as pdf_file:
                        pdf['sha256'] = hashlib.sha256(pdf_file.read()).hexdigest()

            description_data = {'modular': is_modular, 'data': pdfs_descriptions}

            if not approved_dates and failed_dates:
                approved_dates = failed_dates

            if verbose:
                print(f"* writing PDF/description mapping for {fcc_id}\n")
            with open(store_directory/'descriptions.json', 'w') as output:
                output.write(json.dumps(description_data, indent=4))
            with open(store_directory/'approved_dates.json', 'w') as output:
                output.write(json.dumps(sorted(set(approved_dates)), indent=4))
            processed_fccids += 1

            if not no_download and gentle:
                time.sleep(SLEEP_INTERVAL)

        except Exception:
            pass

    if verbose:
        print("Statistics")
        print(f"* processed {processed_fccids} FCC ids")
        print(f"* downloaded {downloaded_documents} documents\n")
        if fcc_id_invalid:
            print("Possibly invalid FCC identifiers")
            for f in fcc_id_invalid:
                print(f"* {f}\n")


if __name__ == "__main__":
    main()
