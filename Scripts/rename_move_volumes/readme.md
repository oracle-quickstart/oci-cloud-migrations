# OCM Rename and move boot and block volumes

A Python utility for Oracle Cloud Infrastructure (OCI) that finds and fixes boot and block volumes left behind in a migration compartment after instances are launched elsewhere.

## Background

When workloads are migrated with the **Oracle Cloud Migration (OCM) Service**, compute instances are often created in a target compartment while their boot and block volumes remain in the original migration compartment. Those volumes typically keep auto-generated names from the migration process rather than meaningful names tied to the instance.

This script helps clean up that situation by:

1. Scanning compute instances in a specified compartment
2. Detecting attached boot and block volumes that are **not** in the same compartment as the instance
3. Optionally renaming and moving only the mismatched volumes to align with the compute instance

## What the script does

### Default mode (report only)

Without `-fix`, the script performs a read-only audit:

- Lists all active compute instances in the target compartment
- Checks each instance's attached boot and block volumes
- Reports any volume whose compartment differs from the instance compartment

### Fix mode (`-fix`)

With `-fix`, the script prepares changes **only for mismatched volumes**:

1. Shows a preview of every planned rename and compartment move
2. Prompts for confirmation (`y` / `yes` to proceed; anything else cancels)
3. **Phase 1 — Rename** mismatched volumes:
   - Boot volume → `{instance name} (Boot Volume)`
   - Block volumes → `{instance name} (Block Volume 01)`, `{instance name} (Block Volume 02)`, …
4. **Phase 2 — Move** those volumes into the same compartment as the compute instance

Volumes already in the correct compartment are not renamed or moved.

### Running the script

Easiest way to run this script is from the OCI Cloud Shell:
```
git clone https://github.com/oracle-quickstart/oci-cloud-migrations.git
cd Scripts/rename_move_volumes
python ocm-fixstorage.py -c [compartmentOCID or (partial) name of compartment]
```

Specify in the example above, in which compartment you want to check the compute instances.


Fixing any mismatches, use the -fix option
```
python ocm-fixstorage.py -c [compartmentOCID or (partial) name of compartment] -fix
```




### Alternative way to run script

You can run the script from any place where you have the OCI CLI configured with the correct authentication (likely in an .OCI\config file)

