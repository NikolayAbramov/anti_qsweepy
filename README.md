## Anti QSWEEPY
A simple measurement automation tool.

To install run this:
```sh
pip install anti_qsweepy
```
Then run the following setup command: 
```sh
anti_qsweepy_setup
```
## How to use
TODO
## IMPA GIU
The package includes GUI tool for tuning of impedance matched parametric amplifiers (IMPA).
The IMPA web GIU can be launched with the following command: 
```sh
impa_gui
```
After first launch the IMPA_GUI_conf and IMPA_GUI_data directories will be created in the \<Documents>/anti_qsweepy folder.
The IMPA_GUI_conf contains yaml configuration files and the IMPA_GUI_data is the place where measurements results will be saved.
Channels layout and used devices are specified in the main configuration file IMPA_GUI/config.yml.
## Device restarter
Device restarting utility
Usage:
```sh
restart_device [part of device name]
```
Example:
```sh
restart_device COM5
```
All devices whose name contains the [part of device name] string will be restarted using pnputil.
Run as administrator in order to avoid permission denied error.