# Creating dump files for TechInfoDepot Wiki and WikiDevi

## Creating a dump file

As both TechInfoDepot and WikiDevi are based on MediaWiki it is possible to
create an export of the data. This can be done in two ways: manually and
automatically. Currently only exports created the manual way are supported.

### TechInfoDepot

Go to <https://techinfodepot.shoutwiki.com/wiki/Special:Export> and add the
following categories to the download. Do this by pasting the name of each
category into the field `Add pages from category` and then clicking `Add`.
Make sure that the boxes `Include only the current revision, not the full
history`, `Include templates` and `Save as file` are ticked.

The categories are:

* Wireless_Embedded_System
* Embedded_System
* Network_Adapter
* Wireless_Adapter
* USB_device
* Network_Switch

The resulting downloaded XML file will be a bit less than 100 MiB in size
(observed August 2024).

Note: there appear to be differences depending on which version of
TechInfoDepot is used and the different subsites do not seem to be properly
synced. The English language subsite seems to have more data, so it might be
better to go to <https://en.techinfodepot.shoutwiki.com/wiki/Special:Export> to
create the export.

### WikiDevi

Go to <https://wikidevi.wi-cat.ru/Special:Export> and add the following
categories to the download. Do this by pasting the name of each category into
the field `Add pages from category` and then clicking `Add`. Make sure that the
boxes `Include only the current revision, not the full history` and `Save as
file` are ticked.

The categories are:

* Wi-Fi Certified
* Wireless adapter
* Wired_embedded_system
* Wireless embedded system
* Wireless_embedded_system
* Embedded_system/analog_phone_gateway
* Embedded_system/access_point
* Embedded_system/bridge
* Embedded_system/NAS
* Embedded_system/mobile_hotspot
* Embedded_system/FiOS_modem
* Embedded_system/client
* Embedded_system/USB_device_server
* Embedded_system/security_appliance
* Embedded_system/ONT
* Embedded_system/802.11_monitoring_device
* Embedded_system/base_station
* Embedded_system/hotspot_gateway
* Embedded_system/residential_gateway
* Embedded_system/digital_photo_frame
* Embedded_system/wireless_internet_appliance
* Embedded_system_firmware/backdoors
* Embedded_system/network_CableCARD_tuner
* Embedded_system/VoIP_phone
* Embedded_system/WiMAX_modem
* Embedded_system/LTE_router
* Embedded_system/WiMAX_CPE
* Embedded_system/internet_radio
* Embedded_system/test
* Embedded_system/mobile_battery_pack
* Embedded_system/digital_video_recorder
* Embedded_system/display_receiver
* Embedded_system/network_monitor
* Embedded_system/video_streamer
* Embedded_system/fiber_gateway
* Embedded_system/point_of_sale_system
* Embedded_system/wireless_button
* Embedded_system/fleet_monitoring_system
* Embedded_system/Universal_Remote
* Embedded_system/wireless_mobile_storage
* Embedded_system/remote_control_extender
* Embedded_system/USB_dongle
* Embedded_system/wireless_terminal
* Embedded_system/sensor
* Embedded_system/hardware_PowerPoint_machine
* Embedded_system/VPN_Concentrator
* Embedded_system/spectrum_analyzer
* Embedded_system/home_monitoring_gateway
* Embedded_system/human_disability_mitigation_device
* Embedded_system/wireless_USB_hub
* Embedded_system/interior_door_station
* Embedded_system/media_converter
* Embedded_system/Wi-Fi_enabled_Arduino
* Embedded_system/Wi-Fi_enabled_MCU_dev._kit
* Embedded_system/wireless_presentation_gateway
* Embedded_system/pico_video_projector
* Embedded_system/printer
* Embedded_system/Wi-Fi_location_tag
* Embedded_system/satellite_TV_receiver
* Embedded_system/WiFi_security_auditing_tool
* Embedded_system/WiMAX_IAD
* Embedded_system/small_remote-controlled_vehicle
* Embedded_system/advertising_kiosk
* Embedded_system/useless_junk
* Embedded_system/body_scale
* Embedded_system/wireless_'cloud'_storage_device
* Embedded_system/braille_notetaker
* Embedded_system/wireless_drone
* Embedded_system/device_storage_extender
* Embedded_system/wireless_payment_stick
* Embedded_system/eMTA
* Embedded_system/hotspot_controller
* Embedded_system/infrared_remote_relay
* Embedded_system/health_monitoring_device
* Embedded_system/location-aware_media_player
* Embedded_system/point-to-point_link
* Embedded_system/screen_sharer
* Embedded_system/service_gateway
* Embedded_system/remote_control_relay
* Embedded_system/wireless_audio_adapter
* Embedded_system/video_server
* Embedded_system/Fiber_CPE
* Embedded_system/ISDN_modem
* Embedded_system/JenNet_wireless_gateway
* Embedded_system/Mouse
* Embedded_system/RF_remote_control
* Embedded_system/station
* Embedded_system/wireless_eMTA
* Embedded_system/wireless_speaker_system
* Embedded_system/RFID_scanner
* Embedded_system/web_server
* Embedded_system/power_distribution
* Embedded_system/crypto_currency_miner

Then click "Export" and store the XML result somewhere.
