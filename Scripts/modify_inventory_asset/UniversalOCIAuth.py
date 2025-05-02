import oci
import os

##################################################################################################
## Create signer for Authentication
## Input - config_profile and is_instance_principals and is_delegation_token and is_security_token
## Output - config and signer objects
##################################################################################################
def create_signer(config_profile, is_instance_principal, is_delegation_token, is_security_token):

    ## Instance Principal
    if is_instance_principal:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("ERROR: Failed to get Instance Principal settings.")
            raise SystemExit

   
    ## CloudShell - Delegation Token
    elif is_delegation_token:

        try:
            ## check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            ## check if file exist
            if env_config_file is None or env_config_section is None:
                print("*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                raise SystemExit

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("ERROR: Failed to get Delegation Token settings.")
            raise SystemExit

        except Exception:
            raise

    ## Session Authentication - Security Token
    elif is_security_token:

        try:
            config = oci.config.from_file(
                oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            token_file = config['security_token_file']
            token = None
            with open(token_file, 'r') as f:
                    token = f.read()
            private_key = oci.signer.load_private_key_from_file(config['key_file'])
            #tenancy_id = config['tenancy']
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            return config, signer

        except KeyError:
            print("ERROR: Failed to get Security Token settings.")
            raise SystemExit

        except Exception:
            raise

    ## API Key Authentication
    else:
        config = oci.config.from_file(
            oci.config.DEFAULT_LOCATION,
            (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
        )
        try:
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
        except KeyError:
            print("ERROR: Failed to get API Key settings.")
            raise SystemExit

        except Exception:
            raise
        return config, signer