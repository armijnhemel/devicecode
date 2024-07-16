# Design: parsing chips information

Each device contains one or more chips. Some chips are explicitly labeled as
for example memory chip, flash chip, ethernet chip, and so on. Then there are
also other chips that don't find in a specific category.

There could be more than one chip for each category. For example, there could
be multiple flash chips, multiple radio chips, and so on. Also, there could be
more than one chip in a single chip package (SoC). In the wiki these are
indicated with various numbers.

As an example take the Ethernet chip. In the TechInfoDepot data you can find
the following values: `eth1chip`, `eth2chip`, `eth3chip`, `eth4chip`,
`eth5chip`, `eth6chip` used for various devices, that indeed appear to have
more than one Ethernet chip.

Then there are devices where there seem to be multiple chips in one chip
package. This happens for example with the radio chips. In the TechInfoDepot
data you can find the following values for the radio chip (note: in the
WikiDevi data the radio chips are not explicitly labeled as such):

`rad1chip1`, `rad1chip2`, `rad1chip3`, `rad2chip1`, `rad2chip2`, `rad2chip3`,
`rad3chip1`, `rad3chip2`, `rad3chip3`, `rad4chip1`, `rad4chip2`, `rad4chip3`

As said, these seem to indicate chip packages. The value for `rad2chip2` should
likely be read as "the second chip in the second radio SoC". This makes parsing
a little bit more challenging.

## Parsing chips information

Most chips, except `addchip` entries (TechInfoDepot) or `addl_chip` (WikiDevi)
seem to be formatted as follows:

```
manufacturer;model;extra information
```

although there seem to be exceptions due to how the data was entered. The field
"extra information" can actually be multiple fields. The assumption is that
these fields are the text that is printed on the chip. It is often empty.

### Parsing `addchip` and `addl_chip` information

The `addchip` (TechInfoDepot) and `addl_chip` (WikiDevi) entries are slightly
different. The format seems to be:

```
description;manufacturer;model;extra information
```

where it is not entirely clear what the extra information is: it seems to
contain more individual fields than the other chip entries. The TechInfoDepot
and WikiDevi wikis do not clarify what each of the different fields mean. There
is definitely wrong data in these fields, where users have filled in random
data. This is difficult to detect automatically and probably needs manual
cleanup.

## Verifying manufacturers and chip models

Some observed errors are that people use different names for chipset
manufacturers such as abbreviations (example: "TI"/"Texas Instruments") or
possibly wrong data (such as spelling mistakes) that makes it hard to compare
devices.

To reduce the amount of bogus data in the chip models, the chip manufacturer
name and model are verified using a list of manufacturer names and model
numbers (per manufacturer). These lists have been (manually) verified. If the
manufacturer and model number are in these lists, then an extra `verified` flag
will be set. This doesn't mean that unverified data is wrong or that the chip
or manufacturer don't exist, it is just not verified. It is only an extra piece
of data to increase fidelity.

The lists with manufacturers and model numbers of course need to be kept up to
date.
