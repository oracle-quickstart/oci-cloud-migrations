check "secondary_requires_migration_compartment" {
  assert {
    condition     = local.migration_compartment_available
    error_message = "Secondary prerequisite stacks require an existing 'Migration' compartment under the selected Migration Root Compartment. Run the primary prerequisite stack first (or select the correct root compartment), then rerun this secondary stack."
  }
}

check "secondary_requires_migration_secrets_compartment" {
  assert {
    condition     = local.migration_secrets_compartment_available
    error_message = "Secondary prerequisite stacks require an existing 'MigrationSecrets' compartment under the selected Migration Root Compartment. Run the primary prerequisite stack first (or select the correct root compartment), then rerun this secondary stack."
  }
}

check "primary_requires_clean_migration_compartment_name" {
  assert {
    condition     = !local.migration_compartment_name_conflict
    error_message = "Primary prerequisite stacks create a child compartment named 'Migration' under the selected Migration Root Compartment. A compartment with that name already exists, which usually means a prior partial run or manual setup. Reuse that existing setup by rerunning this as a secondary prerequisite stack if it is the intended OCM compartment, or delete/rename the conflicting compartment before rerunning the primary stack."
  }
}

check "primary_requires_clean_migration_secrets_compartment_name" {
  assert {
    condition     = !local.migration_secrets_compartment_name_conflict
    error_message = "Primary prerequisite stacks create a child compartment named 'MigrationSecrets' under the selected Migration Root Compartment. A compartment with that name already exists, which usually means a prior partial run or manual setup. Reuse that existing setup by rerunning this as a secondary prerequisite stack if it is the intended OCM secrets compartment, or delete/rename the conflicting compartment before rerunning the primary stack."
  }
}

check "primary_requires_clean_tag_namespace_name" {
  assert {
    condition     = !local.migration_tag_namespace_collision
    error_message = "Primary prerequisite stacks create the 'CloudMigrations' tag namespace in the tenancy home region. That namespace already exists, which usually means a prior partial run or existing prerequisite setup. If the namespace belongs to the existing OCM prerequisite stack, rerun with 'Primary Prerequisite Stack' unchecked and reuse it. Otherwise remove or rename the conflicting namespace before rerunning the primary stack."
  }
}

check "primary_requires_clean_dynamic_group_names" {
  assert {
    condition     = length(local.conflicting_dynamic_group_names) == 0
    error_message = "Primary prerequisite stacks create OCM service dynamic groups in the tenancy home region. The following dynamic group names already exist: ${join(", ", local.conflicting_dynamic_group_names)}. This usually means a prior partial run or existing prerequisite setup. Reuse the existing prerequisite resources with a secondary stack if they are intentional, or delete/rename the conflicting dynamic groups before rerunning the primary stack."
  }
}

check "primary_requires_clean_policy_names" {
  assert {
    condition     = length(local.conflicting_policy_names) == 0
    error_message = "Primary prerequisite stacks create tenancy and compartment IAM policies for OCM. The following policy names already exist: ${join(", ", local.conflicting_policy_names)}. This usually means a prior partial run or existing prerequisite setup. Reuse the existing prerequisite resources with a secondary stack if they are intentional, or delete/rename the conflicting policies before rerunning the primary stack."
  }
}
