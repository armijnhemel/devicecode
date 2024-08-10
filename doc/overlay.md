# Overlay files

Overlay files are a mechanism to add/correct data. These can be used by scripts
processing the data from the Wikis to generate updated files, or to read these
files on the fly.

The structure of overlay files is a dictionary, with the following fields:

* `type`: always `overlay`
* `source`: set to whatever the source of the information is, for example `fcc`
* `data`: following the same structure as the regular data files, but only
  containing a subset of data.

An example of an overlay file:

```
{
    "type": "overlay",
    "source": "fcc",
    "data": {
        "regulatory": {
            "fcc_date": "2012-10-08"
        }
    }
}
```

Overlay files are stored in a directory with the same name as device files
(minus the suffix) and are stored in a directory called `overlays`.

# Creating overlays

Overlays can be created manually (as long as it is valid JSON) or using
scripts. One script to create overlays for FCC data is `fcc_overlay.py`. This
script can be used as follows:

```console
$ python fcc_overlay.py -f /path/to/fcc/directory -d /path/to/device/directory -o /path/to/overlay/directory
```

for example:

```console
$ python fcc_overlay.py -f ~/fcc/ -d ~/devices/TechInfoDepot/devices/ -o ~/devices/TechInfoDepot/
```
