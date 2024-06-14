# Why DeviceCode?

When walking into a shop there is a lot of choice for electronic devices such
as WiFi routers, IP cameras, and so on.

In reality many devices are identical, or near identical, as they are coming
from the same manufacturer or if not from the same manufacturer they might use
the same chip, as well as the code from the chipset manufacturer. CVEs on the
other hand typically focus on single devices, and not on classes of (near)
identical devices, so many vulnerable devices are missed in these reports.

Good examples are [CVE-2006-2560][upnp1] and [CVE-2006-2561][upnp2] that both
cover the same vulnerability, but on devices from different vendors (although
very likely the ODM is the same in this case). Many more devices were released
with the exact same vulnerabilities as they were coming from the same ODM or
a different ODM using the same software from the chip manufacturer. These were
missed, possibly given the false impression that only the devices in the CVEs
are vulnerable.

Information about what is used in devices, let alone which ODM made the devices
isn't easy to come by, as companies do not tend to advertise with that
information. Luckily a large collection of information has been crowd sourced
by many people all over the globe, but the information isn't easy to reuse in
other contexts than the wiki.

This is where DeviceCode comes in: it unlocks the information from various
wikis, cleans it up and enables combining this information with other data
sources such as VulnerableCode, making it possible to query on chipset,
chipset manufacturer, ODM, and possibly other information such as installed
software, to answer the question "Which other devices are similar to a known
vulnerable device?" to allow security researchers to zoom in on these devices
and to uncover more vulnerable devices.

[upnp1]:https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2006-2560
[upnp2]:https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2006-2561
