# DeviceCode: crowdsourced device data parser

This project contains tools to parse content from the
[TechInfoDepot Wiki][techinfodepot] and [WikiDevi][wikidevi] websites.

It parses the content from an XML dump, tries to convert the data into
something more useful and unify all the different ways that people have entered
data. This is why the code is quite hairy, [but it is necessary][metacrap].

Despite data quality issues these wikis are by far the best source of
information about devices currently available under an open license, as vendors
and device manufacturers tend to be not very forthcoming with what is inside
devices.

The goal of this project is to unlock data from various sources, rework it
into a format that is easier to reuse, cleanup and makes it available for use
by other projects, such as [VulnerableCode][vulnerablecode].

## Workflow

The tools need a dump file with data exported from TechInfoDepot or WikiDevi.
This dump file is in XML format and contains content in a mix of HTML and
MediaWiki format.

The formats of the two websites are fairly similar as TechInfoDepot seems to
have been forked from (a predecessor of) WikiDevi.

### Creating a dump file

If you want to get a pregenerated set of data, checkout the
[devicecode-data][devicecode-data] repository.

See [creating a dump file](doc/creating_a_dump_file.md).

### Running the scripts

The easiest to run the script is to use Nix and then `nix-shell` to set up the
environment. If this isn't your cup of tea, then the requirements for running
the scripts are (currently) quite modest (see `requirements.txt`).

To run the script you will need a dump file (see above). It is recommended that
the directory you write to is an existing Git repository. One method is to
create a fresh directory and init a Git repository, for example:

```
$ mkdir devicecode
$ cd devicecode
$ git init
```

but of course you could also use an existing Git clone from for example GitHub.
If you are using Git support (see later) you should be aware that the settings
of the Git repository will be used for the author and committer.

The script will create the following directory structure inside the Git
repository:

```
{WIKI_TYPE}/
{WIKI_TYPE}/devices/
{WIKI_TYPE}/original/
```

where `WIKI_TYPE` is currently either `TechnInfoDepot` or `WikiDevi`. For each
device that was processed a single JSON file will be written to the
subdirectory `devices` with (cleaned up) data extracted from the Wiki. The
original XML data will be written to the directory `original`.

Extra data (such as concluded data or data that wasn't in the original data)
will be written as separate JSON files (this is future work).

To invoke the script use the following command (change the name of the input,
wiki type and output directory to your needs):

```
$ python devicecode.py -i TechInfoDepot-20231002144356.xml --wiki-type=TechInfoDepot -o ~/devicecode
```

If you are using Git support and the Git repository is not local (for example,
it is a GitHub repository) you will have to manually do a `git push` to send
the results upstream.

Using Git will have a serious performance impact. Running the script with Git:

```
$ time python devicecode.py -i TechInfoDepot-20240409163428.xml -o /tmp/bla/ --wiki-type=Techinfodepot --use-git

real	23m37.186s
user	18m13.881s
sys	11m40.159s
```

and without Git:

```
$ time python devicecode.py -i TechInfoDepot-20240409163428.xml -o /tmp/bla2/ --wiki-type=Techinfodepot

real	2m14.091s
user	2m11.968s
sys	0m1.206s
```

Because of this performance impact Git support is disabled by default. To
enable it there is a flag `--use-git`.

When processing an initial dump the following (example) workflow is recommended:

```
$ mkdir ~/devicecode
$ python devicecode.py -i TechInfoDepot-20231002144356.xml --wiki-type=TechInfoDepot -o ~/devicecode
$ cd ~/devicecode
$ git init
$ git add TechInfoDepot
$ git commit -m "add initial dump"
```

When processing updates the `--use-git` flag could then be used.

### Exploring the data using the DeviceCode TUI

The data is easiest explored using the DeviceCode TUI. For a full description
of the TUI (design, filtering language, and so on) see the
[TUI design document](doc/tui.md).

Simply point the script to the top level directory containing the directory
`TechInfoDepot`:

```console
$ python devicecode_tui.py -d /path/to/top/level
```

for example if the [devicecode-data][devicecode-data] repository was cloned
in `$HOME/git/devicecode-data` the command would be:

```console
$ python devicecode_tui.py -d ~/git/devicecode-data
```

# Acknowledgements

This project was funded through the NGI0 Entrust Fund, a fund established by
NLnet with financial support from the European Commission's Next Generation
Internet programme, under the aegis of DG Communications Networks, Content and
Technology under grant agreement No 101069594.

[techinfodepot]:http://en.techinfodepot.shoutwiki.com/wiki/Main_Page
[metacrap]:https://people.well.com/user/doctorow/metacrap.htm
[wikidevi]:https://wikidevi.wi-cat.ru/
[vulnerablecode]:https://github.com/nexB/vulnerablecode/
[devicecode-data]:https://github.com/armijnhemel/devicecode-data
