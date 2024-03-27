import oci
import os
import sys

def confirm():
	answer = input("[Y]es or [N]o: ")
	if answer.strip().lower() not in ('y', 'n'):
		print("Invalid Option. Please Enter a Valid Option.")
		return confirm() 
	return answer

migration_project = str(sys.argv[1])
tenancy_id = os.environ.get('OCI_TENANCY')
config = oci.config.from_file()

cloud_migrations_client = oci.cloud_migrations.MigrationClient(config)
cloud_bridge_client = oci.cloud_bridge.InventoryClient(config)

migration_assets = cloud_migrations_client.list_migration_assets(migration_id=migration_project).data.items

for asset in migration_assets:
	source_asset = asset.source_asset_id
	migration_asset_name = asset.display_name
	aws_name = None
	aws_tags = cloud_bridge_client.get_asset(asset_id=source_asset).data.aws_ec2.tags
	for tag in aws_tags:
		if tag.key == "Name":
			aws_name = tag.value
			break
	if aws_name == None:
		print("No AWS name found for " + migration_asset_name)	
	elif migration_asset_name == aws_name:
		print("AWS name matches for " + migration_asset_name)	
	else:
		print("Rename " + migration_asset_name + " to " + aws_name + "?")
		if confirm().lower() == 'y':
			update_details=oci.cloud_migrations.models.UpdateMigrationAssetDetails(
				display_name=aws_name
			)
			cloud_migrations_client.update_migration_asset(
				migration_asset_id=asset.id,
				update_migration_asset_details=update_details)