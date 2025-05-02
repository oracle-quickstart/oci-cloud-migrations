# modify_inventory_asset.py

## Overview
A simple script which modified an Oracle Cloud Bridge Inventory Asset.

## Usage
### View Inventory Asset Details
```
lgabriel@cloudshell:modify_inventory_asset (us-ashburn-1)$ python modify_inventory_asset.py -cs ocid1.ocbinventoryasset.oc1.iad.tjq3f5qccxmsrtl743 
Inventory Asset Name: uefi-firmware
Current Firmware: UEFI
Current Disks:
['Disk Number', 'Disk Name', 'Boot Order', 'Size in MB', 'UUID']
[0, '/dev/sda1', 0, 30720, 'vol-0779b9ed400bcdb02']
```
### Select a new boot disk
```
```
### Exclude a disk
```
```
### Change compute firmware
```
lgabriel@cloudshell:modify_inventory_asset (us-ashburn-1)$ python modify_inventory_asset.py -cs ocid1.ocbinventoryasset.oc1.iad.tjq3f5qccxmsrtl743 -f efi
Inventory Asset Name: uefi-firmware
Current Firmware: UEFI
Current Disks:
['Disk Number', 'Disk Name', 'Boot Order', 'Size in MB', 'UUID']
[0, '/dev/sda1', 0, 30720, 'vol-0779b9ed400bcdb02']
Changing firmware.
Modifying AWS Timestamps.
New Inventory Details
New Firmware: efi
New Disks:
['Disk Number', 'Disk Name', 'Boot Order', 'Size in MB', 'UUID']
[0, '/dev/sda1', 0, 30720, 'vol-0779b9ed400bcdb02']
```