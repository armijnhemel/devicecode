#!/usr/bin/env python3

# Copyright Armijn Hemel
# Licensed under Apache 2.0, see LICENSE file for details
# SPDX-License-Identifier: Apache-2.0

import csv
import pathlib
import sys
import time
from collections import namedtuple

import click
import requests

# time in seconds to sleep in "gentle mode"
SLEEP_INTERVAL = 2

TIMEOUT = 60

@click.command(short_help='Download OpenWrt pages')
@click.option('--output', '-o', 'output_directory', required=True,
              help='top level output directory, data will be stored in a subdirectory',
              type=click.Path(path_type=pathlib.Path, exists=True))
@click.option('--toh', '-t', 'toh', required=True,
              help='OpenWrt table of hardware CSV dump', type=click.File('r'))
@click.option('--verbose', is_flag=True, help='be verbose')
@click.option('--force', is_flag=True, help='always force downloads')
@click.option('--gentle', is_flag=True, help=f'pause {SLEEP_INTERVAL} seconds between downloads')
def main(output_directory, toh, verbose, force, gentle):
    openwrt_404 = []
    downloaded_openwrt_devices = 0

    # set a User Agent for each user request. This is just to be nice
    # for the people that are running the website, and identify that
    # connections were made using a script, so they can block in case
    # the script is misbehaving. I don't want to hammer their website.
    user_agent_string = "DeviceCode-OpenWrtTOHCrawler/0.1"
    headers = {'user-agent': user_agent_string,
              }

    # the OpenWrt CSV dump has 74 fields, but only a few
    # are (currently) interesting (see documentation in doc/ )
    OpenWrtDevice = namedtuple('OpenWrtDevice', 'pid, devicetype, brand, model, version, fccid, availability, whereavailable, supportedsincecommit, supportedsincerel, supportedcurrentrel, unsupported_functions, target, subtarget, packagearchitecture, bootloader, cpu, cpucores, cpumhz, flashmb, rammb, ethernet100mports, ethernetgbitports, ethernet1gports, ethernet2_5gports, ethernet5gports, ethernet10gports, sfp_ports, sfp_plus_ports, switch, vlan, modem, commentsnetworkports, wlanhardware, wlan24ghz, wlan50ghz, wlancomments, wlandriver, detachableantennas, bluetooth, usbports, sataports, commentsusbsataports, videoports, audioports, phoneports, commentsavports, serial, serialconnectionparameters, jtag, ledcount, buttoncount, gpios, powersupply, devicepage, device_techdata owrt_forum_topic_url, lede_forum_topic_url, forumsearch, gitsearch, wikideviurl, oemdevicehomepageurl, firmwareoemstockurl, firmwareopenwrtinstallurl, firmwareopenwrtupgradeurl, firmwareopenwrtsnapshotinstallurl, firmwareopenwrtsnapshotupgradeurl, installationmethods, commentinstallation, recoverymethods, commentrecovery, picture, comments, page')
    csv_reader = csv.reader(toh, dialect='excel-tab')
    is_first_line = True
    for line in csv_reader:
        if is_first_line:
            is_first_line = False
            continue

        owrt = OpenWrtDevice._make(line)
        if not owrt.page.startswith('toh:hwdata:'):
            continue

        owrt_grab_url = f"https://openwrt.org/{owrt.page}?do=export_raw"

        try:
            if not force:
                if (output_directory/owrt.page).exists():
                    if verbose:
                        print(f"Skipping download of {owrt.page}")
                    continue
            # grab stuff from OpenWrt
            if verbose:
                print(f"Downloading {owrt.page}")
            request = requests.get(owrt_grab_url, headers=headers, timeout=TIMEOUT)

            # now first check the headers to see if it is OK to do more requests
            if request.status_code != 200:
                if request.status_code == 401:
                    print("Denied by OpenWrt website, exiting", file=sys.stderr)
                    sys.exit(1)
                elif request.status_code == 404:
                    # record entries that are not available
                    openwrt_404.append(owrt.page)
                elif request.status_code == 500:
                    print("Server error, exiting", file=sys.stderr)
                    sys.exit(1)
                continue

            result = request.text
            if result == '':
                continue

            with open(output_directory/owrt.page, 'w') as output:
                output.write(result)

            downloaded_openwrt_devices += 1

            if gentle:
                time.sleep(SLEEP_INTERVAL)
        except:
            pass

    if verbose:
        print("Statistics")
        print(f"* downloaded {downloaded_openwrt_devices} pages\n")


if __name__ == "__main__":
    main()
