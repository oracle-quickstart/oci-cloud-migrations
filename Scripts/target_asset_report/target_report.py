import sys
import json
import oci
from openpyxl import Workbook

from ocimodules.functions import input_command_line, create_signer, MyWriter
from ocimodules.IAM import Login


def _prune_nulls(value):
    """Return object with null values removed recursively."""
    if value is None:
        return None

    if isinstance(value, dict):
        cleaned = {}
        for key, nested_value in value.items():
            pruned = _prune_nulls(nested_value)
            if pruned is not None:
                cleaned[key] = pruned
        return cleaned if cleaned else None

    if isinstance(value, list):
        cleaned_list = []
        for nested_value in value:
            pruned = _prune_nulls(nested_value)
            if pruned is not None:
                cleaned_list.append(pruned)
        return cleaned_list if cleaned_list else None

    return value


def _escape_markdown_cell(value):
    text = str(value) if value is not None else ""
    return text.replace("|", "\\|").replace("\n", "<br>")


# Disable OCI CircuitBreaker feature
oci.circuit_breaker.NoCircuitBreakerStrategy()

#################################################
#           Application Configuration           #
#################################################
min_version_required = "2.164.0"
application_version = "11.03.2026"


##########################################################################
# Main Program
##########################################################################

print ("OCI - Oracle Cloud Migration reporting tool")
print ("This utility help you to report the target assets in all the migration projects/plans in a compartment")
print ("=======================================================================================================")
print ("")

# Check command line parameters
cmd = input_command_line()

# if logging to file, overwrite default print function to also write to file
if cmd.log_file != "":
    writer = MyWriter(sys.stdout, cmd.log_file)
    sys.stdout = writer

#################################################
# oci config and "login" check
######################################################
config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)
tenant_id = config['tenancy']

compartments= Login(config, signer, tenant_id, get_compartments=False)
print(f"Current configured region is: {config['region']}")

# Use user-provided compartment OCID, fallback to tenancy OCID.
target_compartment_id = cmd.compartment_id if cmd.compartment_id else tenant_id
print(f"Target compartment OCID: {target_compartment_id}")
print("")

migration_client = oci.cloud_migrations.MigrationClient(config=config, signer=signer)

try:
    migrations = oci.pagination.list_call_get_all_results(
        migration_client.list_migrations,
        compartment_id=target_compartment_id
    ).data
except oci.exceptions.ServiceError as e:
    print(f"Unable to list migration projects/migrations: {e.message}")
    raise

if not migrations:
    print("No migration projects found in the selected compartment.")
    raise SystemExit(0)

print(f"Found {len(migrations)} migration project(s):")
print("")

table_rows = []

for idx, migration in enumerate(migrations, 1):
    migration_name = getattr(migration, "display_name", migration.id)

    plans = oci.pagination.list_call_get_all_results(
        migration_client.list_migration_plans,
        compartment_id=target_compartment_id,
        migration_id=migration.id
    ).data

    if not plans:
        continue

    for pidx, plan in enumerate(plans, 1):
        plan_name = getattr(plan, "display_name", plan.id)

        target_assets = oci.pagination.list_call_get_all_results(
            migration_client.list_target_assets,
            migration_plan_id=plan.id
        ).data

        if not target_assets:
            table_rows.append({
                "project_name": migration_name,
                "plan_name": plan_name,
                "target_asset_name": "",
                "target_asset_lifecycle_state": "",
                "excluded_from_execution": "",
                "recommended_spec_json": "",
                "user_spec_json": ""
            })
            continue

        for aidx, asset in enumerate(target_assets, 1):
            asset_name = getattr(asset, "display_name", getattr(asset, "id", "unknown"))
            asset_id = getattr(asset, "id", "n/a")

            try:
                asset_details = migration_client.get_target_asset(asset_id).data
            except oci.exceptions.ServiceError as e:
                print(f"           unable to get target asset details: {e.message}")
                continue

            user_spec = getattr(asset_details, "user_spec", None)
            recommended_spec = getattr(asset_details, "recommended_spec", None)

            if user_spec is None:
                non_null_user_spec = None
            else:
                user_spec_dict = oci.util.to_dict(user_spec)
                non_null_user_spec = _prune_nulls(user_spec_dict)

            if recommended_spec is None:
                non_null_recommended_spec = None
            else:
                recommended_spec_dict = oci.util.to_dict(recommended_spec)
                non_null_recommended_spec = _prune_nulls(recommended_spec_dict)

            table_rows.append({
                "project_name": migration_name,
                "plan_name": plan_name,
                "target_asset_name": asset_name,
                "target_asset_lifecycle_state": getattr(asset_details, "lifecycle_state", ""),
                "excluded_from_execution": getattr(asset_details, "is_excluded_from_execution", ""),
                "recommended_spec_json": json.dumps(non_null_recommended_spec, sort_keys=True) if non_null_recommended_spec else "",
                "user_spec_json": json.dumps(non_null_user_spec, sort_keys=True) if non_null_user_spec else ""
            })

if not table_rows:
    print("No migration plans / target assets found for the selected compartment.")
    raise SystemExit(0)

print("Migration Report Table")
print("")
headers = [
    "Migration Project Name",
    "Migration Plan Name",
    "Target Asset Name",
    "Target Asset Lifecycle State",
    "Excluded From Execution",
    "Recommended Spec (JSON, Non-Null)",
    "User Spec (JSON, Non-Null)"
]
print("| " + " | ".join(headers) + " |")
print("|" + "|".join(["---"] * len(headers)) + "|")
excel_rows = []
for row in table_rows:
    row_values = [
        row["project_name"],
        row["plan_name"],
        row["target_asset_name"],
        row["target_asset_lifecycle_state"],
        row["excluded_from_execution"],
        row["recommended_spec_json"],
        row["user_spec_json"]
    ]
    excel_rows.append(row_values)

    print(
        "| " + " | ".join(_escape_markdown_cell(v) for v in row_values) + " |"
    )

# Save to Excel
workbook = Workbook()
sheet = workbook.active
sheet.title = "Migration Report"
sheet.append(headers)
for excel_row in excel_rows:
    sheet.append(excel_row)

workbook.save(cmd.excel_file)
print("")
print(f"Excel report saved: {cmd.excel_file}")

