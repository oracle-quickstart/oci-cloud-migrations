# Overview
These are example scripts that support the [Oracle Cloud Migrations](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/home.htm) service.

# Included Scripts
|Script|Description|Environment|Last Updated|
|---|----|----|---|
|[modify_inventory_asset.py](modify_inventory_asset/README.md)| Modifies an Inventory Asset.|And|01 May 2025|
|[find_asset.py](find_asset/README.md)| Scans all compartments to find all Migration Assets, originated from the specific Source Asset.| CloudShell| 28 Mar 2024|
|[cleanup_volumes.py](cleanup_volumes/README.md)|Terminates unattached volumes.|CloudShell|27 Mar 2024|
|[rename_move_volumes.py](rename_move_volumes/readme.md)|Renames and moves block volumes attached to an instance.|Any OCI Config|10 Jun 2024|
|[terminate_nat_gateway](terminate_nat_gateway/README.md)|Workaround for the default Hydration Agent virtual network created by the Oracle Cloud Migrations service.|Resource Manager|12 Jun 2024|
|[SetupWorkloads.ps1](setup_workloads/README.md)|Helpful scripts for setting up a training lab.|PowerShell|18 Apr 2024|
|[SetIP.py](SetIP/README.md)|Manage the private IP address of the target Assets in a migration plan|Python|11 Nov 2024|
|[cbt.py](ChangeBlockTracking/README.md)|Check and configure Change Block Tracking for multiple VMs in vCenter|Python|9 December 2024|
# Usage

## CloudShell
```
lgabriel@cloudshell:~ (us-ashburn-1)$ git clone https://github.com/oracle-quickstart/oci-cloud-migrations.git
Cloning into 'oci-cloud-migrations'...
remote: Enumerating objects: 476, done.
remote: Counting objects: 100% (104/104), done.
remote: Compressing objects: 100% (51/51), done.
remote: Total 476 (delta 65), reused 53 (delta 53), pack-reused 372 (from 2)
Receiving objects: 100% (476/476), 1.09 MiB | 44.46 MiB/s, done.
Resolving deltas: 100% (194/194), done.

lgabriel@cloudshell:~ (us-ashburn-1)$ cd oci-cloud-migrations/

lgabriel@cloudshell:oci-cloud-migrations (us-ashburn-1)$ git checkout main
Already on 'main'
Your branch is up to date with 'origin/main'.

lgabriel@cloudshell:oci-cloud-migrations (us-ashburn-1)$ git checkout lgabriel_modify_inventory_asset
Switched to branch 'lgabriel_modify_inventory_asset'
Your branch is up to date with 'origin/lgabriel_modify_inventory_asset'.
lgabriel@cloudshell:oci-cloud-migrations (us-ashburn-1)$ 
```
