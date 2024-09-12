import oci

BOAT = True

## BOAT Authentication
if BOAT:
        config = oci.config.from_file(profile_name='m360')
        token_file = config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
                token = f.read()
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        tenancy_id = config['tenancy']
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        migration_client = oci.cloud_migrations.MigrationClient({'region': config['region']}, signer=signer)
        migration_composite_client = oci.cloud_migrations.MigrationClientCompositeOperations(migration_client)
else:
        ## CloudShell
        config = oci.config.from_file()
        tenancy_id = config['tenancy']
        migration_client = oci.cloud_migrations.MigrationClient(config)
        migration_composite_client = oci.cloud_migrations.MigrationClientCompositeOperations(migration_client)

print("Generating RMS Stack.")
# rms_stack = migration_client.execute_migration_plan(migration_plan_id = migration_plan_ocid)
# print(rms_stack.headers["opc-work-request-id"])

rms_stack = migration_composite_client.execute_migration_plan_and_wait_for_state(
        migration_plan_id = migration_plan_ocid,
        wait_for_states = [
                oci.cloud_migrations.models.WorkRequest.STATUS_SUCCEEDED,
                oci.cloud_migrations.models.WorkRequest.STATUS_FAILED,
                oci.cloud_migrations.models.WorkRequest.STATUS_CANCELED
        ]
)

migration_plan_details = migration_client.get_migration_plan(migration_plan_id=migration_plan_ocid).data

print("Done.")
print("Stack OCID: " + migration_plan_details.reference_to_rms_stack)