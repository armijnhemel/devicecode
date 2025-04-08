#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

import copy

class DatasetComposer():
    def __init__(self, devices, overlays):
        # keep a full copy of the original data
        self.devices = devices
        self.overlays = overlays

    def compose_data_sets(self, use_overlays=True, **kwargs):
        '''Compose the data sets for devices for display, optionally filtered'''

        # Optional filters with data for devices that should
        # be shown or ignored. If these filters are all empty,
        # then the data set will be the full data (unfiltered).
        filter_baud_rates = kwargs.get('serial_baud_rates', [])
        filter_bootloaders = kwargs.get('bootloaders', [])
        filter_brands = kwargs.get('brands', [])
        filter_chips = kwargs.get('chips', [])
        filter_chip_types = kwargs.get('chip_types', [])
        filter_chip_vendors = kwargs.get('chip_vendors', [])
        filter_connectors = kwargs.get('connectors', [])
        filter_cves = kwargs.get('cves', [])
        filter_cveids = kwargs.get('cveids', [])
        filter_device_types = kwargs.get('types', [])
        filter_fccs = kwargs.get('fccs', [])
        filter_fccids = kwargs.get('fccids', [])
        filter_files = kwargs.get('files', [])
        filter_flags = kwargs.get('flags', [])
        filter_ignore_brands = kwargs.get('ignore_brands', [])
        filter_ignore_odms = kwargs.get('ignore_odms', [])
        filter_ignore_origins = kwargs.get('ignore_origins', [])
        filter_ips = kwargs.get('ips', [])
        filter_jtags = kwargs.get('jtags',[])
        filter_odms = kwargs.get('odms', [])
        filter_operating_systems = kwargs.get('operating_systems', [])
        filter_origins = kwargs.get('origins', [])
        filter_packages = kwargs.get('packages', [])
        filter_partitions = kwargs.get('partitions', [])
        filter_passwords = kwargs.get('passwords', [])
        filter_programs = kwargs.get('programs', [])
        filter_rootfs = kwargs.get('rootfs', [])
        filter_sdks = kwargs.get('sdks', [])
        filter_serials = kwargs.get('serials', [])
        filter_years = kwargs.get('years', [])

        # Data structures to store the (optionally filtered) data
        # mapping of brands to devices
        brands_to_devices = {}

        # mapping of odms to devices
        odm_to_devices = {}

        # known baud rates
        baud_rates = set()

        # known bootloaders
        bootloaders = set()

        # known brands
        brands = set()
        brand_data = []

        # known chips
        chips = set()

        # known chip types
        chip_types = set()

        # known chip vendors
        chip_vendors = set()

        # known serial/JTAG connectors
        connectors = set()

        # known CVE ids
        cveids = set()

        # known ODMS
        odms = set()

        # known FCC ids
        fcc_ids = set()

        # known files
        files = set()

        # known flags
        flags = set()

        # known default IP addresses
        ips = set()

        # known packages
        packages = set()

        # known partitions
        partitions = set()

        # known default passwords
        passwords = set()

        # known programs
        programs = set()

        # known rootfs
        rootfs = set()

        # known SDKs
        sdks = set()

        # known device_types
        device_types = set()

        # known years
        years = set()
        year_data = []

        # Extract useful data from each of the devices for quick
        # access when building the trees and the datatables.
        brand_odm = []
        brand_cpu = []
        odm_cpu = []
        odm_connector = []
        chip_vendor_connector = []

        # walk all the devices, (optionally) apply overlays
        # and determine if it needs end up in the data set
        # or if it should be filtered.
        for original_device in self.devices:
            if 'title' not in original_device:
                continue

            # first make a copy of the original data, so the original
            # data is not overwritten.
            device = copy.deepcopy(original_device)

            # (optionally) apply overlays. This is done dynamically and
            # not during the start of the program, as overlays can be disabled
            # at run time.
            if use_overlays and device['title'] in self.overlays:
                for overlay in self.overlays[device['title']]:
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

            if 'brand' not in device:
                continue

            brand_name = device['brand']

            # filter brands
            if filter_brands and brand_name.lower() not in [x[0] for x in filter_brands]:
                continue
            if filter_ignore_brands and brand_name.lower() in [x[0] for x in filter_ignore_brands]:
                continue

            # filter ODMs
            if device['manufacturer']['name'] == '':
                filter_manufacturer_name = "***unknown***"
            else:
                filter_manufacturer_name = device['manufacturer']['name'].lower()
            if filter_odms:
                if filter_manufacturer_name not in [x[0] for x in filter_odms]:
                    continue
            if filter_ignore_odms:
                if filter_manufacturer_name in [x[0] for x in filter_ignore_odms]:
                    continue

            # then filter various other things
            if filter_device_types:
                dev_types = [x[0] for x in filter_device_types]
                if not {x.lower() for x in device['device_types']}.intersection(dev_types):
                    continue
            if filter_flags:
                ff_flags = [x[0] for x in filter_flags]
                if not set(map(lambda x: x.lower(), device['flags'])).intersection(ff_flags):
                    continue
            if filter_passwords:
                if device['defaults']['password'] not in [x[0] for x in filter_passwords]:
                    continue
            if filter_bootloaders:
                f_bootloaders = [x[0] for x in filter_bootloaders]
                if device['software']['bootloader']['manufacturer'].lower() not in f_bootloaders:
                    continue
            if filter_jtags:
                if device['has_jtag'] not in [x[0] for x in filter_jtags]:
                    continue

                # Process the parameters. These only make sense if
                # there actually is a JTAG port.
                if device['has_jtag'] == 'yes':
                    show_node = True
                    for param_args in [x[1] for x in filter_jtags]:
                        pass
                    if not show_node:
                        continue
            if filter_operating_systems:
                if device['software']['os'].lower() not in [x[0] for x in filter_operating_systems]:
                    continue
            if filter_serials:
                if device['has_serial_port'] not in [x[0] for x in filter_serials]:
                    continue
            if filter_connectors:
                if device['serial']['connector'].lower() not in [x[0] for x in filter_connectors]:
                    continue
            if filter_baud_rates:
                if device['serial']['baud_rate'] not in [x[0] for x in filter_baud_rates]:
                    continue
            if filter_ips:
                if device['defaults']['ip'] not in [x[0] for x in filter_ips]:
                    continue
            if filter_cves:
                f_cves = [x[0] for x in filter_cves]
                if 'yes' in f_cves and 'no' in f_cves:
                    pass
                elif 'yes' in f_cves:
                    if not device['regulatory']['cve']:
                        continue
                else:
                    if device['regulatory']['cve']:
                        continue

            # first collect all the years that have been declared
            # in the data: FCC, wifi certified, release date
            declared_years = []
            if device['commercial']['release_date']:
                declared_years.append(int(device['commercial']['release_date'][:4]))

            for f in device['regulatory']['fcc_ids']:
                if f['fcc_date']:
                    if f['fcc_type'] in ['main', 'unknown']:
                        declared_years.append(int(f['fcc_date'][:4]))
            if device['regulatory']['wifi_certified_date']:
                declared_years.append(int(device['regulatory']['wifi_certified_date'][:4]))

            if filter_years:
                if not set(filter_years).intersection(declared_years):
                    continue

            if filter_cveids:
                f_cveids = [x[0] for x in filter_cveids]
                cv = [x.lower() for x in device['regulatory']['cve']]
                if not set(cv).intersection(f_cveids):
                    continue

            if filter_programs:
                show_node = False
                f_programs = [x[0] for x in filter_programs]
                if 'programs' in device['software']:
                    for prog in device['software']['programs']:
                        if prog['name'].lower() in f_programs:
                            show_node = True
                            break
                if not show_node:
                    continue

            if filter_files:
                show_node = False
                f_files = [x[0] for x in filter_files]
                if 'files' in device['software']:
                    for prog in device['software']['files']:
                        if prog['name'].lower() in f_files:
                            show_node = True
                            break
                if not show_node:
                    continue

            if filter_chips:
                show_node = False
                f_chips = [x[0] for x in filter_chips]
                for cpu in device['cpus']:
                    if cpu['model'].lower() in f_chips:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_chip_types:
                show_node = False
                f_chip_types = [x[0] for x in filter_chip_types]
                for cpu in device['cpus']:
                    if cpu['chip_type'].lower() in f_chip_types:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_chip_vendors:
                show_node = False
                f_chip_vendors = [x[0] for x in filter_chip_vendors]
                for cpu in device['cpus']:
                    if cpu['manufacturer'].lower() in f_chip_vendors:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_ignore_origins:
                show_node = True
                f_ignore_origins = [x[0] for x in filter_ignore_origins]
                for origin in device['origins']:
                    if origin['origin'].lower() in f_ignore_origins:
                        show_node = False
                        break
                if not show_node:
                    continue

            if filter_origins:
                show_node = False
                f_origins = [x[0] for x in filter_origins]
                for origin in device['origins']:
                    if origin['origin'].lower() in f_origins:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_packages:
                show_node = False
                f_packages = [x[0] for x in filter_packages]
                for package in device['software']['packages']:
                    if package['name'].lower() in f_packages:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_partitions:
                show_node = False
                f_partitions = [x[0] for x in filter_partitions]
                for partition in device['software']['partitions']:
                    if partition['name'].lower() in f_partitions:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_rootfs:
                show_node = False
                f_rootfs = [x[0] for x in filter_rootfs]
                for fs in device['software']['rootfs']:
                    if fs.lower() in f_rootfs:
                        show_node = True
                        break
                if not show_node:
                    continue

            if filter_sdks:
                f_sdks = [x[0] for x in filter_sdks]
                if device['software']['sdk']['name'].lower() not in f_sdks:
                    continue

            if filter_fccs:
                f_fccs = [x[0] for x in filter_fccs]
                if 'yes' in f_fccs and 'no' in f_fccs:
                    pass
                elif 'yes' in f_fccs:
                    if not device['regulatory']['fcc_ids']:
                        continue
                else:
                    if device['regulatory']['fcc_ids']:
                        continue

            if filter_fccids:
                show_node = False
                f_fccids = [x[0] for x in filter_fccids]
                for fcc_id in device['regulatory']['fcc_ids']:
                    if fcc_id['fcc_id'].lower() in f_fccids:
                        show_node = True
                        break
                if not show_node:
                    continue

            model = device['model']['model']
            if device['model']['revision'] != '':
                model += " "
                model += device['model']['revision']
            if device['model']['submodel'] != '':
                model += " "
                model += device['model']['submodel']
            if device['model']['subrevision'] != '':
                model += " "
                model += device['model']['subrevision']

            device_types.update(device['device_types'])

            # Compute the labels used in the leaves.
            labels = set()
            for f in device['flags']:
                # Telephone related
                if "voip" in f.lower() or 'telephone' in f.lower() or " phone" in f.lower():
                    labels.add(":phone:")
            for d in device['device_types']:
                # Telephone related
                if "voip" in d.lower() or 'telephone' in d.lower() or " phone" in d.lower():
                    labels.add(":phone:")
            if 'linux' in device['software']['os'].lower():
                # Linux (kernel) based.
                labels.add(":penguin:")
            if 'android' in device['software']['os'].lower():
                # Android. Should always include Linux?
                labels.add(":robot:")
            if 'fcc_data' in device:
                # Extracted FCC data is present. This might be a bit confusing as when
                # there is no FCC data, but there is an FCC id this label is not shown.
                labels.add("\U000024BB")

            # Store the manufacturer name. If it is empty
            # assign it a value.
            manufacturer_name = device['manufacturer']['name']
            if manufacturer_name == '':
                manufacturer_name = '***UNKNOWN***'

            if brand_name not in brands_to_devices:
                brands_to_devices[brand_name] = []

            brands_to_devices[brand_name].append({'model': model, 'data': device,
                                                  'labels': sorted(labels)})
            brands.add(brand_name.lower())
            brand_data.append(brand_name)

            years.update(declared_years)
            year_data += declared_years

            if manufacturer_name not in odm_to_devices:
                odm_to_devices[manufacturer_name] = {}
            if brand_name not in odm_to_devices[manufacturer_name]:
                odm_to_devices[manufacturer_name][brand_name] = []
            odm_to_devices[manufacturer_name][brand_name].append({'model': model, 'data': device,
                                                                  'labels': sorted(labels)})
            odms.add(manufacturer_name.lower())
            brand_odm.append((brand_name, manufacturer_name))

            if device['defaults']['ip'] != '':
                ips.add(device['defaults']['ip'])

            if device['defaults']['password'] != '':
                passwords.add(device['defaults']['password'])

            if device['software']['bootloader']['manufacturer'] != '':
                bootloaders.add(device['software']['bootloader']['manufacturer'].lower())

            if device['serial']['connector'] != '':
                connectors.add(device['serial']['connector'].lower())
                odm_connector.append((manufacturer_name, device['serial']['connector']))
            if device['serial']['baud_rate'] != 0:
                baud_rates.add(device['serial']['baud_rate'])

            for cpu in device['cpus']:
                cpu_vendor_name = cpu['manufacturer']
                chip_vendors.add(cpu_vendor_name.lower())
                if cpu['model'] != '':
                    chips.add(cpu['model'].lower())
                if cpu['chip_type'] != '':
                    chip_types.add(cpu['chip_type'].lower())
                brand_cpu.append((brand_name, cpu_vendor_name))
                odm_cpu.append((manufacturer_name, cpu_vendor_name))
                if device['serial']['connector'] != '':
                    chip_vendor_connector.append((cpu_vendor_name, device['serial']['connector']))

            for chip in device['network']['chips']:
                chip_vendor_name = chip['manufacturer']
                chip_vendors.add(chip_vendor_name.lower())

                if chip['model'] != '':
                    chips.add(chip['model'].lower())

            for chip in device['flash']:
                chip_vendor_name = chip['manufacturer']
                chip_vendors.add(chip_vendor_name.lower())

                if chip['model'] != '':
                    chips.add(chip['model'].lower())

            for fcc_id in device['regulatory']['fcc_ids']:
                fcc_ids.add(fcc_id['fcc_id'].lower())

            for cveid in device['regulatory']['cve']:
                cveids.add(cveid.lower())

            for package in device['software']['packages']:
                package_name = package['name'].lower()
                packages.add(package_name)

            for partition in device['software']['partitions']:
                partition_name = partition['name']
                partitions.add(partition_name.lower())

            for fs in device['software']['rootfs']:
                rootfs.add(fs.lower())

            if device['software']['sdk']:
                sdks.add(device['software']['sdk']['name'].lower())

            if 'programs' in device['software']:
                for prog in device['software']['programs']:
                    program_name = prog['name'].lower()
                    programs.add(program_name)

            if 'files' in device['software']:
                for f in device['software']['files']:
                    file_name = f['name'].lower()
                    files.add(file_name)

            brand_odm.append((brand_name, manufacturer_name))

            flags.update([x.casefold() for x in device['flags']])

        return {'brands_to_devices': brands_to_devices, 'odm_to_devices': odm_to_devices,
                'baud_rates': baud_rates, 'bootloaders': bootloaders, 'brands': brands,
                'brand_data': brand_data, 'chips': chips, 'chip_types': chip_types,
                'chip_vendors': chip_vendors, 'connectors': connectors, 'cveids': cveids,
                'odms': odms, 'fcc_ids': fcc_ids, 'files': files, 'flags': flags, 'ips': ips,
                'brand_odm': brand_odm, 'brand_cpu': brand_cpu, 'odm_cpu': odm_cpu,
                'odm_connector': odm_connector, 'chip_vendor_connector': chip_vendor_connector,
                'packages': packages, 'partitions': partitions, 'passwords': passwords,
                'programs': programs, 'rootfs': rootfs, 'sdks': sdks, 'types': device_types,
                'years': years, 'year_data': year_data}
