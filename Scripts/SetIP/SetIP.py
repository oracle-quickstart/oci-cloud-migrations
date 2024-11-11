import oci
import sys
import argparse
import os
import ipaddress

configfile = "~/.oci/config"
configProfile = "DEFAULT"

def create_signer(config_profile, is_instance_principals, is_delegation_token):

    # Instance principals authentications - for use with OCI Dynamic Groups
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("Error obtaining instance principals certificate, aborting")
            sys.exit(-1)

    # Delegation Token authentications - for use with OCi Cloud Shell
    elif is_delegation_token:

        print ("Using delegation token - should only run in cloud shell")
        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print("*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                print("")
                sys.exit(-1)

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("* Key Error obtaining delegation_token_file")
            sys.exit(-1)

        except Exception:
            raise

    # Config file authentications - for use with OCI Config file
    else:
        try:
            config = oci.config.from_file(
                oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
        except:
            print("Error obtaining authentication, did you configure config file? aborting")
            sys.exit(-1)

        return config, signer


def input_command_line(help=False):
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=130))
    parser.add_argument('-cp', default="", dest='config_profile', help='Config Profile inside the config file')
    parser.add_argument('-ip', action='store_true', default=False, dest='is_instance_principals', help='Use Instance Principals for Authentication')
    parser.add_argument('-dt', action='store_true', default=False, dest='is_delegation_token', help='Use Delegation Token for Authentication')
    parser.add_argument("-rg", default="", dest='region', help="Region")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-targetasset_id", default="", dest='targetOCID', help="Target Asset OCID")
    group.add_argument("-migrationplan_id", default="", dest='migrationPlanOCID', help="Migration Plan OCID")
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument("-fixip", action='store_true', default=False, dest='fixip', help="Set static IP to existing Static IP")
    group2.add_argument("-ipmap", default="", dest='ipmap', help="Set static IP to mappings based in a file")
    group2.add_argument("-tagmap", action='store_true', default=False, dest='tagmap', help="Set static IP based on free form tags on the migration plan")
    group2.add_argument("-vcenter", action='store_true', default=False, dest='vcenter', help="Set static IP based on vCenter Customer attributes")

    cmd = parser.parse_args()
    if help:
        parser.print_help()
    return cmd

def clearLine():
    print("\033[A                                                                                                            \033[A")

def is_valid_ip(ip_string):
    try:
        # Attempt to create an IPv4 or IPv6 address object
        ipaddress.ip_address(ip_string)
        return True  # If no exception, it’s a valid IP address
    except:
        return False  # If exception occurs, it's not a valid IP address

# Get OCM Target Asset (Part of the OCM Migration Plan)
def getTarget(region, targetID, signer):
    migrations = oci.cloud_migrations.MigrationClient(config, signer=signer)
    data = migrations.get_target_asset(target_asset_id=targetID).data
    return data

def processTarget(region, targetID, cmd, signer):
    print(f"Getting {cmd.targetOCID}")
    migrations = oci.cloud_migrations.MigrationClient(config, signer=signer)
    network = oci.core.VirtualNetworkClient(config, signer=signer)
    target = migrations.get_target_asset(target_asset_id=targetID).data
    if target:
        migration_asset = target.migration_asset
        source_asset = migration_asset.source_asset_data
        computeNics = source_asset['compute']['nics']
        clearLine()
        print(f"VM: {source_asset['displayName']}")
        # Get the Target's assigned OCI VCN/Subnet
        try:
            targetSubnetOCID = target.user_spec.create_vnic_details.subnet_id
        except:
            targetSubnetOCID = target.recommended_spec.create_vnic_details.subnet_id
        if not targetSubnetOCID:
            targetSubnetOCID = target.recommended_spec.create_vnic_details.subnet_id

        if targetSubnetOCID:
            subnetDetails = network.get_subnet(subnet_id=targetSubnetOCID).data
            print (f" - Target OCI Subnet: {subnetDetails.display_name} [{subnetDetails.cidr_block}]")

            foundMatch = False
            # Set IP based on source IP Address
            if cmd.fixip:
                IPs = ""
                # Find know IP address of the source VM that matches the OCI VCN/Subnet range
                for nic in computeNics:
                    if len(nic['ipAddresses']) > 0:
                        IPs = IPs + nic['ipAddresses'][0] + " "
                        if ipaddress.ip_address(nic['ipAddresses'][0]) in ipaddress.ip_network(subnetDetails.cidr_block):
                            MappedIP = nic['ipAddresses'][0]
                            foundMatch = True
                            break
                    else:
                        print (" - No source IP Address found")
                if not foundMatch:
                    print (" - No possible IP match found to target subnet: " + IPs)

            # Set IP based on matching IP:VM_name in ipmapping file
            if cmd.ipmap:
                if os.path.exists(cmd.ipmap):
                    with open(cmd.ipmap, "r") as file:
                        for line in file:
                            mapip, vmname = line.strip().split(";")
                            if vmname == source_asset['displayName']:
                                MappedIP = mapip
                                foundMatch = True
                                break
                else:
                    print ("IP Map file not found")
                    exit()

            # Set IPs based on Free form tags on the migration plan
            # format should be: key: vmname value:ipaddress
            if cmd.tagmap:
                plan = migrations.get_migration_plan(migration_plan_id=target.migration_plan_id).data
                for tag_vm, tag_ip in plan.freeform_tags.items():
                    if tag_vm == source_asset['displayName']:
                        MappedIP = tag_ip
                        foundMatch = True
                        break

            if cmd.vcenter:
                customFields = source_asset['vmwareVm']['customerFields']
                for customField in customFields:
                    if customField.startswith("OCI:"):
                        prefix , MappedIP = customField.strip().split(":")
                        foundMatch = True
                        break

            if foundMatch:
                migration_asset = target.migration_asset
                user_spec = oci.cloud_migrations.models.launch_instance_details.LaunchInstanceDetails()
                user_spec = target.user_spec
                source_asset = migration_asset.source_asset_data

                conflict = False
                # Check if IP addres is valid
                if is_valid_ip(MappedIP):
                    pass
                else:
                    print (" - ERROR: Mapped IP is not valid IP address: {}".format(MappedIP))
                    conflict = True

                # Check if IP address is part of subnet CIDR
                if not conflict:
                    if ipaddress.ip_address(MappedIP) in ipaddress.ip_network(subnetDetails.cidr_block):
                        pass
                    else:
                        print (" - Mapped IP [{}] does not match target subnet [{}]".format(mapip,subnetDetails.cidr_block))
                        conflict = True

                # Check IP address does not conflict with default gateway of the subnet
                if not conflict:
                    if ipaddress.ip_address(MappedIP) == ipaddress.ip_network(subnetDetails.cidr_block)[0]:
                        print (" - CONFLICT - You can not use the broadcast address [{}] in the CIDR range [{}]".format(MappedIP, subnetDetails.cidr_block))
                        conflict = True
                    if ipaddress.ip_address(MappedIP) == ipaddress.ip_network(subnetDetails.cidr_block)[1]:
                        print (" - CONFLICT - You can not use the first available address [{}] in the CIDR range [{}], this is reservered for the gateway".format(MappedIP, subnetDetails.cidr_block))
                        conflict = True

                # Get OCI Subnet currently used IPs and check for conflict
                if not conflict:
                    print (" - Checking for IP Conflicts...")
                    ip_inventory = network.get_subnet_ip_inventory(subnet_id=targetSubnetOCID).data
                    for usedIP in ip_inventory.ip_inventory_subnet_resource_summary:
                        if usedIP.ip_address == MappedIP:
                            clearLine()
                            print (" - CONFLICT - Trying to assign IP {}, but is already been used by {} - {}".format(MappedIP, usedIP.dns_host_name, usedIP.ip_id))
                            print (" ")
                            conflict = True
                            break
                    clearLine()

                # Set validated mapped IP to the Target Asset
                if not conflict:
                    vnic_details = oci.cloud_migrations.models.CreateVnicDetails()
                    vnic_details.private_ip = MappedIP
                    vnic_details.subnet_id = targetSubnetOCID
                    user_spec.create_vnic_details = vnic_details
                    print(f" - Setting target ip to [{MappedIP}]")
                    migrations = oci.cloud_migrations.MigrationClient(config, signer=signer)
                    update_details = oci.cloud_migrations.models.UpdateTargetAssetDetails()
                    target_details = oci.cloud_migrations.models.UpdateVmTargetAssetDetails()
                    target_details.type = "INSTANCE"
                    target_details.user_spec = user_spec
                    try:
                        result = migrations.update_target_asset(target_asset_id=targetID,update_target_asset_details=target_details, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
                    except oci.exceptions.ServiceError as response:
                        print (" - ERROR: {}-{}".format(response.code, response.message))
            else:
                print (" - No IP match found, no fixed mapped applied")

        else:
            print (" - Error - No OCI Subnet assign to this target")


cmd = input_command_line()
configProfile = cmd.config_profile if cmd.config_profile else configProfile
config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)

if cmd.region:   # Override default region when a specific region is specified as parameter
    config["region"] = cmd.region

identity = oci.identity.IdentityClient(config, signer=signer)
tenancy = identity.get_tenancy(config['tenancy']).data

print ("Oracle Cloud Migrations (OCM) - Target Asset fixed IP tool")
print ("Tenancy: {}".format(tenancy.name))

# Process one individual Target Asset
if cmd.targetOCID:
    processTarget(config["region"], cmd.targetOCID, cmd, signer)

# Process all Target Assets in one Migration Plan
elif cmd.migrationPlanOCID:
    migrations = oci.cloud_migrations.MigrationClient(config, signer=signer)
    targets = migrations.list_target_assets(migration_plan_id=cmd.migrationPlanOCID).data.items
    for target in targets:
        processTarget(config["region"], target.id, cmd, signer)
else:
    print ("Please specify target asset OCID or Migration Plan OCID")
