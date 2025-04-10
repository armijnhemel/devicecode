# Filtering language

The filtering language is fairly simple with statements and (implicit)
operators (for combining results).

## Statements

Statements resemble bash shell commands and exports and are of the form:

```
name=value
```

In the future this will be extended to allow extra parameters (which will be
different for each field):

```
name?params=value
```

`params` are as follows:

```
param1:value1;param2:value2
```

`name` can be one of:

* `baud`
* `bootloader`
* `brand`
* `chip`
* `chip_type`
* `chip_vendor`
* `connector`
* `cpe`
* `cve`
* `cveid`
* `fccid`
* `file`
* `flag`
* `ignore_brand`
* `ignore_odm`
* `ignore_origin`
* `ip`
* `jtag`
* `odm`
* `origin`
* `overlay`
* `os`
* `package`
* `partition`
* `password`
* `pcbid`
* `program`
* `rootfs`
* `sdk`
* `serial`
* `type`
* `year`

Both names and values are case insensitive.

A name can appear multiple times. Multiple instances with the same name should
be interpreted as "OR". Instances with a different name should be interpreted
as "AND". As an example:

```
odm=edimax odm=accton
```

should be read as:

```
odm=edimax OR odm=accton
```

and return results where either of those two values is true.

```
odm=edimax brand=asus
```

should be read as:

```
odm=edimax AND brand=asus
```

Combining the two:

```
odm=edimax odm=accton brand=asus
```

should be read as:

```
(odm=edimax OR odm=accton) AND brand=asus
```

or even more complex combinations, such as:

```
brand=asus brand=cisco odm=arcadyan odm=edimax brand=netgear brand=sitecom chip_vendor=ralink
```

which should be read as:

```
(brand=asus OR brand=cisco OR brand=netgear OR brand=sitecom) AND (odm=arcadyan OR odm=edimax) AND chip_vendor=ralink
```

In case there are special characters or spaces, then these can be quoted, for
example:

```
brand="Banana Pi"
```

### Baud rate

`baud` can be used to filter on the baud rate of the serial port (if present).

### Bootloader

`bootloader` can be used to filter on bootloader.

### Brand

There are two ways to filter brands:

1. use the `brand` statement to show devices from one or more brands
2. use the `ignore_brand` statement to hide devices from one or more brands

### Chip type

Currently `chip_type` can only be used to show the type of the main CPU in one
or more devices.

### Chip vendor

Currently `chip_vendor` can only be used to show the main CPU in one or more
devices.

### Connector

`connector` can be used to filter connectors (serial port only for now, JTAG
in the future as well).

### CPE

`cpe` can be used to show devices that have, or don't have, an associated CPE.
Valid values are `yes` and `no`.

### CVE

`cve` can be used to show devices that have, or don't have, an associated CVE.
Valid values are `yes` and `no`.

### CVE id

`cveid` can be used to show devices associated with a certain CVE identifier.

### FCC id

`fccid` can be used to show devices associated with a certain FCC identifier.

### File

`file` can be used to show devices with certain files.

### Flag

`flag` can be used to show devices with certain flags.

### IP

`ip` can be used to show devices using a certain default IP address (for
example `192.168.1.1`).

### ODM

There are two ways to filter ODMs:

1. use the `odm` statement to show devices made by one or more ODMs
2. use the `ignore_odm` statement to hide devices made by one or more ODMs

### Default operating system

`os` can be used to show the default operating system that is installed on
the device.

### Origin

There are two ways to filter origins (OpenWrt, TechInfoDepot, WikiDevi)::

1. use the `origin` statement to show devices for which there is information
   defined in that specific wiki
2. use the `ignore_origin` statement to hide devices for which there is
   information defined in that specific wiki

For example, to show devices that are in OpenWrt, but not in WikiDevi use:

`origin=openwrt ignore_origin=wikidevi`

### Overlay

`overlay` can be used to disable showing any overlays as sometimes it is
interesting to only show the "pure" data from the Wiki. Overlays can be
disabled as follows:

`overlays=off`

The only valid value for this flag is `off`.

Please note: this will only work if there actually are any overlays. In the
current `squashed` data set all overlays have already been applied (this will
be changed in the future) so there it doesn't have any effect.

### Serial

`serial` can be used to show if a device has a serial port, or if it is not
known. Valid values are `yes`, `no` and `unknown`.

### JTAG

`jtag` can be used to show if a device has a JTAG port, or if it is not
known. Valid values are `yes`, `no` and `unknown`.

### Package

`package` can be used to show devices containing the package. Package
information is currently extracted from parsing boot logs.

### Partition

`partition` can be used to show devices where the Linux kernel commandline
has certain name for a partition (for example: `u-boot-env` or `nvram`).

### Password

Currently `password` can only be used to show devices with one or more default
passwords.

### pcbid

`pcbid` can be used to show devices with a certain PCB id.

### Program

`program` can be used to show devices containing specific program names as
extracted from output of the `ps` command.

### root file system type

`rootfs` can be used to show devices where the Linux kernel has support for
having the root file system on a certain file system type (such as `squashfs`
or `jffs2`).

### SDK

`sdk` can be used to show devices with references to a certain SDK, such as
`LSDK` (Atheros and Qualcomm Atheros).

### Year

`year` can be used to show devices that have a year associated with it. This
year is either one of:

* release date
* FCC date
* WiFi certified date

The year can either be a single year:

```
year=2018
```

or it can be a range (inclusive):

```
year=2018:2020
```

which is equivalent to:

```
year=2018 year=2019 year=2020
```

# Adding more filter options

When adding a new filtering option the code needs to be changed in a few
places, depending on what functionality is needed. The places where code needs
to be changed:

* `deviceode/defaults.py` - the dictionary `TOKEN_NAMES` needs to be updated.
* `devicecode/suggester.py` - controls the type ahead suggestions in the TUI.
  This is not mandatory to have for filtering, but it is useful for users.
* `devicecode/filter.py` - controls the filtering validation, as well as
  splitting the code and putting the data into the right data structures.
* `devicecode/dataset_composer.py` - compiles the data sets that are used for
  displaying or pretty printing, optionally filtering results using data
  obtained earlier (and can be considered to be the actual filter).
