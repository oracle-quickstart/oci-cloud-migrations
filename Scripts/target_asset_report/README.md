# OCI Cloud Migrations Target Asset Reporting Tool

This script generates a migration reporting table for a given OCI compartment by walking through:

- Migration Projects (migrations)
- Migration Plans for each project
- Target Assets for each plan

For each target asset, it reports:

- Project and plan names
- Target asset name
- Target asset lifecycle state
- Excluded-from-execution flag
- `recommended_spec` JSON (non-null values only)
- `user_spec` JSON (non-null values only)

The report is printed as a Markdown table and also saved to an Excel file (`.xlsx`).

## Goal

Provide a single report that helps compare migration target assets and their non-null specification details across all projects/plans in a compartment.

## Parameters

- `-cp <profile>`: OCI config profile name (default: `DEFAULT`)
- `-ip`: Use Instance Principals authentication
- `-dt`: Use Delegation Token authentication (Auto selected when running in cloud shell)
- `-log [file]`: Also write output to a log file (default file when omitted: `log.txt`)
- `-c, --compartment-id <ocid>`: Compartment OCID to query (defaults to tenancy OCID when omitted)
- `--excel-file <filename.xlsx>`: Excel output file name (default: `migration_report.xlsx`)

## Usage

Install dependencies first:

```bash
pip install -r requirements.txt
```

```bash
python target_report.py -cp DEFAULT -c <compartment_ocid> --excel-file migration_report.xlsx
```