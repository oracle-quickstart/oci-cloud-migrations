import oci
import time

WaitRefresh = 10
MaxIDeleteTagIteration = 5


class OCICompartments:
    fullpath = ""
    level = 0
    details = oci.identity.models.Compartment()


def GetCompartments(identity, rootID):
    retry = True
    while retry:
        retry = False
        try:
            # print("Getting compartments for {}".format(rootID))
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
#                 Login                 #
#################################################
def Login(config, signer, startcomp, sso_user=False, get_compartments=False):
    identity = oci.identity.IdentityClient(config, signer=signer)
    if "user" in config:
        try:
            user = identity.get_user(config["user"]).data
            print("Logged in as: {} @ {}".format(user.description, config["region"]))
        except oci.exceptions.ServiceError as e:
            if e.status == 404 and sso_user:
                print("Warning: user not found — assuming SSO")
                user = "IP-DT"
            else:
                raise e
    else:
        print("Logged in as: {} @ {}".format("InstancePrinciple/DelegationToken", config["region"]))
        user = "IP-DT"

    c = []
    if get_compartments:
        print ("Getting compartments...")
        # Adding Start compartment
        if "user" in config or ".tenancy." not in startcomp:
            compartment = identity.get_compartment(compartment_id=startcomp, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data
        else:
            # Bug fix - for working on root compartment using instance principle.
            compartment = oci.identity.models.Compartment()
            compartment.id = startcomp
            compartment.name = "root compartment"
            compartment.lifecycle_state = "ACTIVE"

        newcomp = OCICompartments()
        newcomp.details = compartment
        if ".tenancy." in startcomp:
            newcomp.fullpath = "/root"
            newcomp.level = 0
        else:
            newcomp.level = 0
            newcomp.fullpath = compartment.name
        c.append(newcomp)

        # Add first level subcompartments
        compartments = GetCompartments(identity, startcomp)

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

