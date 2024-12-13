# Fields in OpenWrt

The OpenWrt CSV data has the following fields (names extracted from the OpenWrt CSV dump):

0. pid
1. devicetype
2. brand
3. model
4. version
5. fccid
6. availability
7. whereavailable
8. supportedsincecommit
9. supportedsincerel
10. supportedcurrentrel
11. unsupported_functions
12. target
13. 'subtarget
14. packagearchitecture
15. bootloader
16. cpu
17. cpucores
18. cpumhz
19. flashmb
20. rammb
21. ethernet100mports
22. ethernetgbitports
23. ethernet1gports
24. ethernet2_5gports
25. ethernet5gports
26. ethernet10gports
27. sfp_ports
28. sfp_plus_ports
29. switch
30. vlan
31. modem
32. commentsnetworkports
33. wlanhardware
34. wlan24ghz
35. wlan50ghz
36. wlancomments
37. wlandriver
38. detachableantennas
39. bluetooth
40. usbports
41. sataports
42. commentsusbsataports
43. videoports
44. audioports
45. phoneports
46. commentsavports
47. serial
48. serialconnectionparameters
49. jtag
50. ledcount
51. buttoncount
52. gpios
53. powersupply
54. devicepage
55. device_techdata
56. owrt_forum_topic_url
57. lede_forum_topic_url
58. forumsearch
59. gitsearch
60. wikideviurl
61. oemdevicehomepageurl
62. firmwareoemstockurl
63. firmwareopenwrtinstallurl
64. firmwareopenwrtupgradeurl
65. firmwareopenwrtsnapshotinstallurl
66. firmwareopenwrtsnapshotupgradeurl
67. installationmethods
68. commentinstallation
69. recoverymethods
70. commentrecovery
71. picture
72. comments
73. page

Not all of these are interesting. Not all of the information can be extracted
from the data in the CSV. For example, serial port information is incomplete
and doesn't include information regarding which solder pads should be used.
This is not entirely surprising as this information sometimes cannot be
squeezed into a single field but needs more characters or a full description,
but in most cases it could be. This information should be extracted from the
individual device pages.
