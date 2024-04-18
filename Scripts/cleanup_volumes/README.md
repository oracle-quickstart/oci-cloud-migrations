# cleanup_volumes.py

## Overview
This script identifies and prompts to terminate unattached boot and data volumes related to a migration.

## Supported Environments
- CloudShell

## Usage

```
lgabriel@cloudshell:cleanup_volumes (us-ashburn-1)$ python cleanup_volumes.py <MIGRATION_COMPARTMENT_OCID>
Searching for compute compartments.
Found 2 compute compartments.
Collecting boot and data volume attachments.
Collecting boot volumes in the Migration compartment.
Collecting data volumes in the Migration compartment.
Delete unattached boot volume (I_6000C293-2fd8-1df5-37f5-447f7b23da1b_2024.03.27.22.10.20.071) for ol8_02_LGABRIEL?
[Y]es or [N]o: n
Delete unattached boot volume (I_6000C293-fa7a-dcc4-d84b-374edc6ea5dc_2024.03.27.22.11.05.033) for ol8_01_LGABRIEL?
[Y]es or [N]o: n
Delete unattached boot volume (I_6000C296-04b9-7db6-ef9b-445c23b63932_2024.03.27.22.11.34.572) for ubuntu22_01_LGABRIEL?
[Y]es or [N]o: n
Delete unattached boot volume (I_6000C292-64a1-d428-d6b6-3edd50f44de8_2024.03.27.22.11.46.339) for win2016_01_LGABRIEL?
[Y]es or [N]o: n
Delete unattached data volume (I_6000C29d-cd58-18c9-e414-120cc0716d82_2024.03.27.22.10.35.691) for ol8_02_LGABRIEL?
[Y]es or [N]o: n
Delete unattached data volume (I_6000C29f-84c3-6bc1-80e0-98a162ca82b4_2024.03.27.22.10.47.335) for ol8_02_LGABRIEL?
[Y]es or [N]o: n
Delete unattached data volume (I_6000C292-8c11-2db7-a5c3-bff2903a59c2_2024.03.27.22.11.21.542) for ubuntu22_01_LGABRIEL?
[Y]es or [N]o: n
lgabriel@cloudshell:cleanup_volumes (us-ashburn-1)$ 
```