import argparse
import oci, oci.exceptions
import json
import re
import sys
import os

def parse_ocid(ocid):
    pattern = '^ocid1\.([a-z0-9]+)\.([a-z0-9]+)*\.([a-z0-9\-]+)\.[a-z0-9]{60}'
    match = re.match(pattern, ocid)
    if not match:
        return False
    return {
        'type': match.group(1),
        'realm': match.group(2),
        'region': match.group(3)
    }

def eprint(*args):
    print(*args, file=sys.stderr)

if (__name__ == '__main__'):
    parser = argparse.ArgumentParser(description='Edits boot order of disks for an source asset.')
    parser.add_argument('ocid', type=str, help='OCID of a target asset')
    parser.add_argument('-b', '--boot-disk', dest='boot_disk_index', help='Index of a boot disk starting from 0')

    args = parser.parse_args()

    source_asset_id = args.ocid
    parsed_asset_id = parse_ocid(source_asset_id)
    if not parsed_asset_id or parsed_asset_id['type'] != 'ocbinventoryasset':
        eprint(f'Invalid source asset id was passed: {source_asset_id}')
        exit(1)

    tenancy_id = os.environ.get('OCI_TENANCY')
    config = oci.config.from_file()
    cloud_bridge_client = oci.cloud_bridge.InventoryClient(config)

    asset = cloud_bridge_client.get_asset(asset_id=source_asset_id).data

    if not args.boot_disk_index:
        print(str(asset.compute.disks))
    else:
        if not args.boot_disk_index.isdigit:
            eprint(f'Invalid boot disk index: {args.boot_disk_index}')
            exit(1)
        
        if len(asset.compute.disks) <= int(args.boot_disk_index):
            eprint(f'Too large boot disk index: {args.boot_disk_index}, compute.disks array: {asset.compute.disks}')
            exit(1)

        for disk in asset.compute.disks:
            disk.boot_order = None
        
        asset.compute.disks[int(args.boot_disk_index)].boot_order = 0

        update_asset_response = cloud_bridge_client.update_asset(asset_id=source_asset_id, update_asset_details=asset)
        if update_asset_response.status != 200:
            eprint(f'Failed to update source asset resource. Status: {update_asset_response.status}, Error: {update_asset_response.data}')
        else:
            print(update_asset_response.data.compute.disks)



