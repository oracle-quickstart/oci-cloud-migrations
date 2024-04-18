# migration_project_rename_aws_asset.py

# LIMITED AVAILABILITY ONLY
This script is only useful for tenancies that are part of the Limited Availability of AWS EC2 Asset Sources.

## Overview
This script renames AWS EC2 Migration Assets based on their AWS name tag. 

## Supported Environments
- CloudShell

## Requirements
This script requires a Preview SDK that supports AWS EC2 Asset Sources.

## Python Virtual Environment and Preview SDK Setup

A Virtual Environment can be setup in CloudShell.

```
lgabriel@cloudshell:~ (us-ashburn-1)$ python -m venv venv/rename_aws_asset
lgabriel@cloudshell:~ (us-ashburn-1)$ source venv/rename_aws_asset/bin/activate
(rename_aws_asset) lgabriel@cloudshell:~ (us-ashburn-1)$ pip install oci-2.93.2+preview.1.1560-py3-none-any.whl
(rename_aws_asset) lgabriel@cloudshell:~ (us-ashburn-1)$ pip install --force-reinstall -v "pyopenssl==22.0.0"
(rename_aws_asset) lgabriel@cloudshell:migration_project_rename_aws_asset (us-ashburn-1)$ deactivate
```

## Usage

```
lgabriel@cloudshell:~ (us-ashburn-1)$ source venv/rename_aws_asset/bin/activate
(rename_aws_asset) lgabriel@cloudshell:~ (us-ashburn-1)$ cd oci-cloud-migrations/Scripts/Migration/migration_project_rename_aws_asset/
(rename_aws_asset) lgabriel@cloudshell:migration_project_rename_aws_asset (us-ashburn-1)$ python migration_project_rename_aws_asset.py <MIGRATION_PROJECT_OCID>
Rename i-0eac1e079449cbc7c to ubuntu22-001?
[Y]es or [N]o: y
Rename i-04d89eb2dc582999c to lab-bastion?
[Y]es or [N]o: y
(rename_aws_asset) lgabriel@cloudshell:migration_project_rename_aws_asset (us-ashburn-1)$ python migration_project_rename_aws_asset.py <MIGRATION_PROJECT_OCID>
AWS name matches for ubuntu22-001
AWS name matches for lab-bastion
(rename_aws_asset) lgabriel@cloudshell:migration_project_rename_aws_asset (us-ashburn-1)$ deactivate
```
