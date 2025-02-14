# Creating/downloading dump files

## Creating a dump file for TechInfodepot Wiki and WikiDevi

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

* Embedded system/camera
* Embedded_System
* Embedded_System_ARM
* Embedded_System_Broadcom
* Embedded_system/3G_gateway
* Embedded_system/3G_mobile_router
* Embedded_system/4G_LTE_router
* Embedded_system/5G_router
* Embedded_system/802.11_monitoring_device
* Embedded_system/CPE
* Embedded_system/FiOS_modem
* Embedded_system/Fiber_CPE
* Embedded_system/IP_camera
* Embedded_system/ISDN_modem
* Embedded_system/IoT
* Embedded_system/IoT_firewall
* Embedded_system/IoT_hub
* Embedded_system/LTE_modem
* Embedded_system/LTE_router
* Embedded_system/MoCA_bridge
* Embedded_system/Mouse
* Embedded_system/PC_to_TV_video_streamer
* Embedded_system/Powerline_Access_Point
* Embedded_system/Powerline_Adapter
* Embedded_system/Remote_NDIS_Ethernet_adapter
* Embedded_system/SoM
* Embedded_system/USB_device_server
* Embedded_system/VPN_Router
* Embedded_system/VPN_Router_Firewall
* Embedded_system/VPN_router
* Embedded_system/VoIP_phone
* Embedded_system/WMC7_extender
* Embedded_system/WiMAX_modem
* Embedded_system/access_point
* Embedded_system/analog_phone_gateway
* Embedded_system/asset_management_appliance
* Embedded_system/audio_bridge
* Embedded_system/audio_streamer
* Embedded_system/baby_monitor
* Embedded_system/base_station
* Embedded_system/bridge
* Embedded_system/cable_modem
* Embedded_system/client
* Embedded_system/computer_screen_streamer
* Embedded_system/development_board
* Embedded_system/digital_(still)_camera
* Embedded_system/digital_media_adapter
* Embedded_system/display_receiver
* Embedded_system/display_receiver_stick
* Embedded_system/dsl_modem
* Embedded_system/enterprise_access_point
* Embedded_system/extender
* Embedded_system/fiber_gateway
* Embedded_system/fleet_monitoring_system
* Embedded_system/game_console
* Embedded_system/hardware_PowerPoint_machine
* Embedded_system/home_automation_controller
* Embedded_system/home_automation_switch
* Embedded_system/home_monitoring_gateway
* Embedded_system/home_security_gateway
* Embedded_system/hotspot_gateway
* Embedded_system/industrial_access_point
* Embedded_system/internet_radio
* Embedded_system/managed_access_point
* Embedded_system/media_bridge
* Embedded_system/mesh_hub
* Embedded_system/mesh_node
* Embedded_system/mini_module
* Embedded_system/miracast_receiver
* Embedded_system/mobile_NAS
* Embedded_system/mobile_hotspot
* Embedded_system/mobile_router
* Embedded_system/module
* Embedded_system/motion_sensor
* Embedded_system/network_monitor
* Embedded_system/outdoor_access_point
* Embedded_system/plug_computer
* Embedded_system/point-to-point_link
* Embedded_system/portable_game_console
* Embedded_system/print_server
* Embedded_system/range_extender
* Embedded_system/remote_control_extender
* Embedded_system/remote_control_relay
* Embedded_system/repeater
* Embedded_system/residential_gateway
* Embedded_system/router
* Embedded_system/screen_sharer
* Embedded_system/security_appliance
* Embedded_system/sensor
* Embedded_system/set_top_box
* Embedded_system/single-board_computer
* Embedded_system/smart_meter_monitor
* Embedded_system/spectrum_analyzer
* Embedded_system/thin_client
* Embedded_system/travel_router
* Embedded_system/video_streamer
* Embedded_system/wireless_'cloud'_storage_device
* Embedded_system/wireless_camera
* Embedded_system/wireless_embedded_board
* Embedded_system/wireless_router
* Embedded_system/wireless_speaker_system
* Embedded_system/wireless_speakers
* Embedded_system/wireless_system
* Network_Adapter
* Network_Switch
* USB_device
* Wired_Embedded_System
* Wireless_Adapter
* Wireless_Embedded_System

(Note: although almost everything should be in "Embedded_system" including
those devices doesn't seem to grab the subcategories.)

The resulting downloaded XML file will be a around 116 MiB in size (observed
August 2024).

Note: there appear to be differences depending on which version of
TechInfoDepot is used and the different subsites do not seem to be properly
synced. The English language subsite sometimes seems to have more data, so it
might be better to go to <https://en.techinfodepot.shoutwiki.com/wiki/Special:Export>
to create the export.

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

## Downloading a dump file for the OpenWrt table of hardware

Get the CSV dump at: <https://openwrt.org/toh/views/start>

The script `devicecode_grab_openwrt.py` can then be used to download additional
pages from the OpenWrt wiki.
