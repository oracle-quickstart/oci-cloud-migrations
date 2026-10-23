# Prerequisite Readiness Check

Use this prompt with an AI assistant that can read repository files and access OCI through an approved method.

```text
You are helping validate Oracle Cloud Migrations prerequisite readiness.

Load these files:
- ocm-ai-tools/README.md
- ocm-ai-tools/workflows/migration-prereqs-validate.md
- ocm-ai-tools/skills/migration-prereqs/SKILL.md
- ocm-ai-tools/skills/migration-prereqs/INDEX.md

Customer inputs:
- Migration scenario: <VMware to OCI | AWS to OCI | VMware to OLVM>
- Migration root compartment: <compartment name or OCID>
- OCI access method: <OCI MCP | OCI CLI | OCI SDK>

Start with read-only validation. Do not create, update, or delete OCI resources. For each prerequisite bar, provide status, evidence, and next step. If setup or remediation is needed, ask before switching to the onboarding workflow.
```
