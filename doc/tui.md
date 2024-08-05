# DeviceCode Text User Interface

To quickly browse devices it is more efficient to use a specialized interface
instead of relying on tools such as `grep` and `less` to look at raw JSON
output.

A TUI (text user interface) can be a quick and easy way to browse and search
results. [Textual][textual] and [Rich][rich] are very suited for this task.

## Representing results

There are many ways results can be represented and there is no single best way
to represent these results. Depending on which element is the most important
the data should be presented in a different way.

An obvious way would be to have a tree, with brands as branches and device
models as leafs, with perhaps an additional layer for the various wiki types
that were parsed.

If a CPU or chip is the most important element, then the results could be
represented as a tree, with chip vendors at the top, chip model numbers as
subtrees, and individual devices as leafs.

If operating system is the most imporant, then the results could be sorted
by operating system. If release year is the most important, then it could be
sorted by year, and so on.

Currently there are three views:

1. brand view: a tree with devices sorted by brand
2. ODM view: a tree with devices sorted by ODM and then brand
3. table view: a table with a count for brand/ODM combinations

## Filtering

The trees with devices can be searched using a special filtering language.
The result after filtering will be a tree containing just some of the entries.

For filtering a special purpose filtering language is used, which can
filter on a few attributes, such as:

* bootloader
* brand
* chipset manufacturer
* ODM
* flags
* serial port
* password
* etc.

### Filtering language

The filtering language is fairly simplewith statements and (implicit)
operators (for combining results).

#### Statements

Statements resemble bash shell commands and exports and are of the form:

```
identifier=value
```

where identifier can be one of:

* `brand`
* `chip`
* `chip_vendor`
* `connector`
* `flag`
* `ignore_brand`
* `ignore_odm`
* `odm`
* `password`
* `serial`
* `type`
* `year`

Values are case insensitive.

An identifier can appear multiple times. Multiple instances with the same
identifer should be interpreted as "OR". Instances with a different identifier
should be interpreted as "AND". As an example:

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

In case there are special characters or spaces, then these can be quoted, for
example:

```
brand="Banana Pi"
```

##### Bootloader

`bootloader` can be used to filter on bootloader.

##### Brand

There are two ways to filter brands:

1. use the `brand` statement to show devices from one or more brands
2. use the `ignore_brand` statement to hide devices from one or more brands

##### Chip vendor

Currently `chip_vendor` can only be used to show the main CPU in one or more
devices.

##### Connector

`connector` can be used to filter connectors (serial port only for now, JTAG
in the future as well).

##### Flag

`flag` can be used to show one or more more devices with certain flags.

##### ODM

There are two ways to filter brands:

1. use the `odm` statement to show devices made by one or more ODMs
2. use the `ignore_odm` statement to hide devices made by one or more ODMs

##### Serial

`serial` can be used to show if a device has a serial port, or if it is not
known. Valid values are `yes`, `no` and `unknown`.

##### Password

Currently `password` can only be used to show devices with one or more default
passwords.

##### Year

`year` can be used to show devices that have a year associated with it. This
year is either one of:

* release date
* FCC date
* WiFi certified date

[rich]:https://github.com/Textualize/rich
[textual]:https://github.com/Textualize/textual
