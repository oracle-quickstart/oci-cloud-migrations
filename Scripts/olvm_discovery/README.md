# olvm_discovery.py

## Overview
Standalone script, which performs discovery of OLVM resources and saves them as OCM inventory assets to enable VMware > OLVM migration using Oracle Cloud Migrations service. It takes OCID of the OLVM asset source and pulls OLVM endpoint URL and credentials from its configuration.

## Supported Auhtentication
- Security token
- API key

## Usage
```
ansokolo$ python3 -m venv new_env
ansokolo$ source ./new_env/bin/activate
(olvm_env) ansokolo$ pip install -r requirements.txt
(olvm_env) ansokolo$ oci session authenticate --region us-phoenix-1 --profile-name=DEFAULT
(olvm_env) ansokolo$ python ./olvm_discovery.py ocid1.ocbassetsource.oc1.iad.amaaaaaag26i5naar3pn2gkajj4hdvalcawgmvncc3fcesvcs5wekgjj6xaa
Got asset source!
Pulling inventory assets ................. Done!
Got OVLM secret!
Pulled 3 storage domains
	OLVM object 1-storage-domain .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naapcvdmoxbjwewf5cfjw2kdvv6b7mbg3g3aizotj5cbchq
	OLVM object data_nfs1 .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naabqch33wnzegrwss3eltt5tzsa3lnhnl6lmrr5jvhn5nq
	OLVM object ovirt-image-repository .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naafzazapl4jsutbhzeygqk5ycnwuk3gt4spu7nb544fqeq
Pulled 1 clusters
	OLVM object Default .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naagkni2k5sxtb7xmx3oek5tyab7jgatno5ctma4oqmiomq
Pulled 2 vNIC profiles
	OLVM object ovirtmgmt .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naao7zf6dfx4vwuw5cwogpuau5v55tyexe46k6gqixbpg6a
	OLVM object L2 VM Network .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naajl6blgymqavbqzbblbohsx5ghp75kcbl4nrdjfwyf43q
Pulled 3 VM templates
	OLVM object Blank .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naa5p3nnhfau57pnpkva6km3emyrphjiuu4gcj6bdsak63q
	OLVM object OL8U10_x86_64-olvm-b258.ova .. New asset ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naaspbrpysiu4jg6bpfkbcvmcv2ymafa4iz3cl2d572mkpq
	OLVM object OL9U5_x86_64-olvm-b259.ova .. Found ocid1.ocbinventoryasset.oc1.iad.amaaaaaag26i5naa5f5atgxfyer47qzhzxpfrycbitcotplyeddbvhidmwkq
(olvm_env) ansokolo$
```
