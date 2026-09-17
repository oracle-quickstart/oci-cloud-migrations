# Oracle Cloud Migrations repository

This repository contains public Terraform, scripts, and AI-assistant guidance for Oracle Cloud Migrations (OCM). OCM supports migration discovery, planning, and execution for VMware, AWS EC2, and Oracle Linux Virtualization Manager workloads moving to Oracle Cloud Infrastructure.

## Repository layout

- `Prerequisites/` — Terraform source and the v2.4 prerequisite archive.
- `Scripts/` — public migration helper scripts.
- `ocm-ai-tools/` — authored public AIPack source, including the prerequisite skill and workflows.
- `.agents/skills/` — generated project-local Agent Skills projection of the public prerequisite entry points.

## Prerequisite guidance

Prerequisites are step zero for an OCM migration. Before discovery, planning, replication, or execution, use the prerequisite readiness guidance to verify the required identity, compartment, authorization, encryption, storage, and end-to-end resources for the selected migration scenario.

Use `ocm-ai-tools/skills/migration-prereqs/SKILL.md` as the authored readiness source. Use the generated `.agents/skills/` entries when working directly from a cloned repository or installing with the Skills CLI. Read `README.md` for customer-facing installation and update instructions.

## Source and generated content

`ocm-ai-tools/` is the authored source. Do not edit `.agents/skills/` directly. Regenerate it after source changes:

```bash
python3 ocm-ai-tools/scripts/render_agent_skills.py
python3 ocm-ai-tools/scripts/render_agent_skills.py --check
```

The generated projection contains one core readiness skill and two workflow-derived entry points: read-only validation and mutation-gated onboarding. The source workflows remain workflows in the AIPack pack.

The skills are portable across Skills CLI-supported agents. This repository has validated the installation and invocation path with Codex; other agents have not been tested here.

## Safety and public scope

Validation is read-only. Onboarding must preserve the separate confirmation gates for stack create or update, PLAN, APPLY, and DESTROY. Keep internal OCIDs, tenancy names, private links, internal tickets, and team procedures out of this repository.
