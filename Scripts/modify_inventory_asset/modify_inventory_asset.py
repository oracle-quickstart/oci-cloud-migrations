import argparse
import oci
import re
import copy
from UniversalOCIAuth import create_signer

try:
    from prettytable import PrettyTable
except:
    pass

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

def ValidateInventoryAssetId(inventory_asset_id):
    parsed_asset_id = parse_ocid(inventory_asset_id)
    if not parsed_asset_id or parsed_asset_id['type'] != 'ocbinventoryasset':
        print("Invalid Inventory Asset OCID was given.")
        raise SystemExit

def GetInventoryAsset (config, signer):
    cloud_bridge_client = oci.cloud_bridge.InventoryClient(config, signer=signer)
    try:
        inventory_asset = cloud_bridge_client.get_asset(asset_id=inventory_asset_id).data
    except Exception:
        raise
    return inventory_asset

def UpdateInventoryAsset (config, signer):
    cloud_bridge_client = oci.cloud_bridge.InventoryClient(config, signer=signer)
    update_asset_response = cloud_bridge_client.update_asset(asset_id=inventory_asset_id, update_asset_details=asset)
    if update_asset_response.status != 200:
            print("Failed to update Inventory Asset.")
            print("Error: " + update_asset_response.data)

def ExcludeDisk (disk_number):
    if len(asset.compute.disks) <= disk_number:
            print("Invalid Disk Number.")
            return
    
    print("Excluding disk.")
    asset.compute.disks.pop(disk_number)

def ChangeBootDisk (disk_number):
    if len(asset.compute.disks) <= disk_number:
            print("Invalid Disk Number.")
            return
    
    print("Changing boot disk.")
    for disk in asset.compute.disks:
            disk.boot_order = None
        
    asset.compute.disks[disk_number].boot_order = 0

def ChangeFirmware (new_firmware):
    if new_firmware == asset.compute.firmware:
            return
    
    print("Changing firmware.")
    asset.compute.firmware = new_firmware

def MungeAWSAssetTimestamps ():
    ## Discovery timestamp format is not compatible with AssetUpdate format.
    print("Modifying AWS Timestamps.")
    asset.aws_ec2.time_launch = asset.time_created
    for index, network_interface in enumerate(asset.aws_ec2.network_interfaces):
        asset.aws_ec2.network_interfaces[index].attachment.time_attach = asset.time_created

def PrintDiskTable (title, inventory_asset):
    table = PrettyTable(["Disk Number", "Disk Name", "Boot Order", "Size in MB", "UUID"]) 
     
    for index, disk in enumerate(asset.compute.disks):
        table.add_row([index,disk.name,disk.boot_order,disk.size_in_mbs,disk.uuid]) 
    print(title + ":")
    print(table)

def PrintDisks (title, inventory_asset):
    header = ["Disk Number", "Disk Name", "Boot Order", "Size in MB", "UUID"]
    print(title + ":")
    print(header)
    for index, disk in enumerate(asset.compute.disks):
        record = [index,disk.name,disk.boot_order,disk.size_in_mbs,disk.uuid]
        print(record)

def PrintFirmware (title, inventory_asset):
    print(title + ": " + inventory_asset.compute.firmware)

def GetAuthSetting (parsed_args):
    if parsed_args.is_instance_principal:
        return str("Instance Principal")
    elif parsed_args.is_delegation_token:
        return str("Delegation Token")
    elif parsed_args.is_security_token:
        return str("Security Token")
    else:
        return str("API Key")

if (__name__ == '__main__'):
    parser = argparse.ArgumentParser(description='Modify an Inventory Asset.')
    parser.add_argument('-p', '--profile', default="", dest='config_profile', help='Config file profile to use.')
    auth_type = parser.add_mutually_exclusive_group(required=False)
    auth_type.add_argument('-ip', '--instance-principal', action='store_true', default=False, dest='is_instance_principal', help='Use Instance Principals for Authentication')
    auth_type.add_argument('-cs', '--cloud-shell', action='store_true', default=False, dest='is_delegation_token', help='Use Delegation Token for Authentication')
    auth_type.add_argument('-st', '--security-token', action='store_true', default=False, dest='is_security_token', help='Use Security Token for Authentication')
    disk_modification = parser.add_mutually_exclusive_group(required=False)
    disk_modification.add_argument('-b', '--boot-disk', type=int, dest='boot_disk_number', help='Disk number to be set as boot')
    disk_modification.add_argument('-e', '--exclude-disk', type=int, dest='exclude_disk_number', help='Disk number to exclude')
    parser.add_argument('-f', '--firmware', dest='firmware_value', choices=['bios', 'efi'], help='Type of firmware to set.')
    parser.add_argument('ocid', type=str, help='OCID of the Inventory Asset.')
  
    cmd = parser.parse_args()
    inventory_asset_id = cmd.ocid

    ValidateInventoryAssetId(inventory_asset_id)

    config, signer = create_signer(cmd.config_profile, cmd.is_instance_principal, cmd.is_delegation_token, cmd.is_security_token)
    tenant_id = config['tenancy']
    try:
        asset = GetInventoryAsset(config, signer)
    except Exception:
        print("ERROR: Failed to get Inventory Asset using " + GetAuthSetting(cmd) + ".")
        raise SystemExit

    original_asset = copy.deepcopy(asset)

    print("Inventory Asset Name: " + asset.display_name)
    PrintFirmware("Current Firmware", asset)
    try:
        PrintDiskTable("Current Disks", asset)
    except:
        PrintDisks("Current Disks", asset)

    ## Modify Inventory Asset
    modified = False
    if cmd.boot_disk_number or cmd.boot_disk_number == 0:
        ChangeBootDisk(cmd.boot_disk_number)
        modified = True
    if cmd.exclude_disk_number or cmd.exclude_disk_number == 0:
        ExcludeDisk(cmd.exclude_disk_number)
        modified = True
    if cmd.firmware_value:
        ChangeFirmware(cmd.firmware_value)
        modified = True
    if not modified:
        raise SystemExit
    
    ## Update Inventory Asset
    if original_asset != asset:
        if asset.asset_type == "AWS_EC2":
            MungeAWSAssetTimestamps()

        UpdateInventoryAsset(config, signer)

        new_asset = GetInventoryAsset(config, signer)
        print("New Inventory Details")
        PrintFirmware("New Firmware", new_asset)
        try:
            PrintDiskTable("New Disks", new_asset)
        except:
            PrintDisks("New Disks", new_asset)
    else:
        print("No new values provided. Inventory Asset unchanged.")