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
