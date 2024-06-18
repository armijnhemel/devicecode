#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse

import click
import requests

# FCC ids can only consist of letters, numbers and hyphens
RE_FCC_ID = re.compile(r'[\w\d\-]+$')

@click.command(short_help='Download FCC documents')
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument('fccids', required=True, nargs=-1)
@click.option('--debug', is_flag=True, help='enable debug logging')
def main(fccids, output_directory, debug):
    if not output_directory.is_dir():
        print(f"{output_directory} is not a directory, exiting.")
        sys.exit(1)

    ids = []

    for fccid in fccids:
        # TODO: more sanity checks here, like length, or perhaps limit
        # it to known FCC ids found in the various Wikis
        if RE_FCC_ID.match(fccid) is None:
            print(f"Invalid FCC id '{fccid}', skipping.", file=sys.stderr)
            continue
        ids.append(fccid)

        # create a subdirectory, use the FCC id as a path component
        store_directory = output_directory/fccid
        store_directory.mkdir(parents=True, exist_ok=True)

    if ids == []:
        print("No valid FCC ids found, exiting.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
