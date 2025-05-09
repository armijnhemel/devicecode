# DeviceCode Command Line Interface

To quickly inspect devices it is more efficient to use a specialized interface
instead of relying on tools such as `grep` and `less` to look at raw JSON
output.

Apart from the [Text User Interface (TUI)](tui.md) for interactive browsing of
results there is also a command line interface (CLI) that can be used to
quickly inspect the data.

## Dumping data

To quickly dump data the `dump` mode of the CLI can be used. A good use for
this is to find out the valid values in the data set, so they can be used in
the TUI, which (currently) cannot display the full list of values.

The following things can be displayed:

* `baudrate_jtag` - baud rate used for JTAG
* `baudrate_serial` - baud rate used for serial
* `bootloader` - name of the bootloader manufacturer (open source project,
   or commercial vendor)
* `cpeid` - CPE identifiers
* `cveid` - CVE identifiers
* `connector_jtag` - (on board) connector or solder pad for JTAG
* `connector_serial` - (on board) connector or solder pad for serial
* `fccid` - FCC identifiers
* `ip` - default IP address
* `jtag` - device has a JTAG port
* `login` - default login
* `odm` - name of the original design manufacturer (ODM)
* `odm_country` - ODM country
* `password` - default password
* `pcbid` - PCB identifier printed on the board
* `sdk` - name of Software Development Kit (SDK) that was used
* `serial` - device has a serial port

in a variety of formats:

* `line` - deduplicated, one line per value
* `list` - a deduplicated list of values
* `counter` - deduplicated, one line per value, with frequency count, most
  common value printed first
* `json` - deduplicated, JSON version of name plus frequency count

For example:

```
$ python devicecode_cli.py dump -d ~/git/devicecode-data/ --value=cve --pretty=counter
```

## Finding nearest devices

Finding the nearest device, or a set of nearest devices, given a device, is a
very powerful feature, as it is a lot easier to reason about a device if you
have more information available. For example, if you know that a device is very
close to a device with a known vulnerability, then that device could
potentially also be affected by that vulnerability. Finding close devices is
therefore a good method for triaging.

For exact matches it is likely that some of these are identical:

1. known ODM model - some devices are simply rebranded. The closest devices
   are then the other devices with the same ODM and model.
2. main FCC identifier - if devices have the same FCC identifier, then they
   tend to be the exact same device, plus or minus perhaps some extras like a
   harddisk, or a different colour casing. Each FCC identifier in the data set
   has a `type` associated with it: `main` for the main FCC id (for the
   specific device), `auxiliary` for peripherals with a separate FCC id, such
   as Mini-PCI cards for WiFi, or `unknown` for when it isn't clear. Only FCC
   identifiers with type `main` are useful.
3. PCB id - although vendors could potentially use the same PCB id as other
   vendors they typically don't.

Other things to look at to decide if devices are similar:

1. SDK version - most software choices are not made by the ODM, but by the
   chipset vendor. If any errors are in the software provided by the chipset
   vendor, then these are likely in more devices made with that SDK.
2. ODM and chipset
3. software fingerprint - files, programs, packages
4. partition layout

These can be looked at in isolation, but also be combined to give more reliable
results: especially for weak results this makes sense. For example, if there is
a single partition name that devices have in common it doesn't say much, but if
it is made by the same OEM, with the same chip, then the case for devices being
similar becomes stronger.

OEM match example:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="ZyXEL X150N" --report=100
Matching device found: 'AboCom WR5506' with 1 criteria
 - OEM model, match type: exact
```

FCC id match example:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="AboCom ARM904" --report=10000
Matching device found: 'Hawking HWR54G' with 1 criteria
 - FCC id, match type: exact

Matching device found: 'Soyo AWRO3101' with 1 criteria
 - FCC id, match type: exact
```

PCB id match example:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="Senao CAP4200AG" --report=10000
Matching device found: 'Adtran Bluesocket BSAP-1925' with 1 criteria
 - PCB id, match type: exact

Matching device found: 'AirTight Networks SS-300-AT-C-55' with 2 criteria
 - FCC id, match type: exact
 - PCB id, match type: exact

Matching device found: 'PowerCloud Systems CAP324' with 1 criteria
 - FCC id, match type: exact

Matching device found: 'WatchGuard AP100' with 2 criteria
 - FCC id, match type: exact
 - PCB id, match type: exact

Matching device found: 'WatchGuard AP200' with 2 criteria
 - FCC id, match type: exact
 - PCB id, match type: exact
```

SDK and partitions match example:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="TP-LINK TL-WA901ND v1.x" --report=100
Matching device found: 'TP-LINK TL-WA901ND v2.x' with 3 criteria
 - FCC id, match type: exact
 - SDK, match type: possible
 - partitions, match type: possible

Matching device found: 'TP-LINK TL-WA901ND v3.x' with 2 criteria
 - SDK, match type: possible
 - partitions, match type: possible

Matching device found: 'TP-LINK TL-WA901ND v4.x' with 2 criteria
 - SDK, match type: possible
 - partitions, match type: possible
```

Some CVE information is printed, if available:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ -m "Tenda A18" --report=10000
Matching device found: 'Rock space RSD0607' with 1 criteria
 - FCC id, match type: exact

Matching device found: 'Rock space RSD0608' with 1 criteria
 - FCC id, match type: exact

Matching device found: 'Tenda A15' with 1 criteria
 - FCC id, match type: exact, CVEs: CVE-2024-0531, CVE-2024-0532, CVE-2024-0533, CVE-2024-0534

Matching device found: 'Tenda Mesh3s' with 1 criteria
 - FCC id, match type: exact
```

## Searching devices using a filter

With the same filtering language as used in the TUI it is possible to search
for devices with the CLI. Output formats currently supported are:

* `compact` - list of model names of devices
* `compact-json` - list of model names of devices in JSON
* `json` - list with device information (full device data)

For example:

```
$ python devicecode_cli.py search -d ~/git/devicecode-data/ --filter=" brand=asus cve=yes" --pretty=compact
ASUS RT-AC86U (1.40)
ASUS RT-AX55
ASUS RT-AX56U V2 (B1)
ASUS RT-AX88U A1
ASUS RT-N12+ B1
```

For more information about the filtering language read the
[filtering language documentation](filter.md).
