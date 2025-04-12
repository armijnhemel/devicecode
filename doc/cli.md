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

## Comparing devices

Finding the closest device, or a set of closest devices, given a device, is a
very powerful feature, as it is a lot easier to reason about a device if you
have more information available. For example, if you know that a device is very
close to a device with a known vulnerability, then that device could
potentially also be affected by that vulnerability. Finding close devices is
therefore a good method for triaging.

Devices tend to be the same have devices have the same:

1. main FCC identifier - if devices have the same FCC identifier, then they
   tend to be the exact same device, plus or minus perhaps some extras like a
   harddisk, or a different colour casing.
2. PCB id - although vendors could potentially use the same PCB id as other
   vendors they typically don't.

Other methods to decide if devices are similar:

1. SDK version - most software choices are not made by the ODM, but by the
   chipset vendor. If any errors are in the software provided by the chipset
   vendor, then these are likely in more devices made with that SDK.
2. ODM and chipset
3. similar software fingerprint: files, programs, packages

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
