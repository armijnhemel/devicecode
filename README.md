# DeviceCode: crowdsourced device data parser

This project contains tools to parse content from the
[TechInfoDepot Wiki][techinfodepot] and [WikiDevi][wikidevi] websites.

It parsers the content from an XML dump, tries to convert the data into
something more useful and unify all the different ways that people have entered
data. This is why the code is quite hairy, [but it is necessary][metacrap].

Despite data quality issues these wikis are by far the best source of
information about devices currently available under an open license, as vendors
and device manufacturers tend to be not very forthcoming with what is inside
devices.

The goal of this project is to unlock data from various sources, rework it
into a format that is easier to reuse, cleanup and makes it available for use
by other projects, such as [VulnerableCode][vulnerablecode].

# Acknowledgements

This project was funded through the NGI0 Entrust Fund, a fund established by
NLnet with financial support from the European Commission's Next Generation
Internet programme, under the aegis of DG Communications Networks, Content and
Technology under grant agreement No 101069594.

[techinfodepot]:http://en.techinfodepot.shoutwiki.com/wiki/Main_Page
[metacrap]:https://people.well.com/user/doctorow/metacrap.htm
[wikidevi]:https://wikidevi.wi-cat.ru/
[vulnerablecode]:https://github.com/nexB/vulnerablecode/
