# Overview
These are example scripts that support the [Oracle Cloud Migrations](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/home.htm) service.

# Included Scripts
|Script|Description|Environment|Last Updated|
|---|----|----|---|
|[boot_order.py](boot_order/README.md)| Modifies the boot order of disks for a VMware VM Asset.|CloudShell|27 Mar 2024|
|[find_asset.py](find_asset/README.md)| Scans all compartments to find all Migration Assets, originated from the specific Source Asset.| CloudShell| 28 Mar 2024|
|[cleanup_volumes.py](cleanup_volumes/README.md)|Terminates unattached volumes.|CloudShell|27 Mar 2024|
|[migration_project_rename_aws_asset.py](migration_project_rename_aws_asset/README.md)|Renames AWS EC2 Migration Assets based on AWS tag name.|CloudShell|27 Mar 2024|
|[SetupWorkloads.ps1](setup_workloads/README.md)|Helpful scripts for setting up a training lab.|PowerShell|18 Apr 2024|