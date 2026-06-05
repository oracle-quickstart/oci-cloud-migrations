# sanitize_tf_json_resources.py

## Overview

This script renames Terraform JSON resource files so resource labels do not contain dots. It also updates JSON keys and string references in the same directory so Terraform configuration continues to point at the renamed resources.

For each `.json` or `.tf.json` file in the target directory, the script:

- Loads the JSON document.
- Treats files with a top-level `resource` block as Terraform resource files.
- Replaces dots in the filename stem with underscores.
- Rewrites matching JSON keys and string values across all JSON files in the directory.
- Writes the updated JSON with two-space indentation.

Example rename:

```text
my.resource.tf.json -> my_resource.tf.json
```

## Requirements

- Python 3
- No external Python packages

## Usage

Run against the current directory:

```bash
python3 sanitize_tf_json_resources.py
```

Run against a specific directory:

```bash
python3 sanitize_tf_json_resources.py /path/to/terraform-json
```

Preview planned changes without modifying files:

```bash
python3 sanitize_tf_json_resources.py --dry-run /path/to/terraform-json
```

## Output

When changes are needed, the script prints each resource-name rewrite:

```text
Renamed: my.resource -> my_resource
```

With `--dry-run`, the prefix changes to:

```text
Would rename: my.resource -> my_resource
```

If no files need changes, it prints:

```text
No Terraform JSON resource files needed sanitizing.
```

## Safety Checks

The script stops before modifying files when:

- Multiple resource files would be renamed to the same target filename.
- A target filename already exists and is not part of the planned rename set.
- Rewriting JSON keys would create duplicate keys in the same object.

## Notes

- The script only processes files directly inside the target directory.
- It only updates files ending in `.json`, including `.tf.json`.
- It performs plain string replacements for the affected resource-name stems, so run `--dry-run` first and review the working tree before committing changes.
- Changes are written in place.
