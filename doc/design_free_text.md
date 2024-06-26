# Design: parsing free text

In the pages of the various Wikis there is useful information stored in
data that is mostly unstructured, for example boot log information, output of
`/proc/cpuinfo` and `/proc/pci`, nvram contents, output of `dmesg`,
and so on.

Some interesting information that could be extracted from this data includes
package names and versions (of both proprietary and open source packages),
build dates, usernames of the ODM (recorded in for example the Linux kernel
and printed by boot messages), references to SDKs, etcetera.

Of particular interest are the following:

* boot logs
* output of `dmesg`
* output of `nvram show`
* output of `ls`
* anything in `/proc`
* serial console output
* serial port information (pin headers, layout, etc.)

although some useful data can be hidden in other places as well, because users
tend to put it in random locations.

## Example data

The boot logs are interesting, because these can contain information about the
Linux kernel and programs that are started. Depending on the user who entered
the data these might contain full logs with/without timestamps. Some examples
are below:

### BusyBox

If `klogd` from BusyBox is used the BusyBox version and compile date can be
extracted:

```
Feb 14 00:00:17 kernel: klogd started: BusyBox v1.17.4 (2018-05-11 21:25:06 CST)
```

### Linux kernel version

The Linux kernel version can reveal interesting information:

```
Feb 14 00:00:17 kernel: Linux version 2.6.36.4brcmarm (root@asus) (gcc version 4.5.3 
                    (Buildroot 2012.02) ) #1 SMP PREEMPT Fri May 11 21:29:42 CST 2018
```

The GCC version string indicates that at least the compiler is from Buildroot.
There is a good chance that the rest of the system was also built with
this particular version of Buildroot. Knowing which the (default) package are
in that particular version of Buildroot makes it likely that these versions are
also used/present on the device.

### Linux kernel commandline

The Linux kernel commandline lists the boot parameters such as whether or not
there is a serial port and how to connect to it (speed, `tty`):

```
Feb 14 00:00:17 kernel: Kernel command line: root=/dev/mtdblock2 console=ttyS0,115200 init=/sbin/preinit earlyprintk debug
```

### U-Boot

```
U-Boot 2010.12-00050-ga7f6f23 (Oct 02 2013 - 15:23:12)
```

### Other open source packages

Sometimes package information can be extracted, such as for `dnsmasq`:

```
Feb 14 00:00:19 dnsmasq[211]: warning: no upstream servers configured
```

or `e2fsprogs`:

```
e2fsck 1.42.9 (28-Dec-2013)
```

or `miniupnp`:

```
Jan  1 00:00:33 miniupnpd[378]: listening on 192.168.1.1:5555
Jan  1 00:00:26 miniupnpd[318]: WPS listening on port 7777
```

### services

```
Feb 14 00:00:19 RT-N66U_C1: start httpd:80
```

indicates clearly that there is a web server running.

### Proprietary packages

```
CFE version 1.0.37 for BCM947XX (32bit,SP,LE)
```

```
Adtran bootloader version 1.0.5
```

## Parsing logs

As the data that is entered really is free form text there is little structure
that can be expected. Various techniques are used to extract the data. First
and foremost: regular expressions for packages, functionality, program names
and source code names.

If it is clear that the data follows a certain structure (such as the output
of `ls -la` or `ps`), then some custom code is used to specifically parse that
format.

### ps

The output of `ps` depends on the flags that were given to `ps` when the command
was run. The output of `ps e` will be different from the output of `ps aux`.
