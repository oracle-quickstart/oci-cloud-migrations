# terminate_nat_gateway

This Terraform configuration deployes an OCI Function that removes NAT Gateway route rules from a route table and deletes the NAT Gateway that was referenced in the rule.

This function modifies the default Hydration Agent virtual network created by the Oracle Cloud Migrations service.

## Prerequisites

- [OCI Auth Token](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm) - Used for pushing images to an OCI container registry using Terraform.
- Tenancy User - This user needs to have permission to manage identity (dynamic groups and policies) and 

## Deploy Using Oracle Resource Manager

1. Download this repository.

2. Create an OCI Resource Manger stack in the 'Migrations' compartment.

3. During creation, for the 'Stack configuration' section, choose the 'Folder' and select the 'termiante_nat_gateway' folder 

4. Click 'Next' to configure variables.

5. The following variables are required:
   1. ocir_password - The OCI Auth Token generated for the OCIR user below. This token can be deleted after the stack is applied sucessfully.
   2. ocir_user_name - The tenancy user who has permission to create the function in the OCI Container Registry.
   3. subnet_ocid - Any subnet where the function can run. This subnet requires at least a Service Gateway.