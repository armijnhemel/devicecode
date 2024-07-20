# DeviceCode Text User Interface

To quickly browse devices it is more efficient to use a specialized interface
instead of relying on tools such as `grep` and `less` to look at raw JSON
output.

A TUI (text user interface) can be a quick and easy way to browse and search
results.

## Representing results

There are many ways results can be represented and there is no single best way
to represent these results. Depending on which element is the most important
the data should be presented in a different way.

An obvious way would be to have a tree, with brands at the top and device
models as leafs, with perhaps an additional layer for the various wiki types
that were parsed.

If a CPU or chip is the most important element, then the results could be
represented as a tree, with chip vendors at the top, chip model numbers as
subtrees, and individual devices as leafs.

If operating system is the most imporant, then the results could be sorted
by operating system. If release year is the most important, then it could be
sorted by year, and so on.

Currently there are three views:

1. brand view: devices are sorted by brand
2. ODM view: devices are sorted by ODM and then brand
3. filter view: devices are sorted depending on a filter

## Filtering

In the "filter view" devices can be searched using a special filtering
language. The result after filtering will be a tree containing just some
of the entries.

For filtering a special purpose filtering language will be used, which can
filter on a few attributes, such as:

* chipset manufacturer
* ODM
* operating system
* etc.

and optionally sort by:

* brand
* ODM
* chipset manufacturer/chip

### Filtering language

The filtering language is fairly simple. There are statements, (implicit)
operators (for combining results) and sorters (for sorting).

#### Statements

Statements resemble bash shell commands and exports and are of the form:

```
identifier=value
```

where identifier can be one of:

* `brand`
* `odm`
* `chip`

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

#### Sorting


[rich]:https://github.com/Textualize/rich
[textual]:https://github.com/Textualize/textual
