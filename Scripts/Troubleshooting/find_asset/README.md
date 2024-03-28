# find_asset.py

## Overview
This script scans all compartments and lists all Migration Assets, originated from the Source Asset, which `id`, `displayName` or `externalAssetKey` matches script argument.

## Supported Environments
- CloudShell

## Usage
```
ansokolo@cloudshell:~ (us-ashburn-1)$ python ./find_asset.py WindowsServer2022Std
Scanning compartment amb
Scanning compartment CompA
Scanning compartment ocb-user\CompA\CompAA
Scanning compartment ocb-user\CompA\CompAB
Scanning compartment ocb-user\CompA\CompAC
Scanning compartment ManagedCompartment
        Unable to list migration projects. Status: 404, code: NotAuthorizedOrNotFound, message: Authorization failed or requested resource not found.
Scanning compartment ocb-user
        Migration: egolenko-project
Found compartment: ocb-user, migration project: ocid1.ocmmigration.oc1.iad.amaaaaaabkvoaqqa6r46imxqtwplyoj4ulkgdu3nmmic5pyqiirslv44e2eq, state: ACTIVE, migration asset:ocid1.ocmmigrationasset.oc1.iad.amaaaaaa556ckoia5bjs5tw26ty2pxeoen4jqvgammkmldocuuhopqf3ytza, state: ACTIVE
        Migration: migration_2023-0511-1447
Scanning compartment vSphere-compartment
Scanning compartment hgf-poc
```