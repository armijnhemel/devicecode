#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

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
def main(fccids, output_directory, grantees, debug):
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

        # create a subdirectory, use the FCC id as a path component
        store_directory = output_directory/fccid
        store_directory.mkdir(parents=True, exist_ok=True)

    if not ids:
        print("No valid FCC ids found, exiting.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
