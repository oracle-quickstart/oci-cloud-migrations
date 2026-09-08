# OCI Cloud Migrations AI Tools

AI-assistant guidance for Oracle Cloud Migrations customer workflows.

The current content focuses on prerequisite readiness: validating the prerequisite stack, explaining non-green readiness bars, and guiding Resource Manager stack setup or remediation.

## Use Directly

No installer is required.

1. Use `workflows/migration-prereqs-validate.md` for read-only readiness checks.
2. Use `workflows/migration-prereqs-onboard.md` when prerequisites need to be created or remediated.
3. Give your assistant the files under `skills/migration-prereqs/` when it needs bar-by-bar validation details.
4. Start from `examples/prereq-readiness-request.md` or `prompts/prereq-readiness-check.md` if you want a copy-ready request.

Live deterministic validation requires OCI CLI tenancy access. The packaged MCP config uses the public OCI MCP server from `oracle/mcp` for optional follow-up diagnostics or corroboration; this pack does not provide an SDK-only verifier.

The generated skills are portable across Skills CLI-supported agents. The commands below target Codex because Codex is the only agent tested for this pack; replace `codex` with another supported agent name only after validating that agent's installation and invocation behavior.

## Skills CLI

If your assistant uses the Skills CLI, install the generated workflow-as-skill surface from the repository root:

```sh
npx skills add https://github.com/oracle-quickstart/oci-cloud-migrations/tree/main/.agents/skills \
  --skill '*' --global --agent codex --yes
```

From a clone of the repository:

```sh
npx skills add ./.agents/skills --skill '*' --agent codex --yes
```

The generated surface contains `migration-prereqs`, `migration-prereqs-validate`, and `migration-prereqs-onboard`. The authored core skill and the source workflows remain in this directory for AIPack and direct GitHub use.

Install all three entry points together. The validation and onboarding workflow skills depend on the core `migration-prereqs` skill; installing either workflow by itself is incomplete.

## Optional aipack

`aipack` is optional. See the [AIPack repository](https://github.com/shrug-labs/aipack) for installation and usage. It installs the same content into supported AI assistant harnesses and can enable the packaged OCI MCP configuration.

```sh
aipack pack install --url https://github.com/oracle-quickstart/oci-cloud-migrations.git --path ocm-ai-tools --ref main --with all
aipack sync --profile ocm-ai-tools --dry-run
aipack sync --profile ocm-ai-tools
```

Set `oci_config_profile` in `profiles/ocm-ai-tools.yaml` if you do not use the `DEFAULT` OCI profile.

To refresh an installed pack, fetch the updated source and then sync it:

```sh
aipack pack update ocm-ai-tools --with all
aipack sync --profile ocm-ai-tools
```

## Contents

- `skills/migration-prereqs/` - prerequisite-stack validation knowledge, references, bar modules, and the deterministic verifier.
- `workflows/` - read-only validation and guided onboarding workflows.
- `rules/` - passive OCM prerequisite routing guidance.
- `mcp/oci-mcp.json` - optional OCI MCP server configuration.
- `prompts/` - copy-ready prompts for assistant sessions.
- `examples/` - sample customer requests and expected response shape.
- `tests/` - offline detector tests for the public verifier.

## Safety

`migration-prereqs-validate` is read-only. `migration-prereqs-onboard` requires a Resource Manager plan review and explicit customer confirmation before any apply operation. The workflows do not create prerequisite resources directly through ad hoc API calls.

## Updates and support

The repository-root `.agents/skills/` directory is generated from this pack by `scripts/render_agent_skills.py`. It is the primary install surface for the Skills CLI because it exposes the core skill and both workflow entry points as installable `SKILL.md` directories. Do not edit the generated files directly.

After a global Skills CLI install, update with `npx skills update --global --yes`. After a clone-local install, update with `npx skills update --project --yes`.

The current prerequisite contract is v2.4. `Prerequisites/` remains the canonical repository Terraform and archive source; the generated skill projection contains only the agent instructions and verifier support needed by the three entry points.

Use [GitHub Issues](https://github.com/oracle-quickstart/oci-cloud-migrations/issues) for support and include the entry point, scenario, and sanitized verifier output. Before sharing verifier output, redact tenancy, compartment, stack, bucket, job, profile, namespace, and credential identifiers. For security vulnerabilities, follow the repository's [security policy](../SECURITY.md) instead of opening an issue.
