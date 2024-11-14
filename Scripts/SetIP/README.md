# Oracle Cloud Migration - Set IP Address for Target Assets

This script allow you to set a predetermined IP Address for your Assets in an Oracle Cloud Migration Plan

You have 4 options on how you can control the Target Asset IP Address
- Based on existing IP Address (IP Address of the Source VM)
- Based on a text file where you can Map IP addresses to VM Names
- Based on free form tags that are part of the migration plan
- Based on a Custom Attribute in vCenter set in the source VM


## Usage
```
usage: SetIP.py [-h] [-cp CONFIG_PROFILE] [-ip] [-dt] [-rg REGION]
                (-targetasset_id TARGETOCID | -migrationplan_id MIGRATIONPLANOCID) (-fixip | -ipmap IPMAP | -tagmap | -vcenter)

options:
  -h, --help                           show this help message and exit
  -cp CONFIG_PROFILE                   Config Profile inside the config file
  -ip                                  Use Instance Principals for Authentication
  -dt                                  Use Delegation Token for Authentication
  -rg REGION                           Region
  -targetasset_id TARGETOCID           Target Asset OCID
  -migrationplan_id MIGRATIONPLANOCID  Migration Plan OCID
  -fixip                               Set static IP to existing Static IP
  -ipmap IPMAP                         Set static IP to mappings based in a file
  -tagmap                              Set static IP based on free form tags on the migration plan
  -vcenter                             Set static IP based on vCenter Customer attributes
```

## How to run the script

### OCI CLI
You can run the script from any place where you have setup the OCI CLI tool with the correct authentication.

## Cloud Shell
You can run the script from the cloud shell, just clone this repo into your cloud shell. When you run the script
add the option **-dt** this will let you use the cloud shell delegated authentication. This means it will use the 
current user logged into cloud shell to run the script

## Instance Principle
You can run the script inside a VM in OCI. If that VM belongs to a dynamic group that has the right permissions you 
can use the option **-ip** to use the instance's Dynamic group to authenticate against OCI.

More info: https://www.ateam-oracle.com/post/calling-oci-cli-using-instance-principal

## Setting the IP address of your Target Assets

### Setting IP Addresses based on Source VMs
Using the **-fixip** option, the script will check the IP Address(es) of the source VM. If an IP Address is found that matches the
target Subnet's CIDR if will configure the target VM with this IP address

### Setting IP Addresses based on a Mapping File
Using the **-ipmap [filename]** option, you can create a mapping file. See the **ipmap.txt** example file. Per line in the file specify the
IP Address and Virtual Machine name, seperated with a ;

If a matching VM is found in the mapping file, it will use that IP address to setup the target VM

### Setting IP Address based on Free Form Tags
Using the **-tagmap** option, you can map IP addresses using the OCI Free-form tags. You can create one or multiple Free-form tags
on the migration plan. The **Tag Key** should match the VM Name and the **Tag Value** should contain the IP Address
you want to have configured for this VM

**IMPORTANT: ** OCI Support only up to 10 Free-form tags per object. So using Free-form tags you can only make 10
assignments per migration plan.

<img src=tag_example.png width="400">

### Setting IP Address based on Customer Attribute set in vCenter
Using the **-vcenter** option, you can create in vCenter a Custom Attribute on the source VM. The name of 
the attribute can be anything, but the value must start with **OCI:** and then followed with the IP Address you want to use.

<img src=vcenter_example.png width="400">

## Validation
When the script runs, if will check if an assigned/mapped IP address is found and if this IP Address is part of the CIDR
range of the target Subnet in OCI. It will also check if there is no conflict with the default gateway in that subnet or with any 
current running services that are using this subnet.


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
