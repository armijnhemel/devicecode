# Design: default values in TechInfoDepot

The TechInfoDepot data is stored in a Wiki that can be edited by anyone with an
account on the Wiki.

It seems that when new data is entered on the TechInfoDepot website a template
is used with default values (in HTML comments) and users are expected to remove
the default text and supply their own text. WikiDevi doesn't seem to take this
approach.

After looking at the data a few things become clear:

1. templates have been updated over the years, so there can be multiple default
   values. Old templates in the data have not been updated.
2. some users merely update the values in the template itself, without removing
   the HTML comment tags (`<!--` and `-->`). Combined with 1. this makes it
   sometimes difficult to see if the data is a default value, or if it has been
   changed.
3. some users insert values but don't remove the template. Some prepend their
   own data before the template, others append it.
4. a combination of 2. and 3.

Examples of all these can be found when processing `cpu1spd`.

## 1: There are three known default values:

```
<!-- CPU1 speed, MHz, GHz, Leave blank if unknown -->
<!-- undocumented -->
<!-- In MHz, number only Leave blank if unknown -->
```

Note that the first and the last option are contradicting each other, which
means that the entered data is inconsistent depending on which value was the
default at the time.

## 2: data is merely updated inside comment tags

```
<!-- up to 180 MHz -->
<!-- 2.0 GHz 2.2 GHz (+ 2x NPU @1.7GHz) -->
<!-- 32-bit MCU & 2.4GHz Wi-Fi, Single-core CPU @160MHz -->
```

## 3: template values are not removed

```
1.2 GHz<!-- 1.2 GHz  -->
1.8 GHz<!-- undocumented -->
600<!-- undocumented -->
```

## 4: data is updated inside comment tags and template values are not removed

```
1.4 GHz<!-- 1.4 GHz 1.4 GHz (+ 2x NPU @1.5GHz) -->
450<!-- 200 per doc page, 450 per OpenWrt -->
```

## Ignoring default values

Default values are ignored and not even processed. In `devicecode_defaults.py`
a lookup table called `DEFAULT_VALUE` is defined with default values for most
identifiers. Default values are a list of strings. If a value for an identifier
matches one of the default values for that identifier (full match, not partial)
then processing continues with the next value or next identifier.

To add a new default value edit the `DEFAULT_VALUE` table.
