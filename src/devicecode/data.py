#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import json

def read_data_with_overlays(devicecode_directories, no_overlays):
    '''Read devicecode data and return devices with overlays applied'''
    devices, overlays = read_data(devicecode_directories, no_overlays)
    new_devices = []
    for device in devices:
        if 'title' not in device:
            continue

        # (optionally) apply overlays. This is done dynamically and
        # not during the start of the program, as overlays can be disabled
        # at run time.
        if device['title'] in overlays:
            for overlay in overlays[device['title']]:
                if overlay['name'] == 'fcc_id':
                    device['regulatory']['fcc_ids'] = overlay['data']
                elif overlay['name'] == 'cpe':
                    device['regulatory']['cpe'] = overlay['data']
                elif overlay['name'] == 'cve':
                    device['regulatory']['cve'] = overlay['data']
                elif overlay['name'] == 'oui':
                    device['network']['ethernet_oui'] = overlay['data']['ethernet_oui']
                    device['network']['wireless_oui'] = overlay['data']['wireless_oui']
                elif overlay['name'] == 'fcc_extracted_text':
                    device['fcc_data'] = overlay['data']
                elif overlay['name'] == 'brand':
                    device['brand'] = overlay['data']['brand']
        new_devices.append(device)

    return new_devices

def read_data(devicecode_directories, no_overlays):
    '''Read devicecode data and return devices and overlays per device'''
    devices = []
    overlays = {}

    # store device data and overlays
    for devicecode_dir in devicecode_directories:
        for result_file in devicecode_dir.glob('**/*'):
            if not result_file.is_file():
                continue
            try:
                with open(result_file, 'r', encoding='utf-8') as wiki_file:
                    device = json.load(wiki_file)
                    devices.append(device)
            except json.decoder.JSONDecodeError:
                pass

        overlays_directory = devicecode_dir.parent / 'overlays'
        if not no_overlays and overlays_directory.exists() and overlays_directory.is_dir():
            for result_file in overlays_directory.glob('**/*'):
                if not result_file.is_file():
                    continue
                device_name = result_file.parent.name
                if device_name not in overlays:
                    overlays[device_name] = []
                try:
                    with open(result_file, 'r', encoding='utf-8') as wiki_file:
                        overlay = json.load(wiki_file)
                        if 'type' not in overlay:
                            continue
                        if overlay['type'] != 'overlay':
                            continue
                        overlays[device_name].append(overlay)
                except json.decoder.JSONDecodeError:
                    pass
    return (devices, overlays)
