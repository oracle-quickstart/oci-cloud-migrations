# Overview
This repository contains resources related to the [Oracle Cloud Migrations](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/home.htm) service.

# Included Resources

- [Prerequisites](Prerequisites) - A copy of the Terraform that is provided via the [Oracle Cloud Migrations Overview](https://cloud.oracle.com/cloud-migrations) page of the Oracle Cloud Console.
- [Scripts](Scripts) - Example scripts that can be modified and used as part of the migration process.

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security vulnerability disclosure process

## License

Copyright (c) 2018-2020 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.

## OCI Cloud Migrations AI Tools

Oracle Cloud Migrations (OCM) supports discovery, planning, and execution for VMware, AWS EC2, and Oracle Linux Virtualization Manager workloads moving to Oracle Cloud Infrastructure. Prerequisites are step zero: validate the required identity, compartment, authorization, encryption, storage, and end-to-end resources before downstream migration work.

The authored public AI-assistant pack is in [`ocm-ai-tools/`](ocm-ai-tools/). The generated [`.agents/skills/`](.agents/skills/) directory exposes the prerequisite skill plus the read-only validation and mutation-gated onboarding workflows as installable Agent Skills.

Install all three entry points from GitHub:

```bash
npx skills add https://github.com/oracle-quickstart/oci-cloud-migrations/tree/main/.agents/skills \
  --skill '*' --global --agent codex --yes
```

After cloning this repository, use the same project-local surface:

```bash
npx skills add ./.agents/skills --skill '*' --agent codex --yes
```

The current prerequisite contract is v2.4. Update installed Skills CLI content with `npx skills update`. The optional AIPack composition and update route are documented in [`ocm-ai-tools/README.md`](ocm-ai-tools/README.md).
