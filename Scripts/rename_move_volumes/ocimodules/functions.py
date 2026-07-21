import argparse
import oci
import os
import re
import sys
import time

WaitRefresh = 10

class OCICompartments:
    fullpath = ""
    level = 0
    details = oci.identity.models.Compartment()

##########################################################################
# input_command_line
##########################################################################
def input_command_line(help=False):
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=130))
    parser.add_argument('-cp', default="DEFAULT", dest='config_profile', help='Config Profile inside the config file')
    parser.add_argument('-ip', action='store_true', default=False, dest='is_instance_principals', help='Use Instance Principals for Authentication')
    parser.add_argument('-dt', action='store_true', default=False, dest='is_delegation_token', help='Use Delegation Token for Authentication')
    parser.add_argument("-log", nargs='?', const='log.txt', default="", dest='log_file', help="Output also to logfile. If logfile not specified, will log to log.txt")
    parser.add_argument("-rg", default="", dest='region', help="Select Region")
    parser.add_argument("-c", required=True, dest='compartment', help="Select Compartment by specified OCID or (partial) name")
    parser.add_argument("-fix", action='store_true', default=False, dest='fix', help="Rename and move only mismatched attached volumes to the instance compartment")
    cmd = parser.parse_args()

    # If running in Cloud Shell (OCI_CLI_CLOUD_SHELL=true), default to Delegation Token
    if os.environ.get("OCI_CLI_CLOUD_SHELL", "").lower() == "true":
        print("Running in Cloud Shell..")
        cmd.is_delegation_token = True
        cmd.is_instance_principals = False
        cmd.config_profile = "DEFAULT"

    if help:
        parser.print_help()

    return cmd

##########################################################################
# Create signer for Authentication
# Input - config_profile and is_instance_principals and is_delegation_token
# Output - config and signer objects
##########################################################################
def create_signer(config_profile, is_instance_principals, is_delegation_token):

    # if instance principals authentications
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("Error obtaining instance principals certificate, aborting")
            sys.exit(-1)

    # -----------------------------
    # Delegation Token
    # -----------------------------
    elif is_delegation_token:

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

    # -----------------------------
    # config file authentication
    # -----------------------------
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
        except Exception:
            print("Error obtaining authentication, did you configure config file? aborting")
            sys.exit(-1)

        return config, signer

#################################################
#                 Login                 #
#################################################
def login(config, signer):
    print("OCI SDK Version: {}".format(oci.__version__))
    identity = oci.identity.IdentityClient(config, signer=signer)
    try: 
        user = identity.get_user(user_id=config["user"]).data
        print("Logged in as: {} @ {}".format(user.name, config["region"]))
    except Exception:
        print("Logged in as: {} @ {}".format("unknown", config["region"]))
        user = "IP-DT"


#################################################
#              GetHomeRegion
#################################################
def GetHomeRegion(config, signer):
    home_region = ""
    identity = oci.identity.IdentityClient(config, signer=signer)
    regionDetails = identity.list_region_subscriptions(tenancy_id=config["tenancy"]).data

    # Set home region for connection
    for reg in regionDetails:
        if reg.is_home_region:
            home_region = str(reg.region_name)

    return home_region

#################################################
#              GetTenantName
#################################################
def GetTenantName(config, signer):
    identity = oci.identity.IdentityClient(config, signer=signer)
    tenancy = identity.get_tenancy(config['tenancy']).data
    return tenancy.name

#################################################
#              SubscribedRegions
#################################################
def SubscribedRegions(config, signer):
    regions = []
    identity = oci.identity.IdentityClient(config, signer=signer)
    regionDetails = identity.list_region_subscriptions(tenancy_id=config["tenancy"]).data

    # Add subscribed regions to list
    for detail in regionDetails:
        regions.append(detail.region_name)

    return regions


#################################################
## Basic Get Compartments Function
#################################################
def GetCompartments(identity, rootID):
    retry = True
    while retry:
        retry = False
        try:
            compartments = oci.pagination.list_call_get_all_results(identity.list_compartments, compartment_id=rootID, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data
            return compartments
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                print("API busy.. retry", end="\r")
                retry = True
                time.sleep(WaitRefresh)
            else:
                print("bad error!: " + e.message)
    return []

#################################################
# Get compartments for the tenant
#################################################
def GetFullCompartments(config, signer):
    print("Getting full compartments for the tenant...")
    identity = oci.identity.IdentityClient(config, signer=signer)
    c = []
    compartment = oci.identity.models.Compartment()
    compartment.id = config["tenancy"]
    compartment.name = "root compartment"
    compartment.lifecycle_state = "ACTIVE"

    newcomp = OCICompartments()
    newcomp.details = compartment
    newcomp.fullpath = "/root"
    newcomp.level = 0
    c.append(newcomp)

    # Add first level subcompartments
    compartments = GetCompartments(identity, config["tenancy"])

    # Add 2nd level subcompartments
    fullpath = newcomp.fullpath + "/"
    for compartment in compartments:
        if compartment.lifecycle_state == "ACTIVE":
            newcomp = OCICompartments()
            newcomp.details = compartment
            newcomp.fullpath = "{}{}".format(fullpath, compartment.name)
            newcomp.level = 1
            c.append(newcomp)
            subcompartments = GetCompartments(identity, compartment.id)
            subpath1 = compartment.name
            for sub1 in subcompartments:
                if sub1.lifecycle_state == "ACTIVE":
                    newcomp = OCICompartments()
                    newcomp.details = sub1
                    newcomp.fullpath = "{}{}/{}".format(fullpath, subpath1, sub1.name)
                    newcomp.level = 2
                    c.append(newcomp)

                    subcompartments2 = GetCompartments(identity, sub1.id)
                    subpath2 = sub1.name
                    for sub2 in subcompartments2:
                        if sub2.lifecycle_state == "ACTIVE":
                            newcomp = OCICompartments()
                            newcomp.details = sub2
                            newcomp.fullpath = "{}{}/{}/{}".format(fullpath, subpath1, subpath2, sub2.name)
                            newcomp.level = 3
                            c.append(newcomp)

                            subcompartments3 = GetCompartments(identity, sub2.id)
                            subpath3 = sub2.name
                            for sub3 in subcompartments3:
                                if sub3.lifecycle_state == "ACTIVE":
                                    newcomp = OCICompartments()
                                    newcomp.details = sub3
                                    newcomp.fullpath = "{}{}/{}/{}/{}".format(fullpath, subpath1, subpath2, subpath3, sub3.name)
                                    newcomp.level = 4
                                    c.append(newcomp)

                                    subcompartments4 = GetCompartments(identity, sub3.id)
                                    subpath4 = sub3.name
                                    for sub4 in subcompartments4:
                                        if sub4.lifecycle_state == "ACTIVE":
                                            newcomp = OCICompartments()
                                            newcomp.details = sub4
                                            newcomp.fullpath = "{}{}/{}/{}/{}/{}".format(fullpath, subpath1, subpath2,
                                                                                         subpath3, subpath4, sub4.name)
                                            newcomp.level = 5
                                            c.append(newcomp)

                                            subcompartments5 = GetCompartments(identity, sub4.id)
                                            subpath5 = sub4.name
                                            for sub5 in subcompartments5:
                                                if sub5.lifecycle_state == "ACTIVE":
                                                    newcomp = OCICompartments()
                                                    newcomp.details = sub5
                                                    newcomp.fullpath = "{}{}/{}/{}/{}/{}/{}".format(fullpath, subpath1, subpath2, subpath3, subpath4, subpath5, sub5.name)
                                                    newcomp.level = 6
                                                    c.append(newcomp)

                                                    subcompartments6 = GetCompartments(identity, sub5.id)
                                                    subpath6 = sub5.name
                                                    for sub6 in subcompartments6:
                                                        if sub6.lifecycle_state == "ACTIVE":
                                                            newcomp = OCICompartments()
                                                            newcomp.details = sub6
                                                            newcomp.fullpath = "{}{}/{}/{}/{}/{}/{}/{}".format(
                                                                fullpath,
                                                                subpath1,
                                                                subpath2,
                                                                subpath3,
                                                                subpath4,
                                                                subpath5, subpath6,
                                                                sub6.name)
                                                            newcomp.level = 7
                                                            c.append(newcomp)

    return c

#################################################
## Resolve Compartment OCID to Full Path using the full list of compartments
#################################################
def GetCompartmentFullPath(compartments, ocid):
    """
    Given a list of OCICompartments objects and an OCID, 
    returns the full path of the compartment that matches the given OCID.
    If not found, returns None.
    """
    for compartment in compartments:
        if hasattr(compartment, "details") and getattr(compartment.details, "id", None) == ocid:
            return getattr(compartment, "fullpath", None)
    return None


#################################################
## Find compartment by OCID or display name
#################################################
def _confirm_compartment_match(specified, display_name, ocid):
    if display_name == specified:
        return True

    print("Found compartment: {} ({})".format(display_name, ocid))
    while True:
        answer = input("Use this compartment? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter y or n.")


def findCompartment(config, signer, compartment):
    """
    Resolve a compartment OCID from an OCID or display name.

    If compartment starts with ocid1., verify it exists via the Identity API.
    Otherwise search compartments by display name using OCI Resource Search.
    Returns the compartment OCID, or 0 if not found.
    """
    if not compartment:
        return 0

    identity = oci.identity.IdentityClient(config, signer=signer)

    if compartment.startswith("ocid1."):
        retry = True
        while retry:
            retry = False
            try:
                identity.get_compartment(compartment_id=compartment).data
                return compartment
            except oci.exceptions.ServiceError as e:
                if e.status == 404:
                    return 0
                if e.status == 429:
                    print("API busy.. retry", end="\r")
                    retry = True
                    time.sleep(WaitRefresh)
                else:
                    print("bad error!: " + e.message)
                    return 0
        return 0

    escaped_name = re.escape(compartment).replace('"', '\\"')
    query = 'query compartment resources where displayName =~ "{}"'.format(escaped_name)
    search_client = oci.resource_search.ResourceSearchClient(config, signer=signer)
    search_details = oci.resource_search.models.StructuredSearchDetails(
        query=query,
        type="Structured",
    )

    retry = True
    matches = []
    while retry:
        retry = False
        try:
            matches = oci.pagination.list_call_get_all_results(
                search_client.search_resources,
                search_details,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                print("API busy.. retry", end="\r")
                retry = True
                time.sleep(WaitRefresh)
            else:
                print("bad error!: " + e.message)
                return 0

    if not matches:
        return 0

    if len(matches) == 1:
        match = matches[0]
        if _confirm_compartment_match(compartment, match.display_name, match.identifier):
            return match.identifier
        return 0

    print("Multiple compartments found:")
    for index, match in enumerate(matches, start=1):
        print("  {}. {} ({})".format(index, match.display_name, match.identifier))

    while True:
        try:
            selection = input("Select compartment number: ").strip()
            choice = int(selection)
            if 1 <= choice <= len(matches):
                return matches[choice - 1].identifier
        except ValueError:
            pass
        print("Invalid selection. Enter a number between 1 and {}.".format(len(matches)))


##########################################################################
# Checking SDK Version
# Minimum version requirements for OCI SDK
##########################################################################
def check_oci_version(min_oci_version_required):
    outdated = False

    for i, rl in zip(oci.__version__.split("."), min_oci_version_required.split(".")):
        if int(i) > int(rl):
            break
        if int(i) < int(rl):
            outdated = True
            break

    if outdated:
        print("Your version of the OCI SDK is out-of-date. Please first upgrade your OCI SDK Library bu running the command:")
        print("OCI SDK Version : {}".format(oci.__version__))
        print("Min SDK required: {}".format(min_oci_version_required))
        print("pip install --upgrade oci")
        quit()


#############################################
# MyWriter to redirect output
#############################################
def CurrentTimeString():
    return time.strftime("%D %H:%M:%S", time.localtime())

class MyWriter:

    #filename = "log.txt"

    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.filename = filename
        self.logfile = open(self.filename, "a", encoding="utf-8")

    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)

    def close(self):
        self.stdout.close()
        self.logfile.close()

    def flush(self):
        self.logfile.close()
        self.logfile = open(self.filename, "a", encoding="utf-8")



