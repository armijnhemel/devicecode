# DeviceCode Command Line Interface

To quickly inspect devices it is more efficient to use a specialized interface
instead of relying on tools such as `grep` and `less` to look at raw JSON
output.

Apart from the [Text User Interface (TUI)](tui.md) for interactive browsing of
results there is also a command line interface (CLI) that can be used to
quickly inspect the data.

## Dumping data

To quickly dump data the `dump` mode of the CLI can be used. Several things can
be displayed:

* `baudrate_jtag` - baud rate used for JTAG
* `baudrate_serial` - baud rate used for serial
* `cveids` - CVE identifiers
* `connector_jtag` - (on board) connector or solder pad for JTAG
* `connector_serial` - (on board) connector or solder pad for serial
* `pcbid` - PCB identifier printed on the board

in a variety of formats:

* `line` - deduplicated, one line per value
* `list` - a deduplicated list of values
* `counter` - deduplicated, one line per value, with frequency count, most
  common value printed first

```
$ python devicecode_cli.py dump -d ~/git/devicecode-data/ --value=cve --pretty=counter
```


For more information about the filtering language read the
[filtering language documentation](filter.md).
