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

Example invocations:

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="ZyXEL X150N" --pretty=line --report=100
device: 'AboCom WR5506', reason='OEM model', match_type='exact'
```

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="Senao CAP4200AG" --report=10000 --pretty=line
device: 'Adtran Bluesocket BSAP-1925', reason='PCB id', match_type='exact'
device: 'AirTight Networks SS-300-AT-C-55', reason='FCC id', match_type='exact'
device: 'AirTight Networks SS-300-AT-C-55', reason='PCB id', match_type='exact'
device: 'PowerCloud Systems CAP324', reason='FCC id', match_type='exact'
device: 'WatchGuard AP100', reason='FCC id', match_type='exact'
device: 'WatchGuard AP100', reason='PCB id', match_type='exact'
device: 'WatchGuard AP200', reason='FCC id', match_type='exact'
device: 'WatchGuard AP200', reason='PCB id', match_type='exact'
```

```
$ python devicecode_cli.py find-nearest -d ~/git/devicecode-data/ --model="AboCom ARM904" --report=10000 --pretty=line
device: 'Hawking HWR54G', reason='FCC id', match_type='exact'
device: 'Soyo AWRO3101', reason='FCC id', match_type='exact'
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
