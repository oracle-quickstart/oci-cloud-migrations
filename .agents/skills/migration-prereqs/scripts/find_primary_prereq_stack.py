#!/usr/bin/env python3
"""Discover the primary OCM prerequisite RMS stack and verify live readiness.

Heuristic:
- Inspect the customer-selected root, or infer roots from surviving artifacts when no
  root is selected.
- Inspect separately stored RMS stacks only when their compartments are supplied.
- Optionally inspect every accessible compartment.
- Find prereq-like stacks from full stack details.
- Score stacks by latest job state, APPLY success, surviving artifacts, and destroy state.

With --verify, the same read-only evidence path also evaluates the six published
prerequisite bars. A proven required failure is authoritative not-ready even
when another check is unavailable; incomplete evidence is never inferred ready.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PREREQ_DESC_SNIPPET = "deploy the resources required for the oracle cloud migration service"
PREREQ_NAME_RE = re.compile(r"(prereq|prerequisite|ocm)", re.IGNORECASE)
TIME_MIN = datetime.min.replace(tzinfo=timezone.utc)
DEFAULT_OCI_CMD_TIMEOUT_SECONDS = 120
VERIFIER_SCHEMA_VERSION = "1.0"
CONTRACT_VERSION = "2.4"
CONTRACT_SOURCE = (
    "https://github.com/oracle-quickstart/oci-cloud-migrations/tree/v2.4/Prerequisites/src"
)
SUPPORTED_SCENARIOS = ("VMware to OCI", "AWS to OCI", "VMware to OLVM")
CONFIGLESS_AUTH_MODES = frozenset(
    {"instance_principal", "resource_principal", "oke_workload_identity"}
)
REQUIRED_TAGS = {
    "PrerequisiteVersion",
    "PrerequisiteResourceLevel",
    "PrerequisiteForVMware",
    "PrerequisiteForAWS",
    "PrerequisiteForOLVM",
    "SourceEnvironmentType",
    "SourceEnvironmentId",
    "SourceAssetId",
    "MigrationProject",
    "ServiceUse",
}


@dataclass(frozen=True)
class OciCliContext:
    profile: str
    config_file: str
    auth: str | None = None
    region: str | None = None
    cert_bundle: str | None = None
    timeout_seconds: int = DEFAULT_OCI_CMD_TIMEOUT_SECONDS


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect primary OCM prerequisite RMS stack")
    parser.add_argument("--profile", default="DEFAULT", help="OCI CLI profile (default: DEFAULT)")
    parser.add_argument(
        "--config-file",
        default=os.environ.get("OCI_CLI_CONFIG_FILE", str(Path.home() / ".oci" / "config")),
        help="OCI CLI config file path",
    )
    parser.add_argument(
        "--auth",
        choices=(
            "api_key",
            "instance_principal",
            "security_token",
            "instance_obo_user",
            "resource_principal",
            "oke_workload_identity",
        ),
        help="OCI CLI authentication type (default: OCI CLI configuration)",
    )
    parser.add_argument("--region", help="OCI region override")
    parser.add_argument("--cert-bundle", help="CA certificate bundle for SSL verification")
    parser.add_argument(
        "--oci-timeout-seconds",
        type=int,
        default=DEFAULT_OCI_CMD_TIMEOUT_SECONDS,
        help=(
            "Timeout for each OCI CLI read "
            f"(default: {DEFAULT_OCI_CMD_TIMEOUT_SECONDS} seconds)"
        ),
    )
    parser.add_argument("--tenancy-ocid", help="Tenancy OCID (optional; falls back to profile config)")
    parser.add_argument(
        "--root-compartment-ocid",
        help="Customer-selected migration root; always inspect this compartment",
    )
    parser.add_argument(
        "--stack-compartment-ocid",
        action="append",
        default=[],
        help=(
            "Compartment containing an RMS prerequisite stack; repeat for multiple "
            "known stack locations"
        ),
    )
    parser.add_argument(
        "--scan-all-compartments",
        action="store_true",
        help="Also inspect every accessible compartment for prereq-like stacks",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Evaluate all scenario-required prerequisite bars from live read-only evidence",
    )
    parser.add_argument(
        "--scenario",
        choices=SUPPORTED_SCENARIOS,
        help="Migration scenario to evaluate; required with --verify",
    )
    parser.add_argument(
        "--replication-bucket-name",
        help="Explicit configured replication bucket name when stack evidence is unavailable",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser.parse_args()


def _load_tenancy_from_config(config_file: str, profile: str) -> str:
    current = None
    tenancy = None
    with open(config_file, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1].strip()
                continue
            if current == profile and "=" in line:
                k, v = [s.strip() for s in line.split("=", 1)]
                if k == "tenancy":
                    tenancy = v
                    break
    if not tenancy:
        raise RuntimeError(
            f"Could not find tenancy for profile '{profile}' in config '{config_file}'"
        )
    return tenancy


def _oci(context: OciCliContext, args: list[str], *, allow_empty: bool = False) -> Any:
    cmd = [
        "oci",
        "--profile",
        context.profile,
        "--config-file",
        context.config_file,
        "--output",
        "json",
    ]
    if context.auth:
        cmd.extend(["--auth", context.auth])
    if context.region:
        cmd.extend(["--region", context.region])
    if context.cert_bundle:
        cmd.extend(["--cert-bundle", context.cert_bundle])
    cmd.extend(args)
    try:
        out = subprocess.run(
            cmd, check=True, capture_output=True, text=True,
            timeout=context.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"OCI command timed out after {context.timeout_seconds}s. Validate the "
            "security-token session, network reachability, and endpoint latency before "
            "retrying; increase --oci-timeout-seconds when the endpoint is healthy but slow."
        )
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or e.stdout.strip() or str(e)
        raise RuntimeError(f"OCI command failed: {' '.join(cmd)}\n{msg}") from e

    stdout = out.stdout.strip()
    if not stdout:
        if allow_empty:
            return []
        raise RuntimeError(f"OCI command produced no JSON output: {' '.join(cmd)}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"OCI command produced invalid JSON: {' '.join(cmd)}\n{stdout[:500]}"
        ) from e
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _parse_time(val: str | None) -> datetime:
    if not val:
        return TIME_MIN
    # OCI timestamps are RFC3339 with timezone, often +00:00.
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except ValueError:
        return TIME_MIN


def _discover_compartments(context: OciCliContext, tenancy_ocid: str) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "iam",
            "compartment",
            "list",
            "--compartment-id",
            tenancy_ocid,
            "--compartment-id-in-subtree",
            "true",
            "--access-level",
            "ACCESSIBLE",
            "--lifecycle-state",
            "ACTIVE",
            "--all",
        ],
        allow_empty=True,
    )


def _prereq_version_from_tags(compartment: dict[str, Any]) -> str | None:
    defined_tags = compartment.get("defined-tags") or compartment.get("defined_tags") or {}
    namespace = defined_tags.get("CloudMigrations") or {}
    value = namespace.get("PrerequisiteVersion")
    if value is None:
        return None
    version = str(value).strip()
    return version or None


def _artifact_roots(compartments: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id = {c.get("id"): c for c in compartments}
    roots: dict[str, dict[str, Any]] = {}
    for c in compartments:
        name = c.get("name")
        if name not in {"Migration", "MigrationSecrets"}:
            continue
        parent = c.get("compartment-id")
        if not parent:
            continue
        if parent not in roots:
            roots[parent] = {
                "root_compartment_id": parent,
                "root_compartment_name": by_id.get(parent, {}).get("name", "<unknown>"),
                "has_migration": False,
                "has_migration_secrets": False,
                "migration_compartment_id": None,
                "migration_secrets_compartment_id": None,
                "observed_prereq_versions": [],
            }
        if name == "Migration":
            roots[parent]["has_migration"] = True
            roots[parent]["migration_compartment_id"] = c.get("id")
        elif name == "MigrationSecrets":
            roots[parent]["has_migration_secrets"] = True
            roots[parent]["migration_secrets_compartment_id"] = c.get("id")
        version = _prereq_version_from_tags(c)
        if version and version not in roots[parent]["observed_prereq_versions"]:
            roots[parent]["observed_prereq_versions"].append(version)
    return roots


def _list_stacks(context: OciCliContext, compartment_id: str) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "resource-manager",
            "stack",
            "list",
            "--compartment-id",
            compartment_id,
            "--all",
        ],
        allow_empty=True,
    )


def _list_jobs(context: OciCliContext, stack_id: str) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "resource-manager",
            "job",
            "list",
            "--stack-id",
            stack_id,
            "--all",
        ],
        allow_empty=True,
    )


def _get_stack(context: OciCliContext, stack_id: str) -> dict[str, Any]:
    return _oci(
        context,
        [
            "resource-manager",
            "stack",
            "get",
            "--stack-id",
            stack_id,
        ],
    )


def _preflight_root(
    context: OciCliContext, tenancy_ocid: str, root_compartment_ocid: str
) -> dict[str, Any]:
    if root_compartment_ocid == tenancy_ocid:
        return _oci(
            context,
            ["iam", "tenancy", "get", "--tenancy-id", tenancy_ocid],
        )
    return _oci(
        context,
        ["iam", "compartment", "get", "--compartment-id", root_compartment_ocid],
    )


def _list_tag_namespaces(
    context: OciCliContext, tenancy_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "iam",
            "tag-namespace",
            "list",
            "--compartment-id",
            tenancy_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _list_tags(context: OciCliContext, namespace_id: str) -> list[dict[str, Any]]:
    return _oci(
        context,
        ["iam", "tag", "list", "--tag-namespace-id", namespace_id, "--all"],
        allow_empty=True,
    )


def _list_child_compartments(
    context: OciCliContext, root_compartment_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "iam",
            "compartment",
            "list",
            "--compartment-id",
            root_compartment_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _list_dynamic_groups(
    context: OciCliContext, tenancy_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "iam",
            "dynamic-group",
            "list",
            "--compartment-id",
            tenancy_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _list_policies(
    context: OciCliContext, compartment_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "iam",
            "policy",
            "list",
            "--compartment-id",
            compartment_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _list_vaults(
    context: OciCliContext, compartment_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "kms",
            "management",
            "vault",
            "list",
            "--compartment-id",
            compartment_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _list_keys(
    context: OciCliContext, compartment_ocid: str, management_endpoint: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "kms",
            "management",
            "key",
            "list",
            "--endpoint",
            management_endpoint,
            "--compartment-id",
            compartment_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _get_object_storage_namespace(context: OciCliContext) -> str:
    value = _oci(context, ["os", "ns", "get"])
    if not isinstance(value, str) or not value:
        raise RuntimeError("Object Storage namespace response did not contain a namespace")
    return value


def _get_bucket(
    context: OciCliContext, namespace: str, bucket_name: str
) -> dict[str, Any]:
    return _oci(
        context,
        [
            "os",
            "bucket",
            "get",
            "--namespace-name",
            namespace,
            "--bucket-name",
            bucket_name,
        ],
    )


def _list_buckets(
    context: OciCliContext, namespace: str, compartment_ocid: str
) -> list[dict[str, Any]]:
    return _oci(
        context,
        [
            "os",
            "bucket",
            "list",
            "--namespace-name",
            namespace,
            "--compartment-id",
            compartment_ocid,
            "--all",
        ],
        allow_empty=True,
    )


def _is_prereq_stack(stack: dict[str, Any], root_compartment_id: str) -> bool:
    name = (stack.get("display-name") or "").lower()
    desc = (stack.get("description") or "").lower()
    variables = stack.get("variables") or {}

    if PREREQ_NAME_RE.search(name):
        return True
    if PREREQ_DESC_SNIPPET in desc:
        return True

    comp_var = variables.get("compartment_ocid")
    if comp_var and "tenancy_ocid" in variables:
        # v2.3+ variable family
        current_model_keys = {
            "enabled_migration_scenario", "primary_prerequisite_stack",
            "add_vmware_to_oci", "add_vmware_to_olvm", "add_aws_to_oci",
        }
        # v2.1 variables
        v21_keys = {"migration_from_vmware", "migration_from_aws"}
        if current_model_keys.intersection(variables.keys()) or v21_keys.intersection(variables.keys()):
            return True

    return False


def _stack_score(
    stack: dict[str, Any],
    jobs: list[dict[str, Any]],
    root_artifact: dict[str, Any] | None,
) -> dict[str, Any]:
    latest_job = max(
        jobs,
        key=lambda j: _parse_time(j.get("time-finished") or j.get("time-created")),
        default=None,
    )
    apply_succeeded = [
        j
        for j in jobs
        if (j.get("operation") == "APPLY" and j.get("lifecycle-state") == "SUCCEEDED")
    ]
    destroy_succeeded = [
        j
        for j in jobs
        if (j.get("operation") == "DESTROY" and j.get("lifecycle-state") == "SUCCEEDED")
    ]

    latest_apply = max(
        (_parse_time(j.get("time-finished") or j.get("time-created")) for j in apply_succeeded),
        default=TIME_MIN,
    )
    latest_destroy = max(
        (_parse_time(j.get("time-finished") or j.get("time-created")) for j in destroy_succeeded),
        default=TIME_MIN,
    )

    score = 0
    reasons: list[str] = []

    if latest_job:
        latest_operation = latest_job.get("operation")
        latest_state = latest_job.get("lifecycle-state")
        latest_job_id = latest_job.get("id")
        latest_at = _parse_time(latest_job.get("time-finished") or latest_job.get("time-created"))
        reasons.append(f"latest job is {latest_operation} {latest_state}")
        if latest_state == "FAILED":
            score -= 2
    else:
        latest_operation = None
        latest_state = None
        latest_job_id = None
        latest_at = TIME_MIN
        reasons.append("job history unavailable")

    if latest_apply > TIME_MIN:
        score += 3
        reasons.append("has APPLY SUCCEEDED")
    else:
        reasons.append("no APPLY SUCCEEDED")

    if root_artifact:
        has_m = bool(root_artifact.get("has_migration"))
        has_s = bool(root_artifact.get("has_migration_secrets"))
        if has_m and has_s:
            score += 2
            reasons.append("Migration + MigrationSecrets exist under stack root")
        elif has_m or has_s:
            score += 1
            reasons.append("one prerequisite compartment exists under stack root")

    if latest_destroy > latest_apply and latest_destroy > TIME_MIN:
        score -= 3
        reasons.append("latest successful mutation is DESTROY")

    return {
        "score": score,
        "latest_apply_succeeded_at": latest_apply.isoformat() if latest_apply != TIME_MIN else None,
        "latest_destroy_succeeded_at": latest_destroy.isoformat() if latest_destroy != TIME_MIN else None,
        "latest_job_operation": latest_operation,
        "latest_job_state": latest_state,
        "latest_job_id": latest_job_id,
        "latest_job_at": latest_at.isoformat() if latest_at != TIME_MIN else None,
        "reasons": reasons,
    }

# TODO: drift detection between stack variables and last applied state

def _detect_variable_model(variables: dict[str, Any]) -> str | None:
    """Identify the variable-model family without claiming an exact release."""
    if ("enabled_migration_scenario" in variables
            or "primary_prerequisite_stack" in variables
            or any(k.startswith("add_") for k in variables)):
        return "v2.3+"
    if "primary_migration_scenario" in variables:
        return "pre-v2.3-rename"
    if "migration_from_vmware" in variables or "migration_from_aws" in variables:
        return "v2.1"
    return None


def _is_true(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def _extract_scenario(variables: dict[str, Any], variable_model: str | None) -> str | None:
    """Extract the configured scenario from stack variables."""
    if variable_model == "v2.3+":
        primary = variables.get("enabled_migration_scenario")
        labels = {
            "add_vmware_to_oci": "VMware to OCI",
            "add_vmware_to_olvm": "VMware to OLVM",
            "add_aws_to_oci": "AWS to OCI",
        }
        additive = [labels[k] for k in labels if _is_true(variables.get(k))]
        parts = ([primary] if primary else []) + additive
        return ", ".join(parts) if parts else None
    if variable_model == "pre-v2.3-rename":
        primary = variables.get("primary_migration_scenario")
        labels = {
            "vmware_to_oci": "VMware to OCI",
            "aws_to_oci": "AWS to OCI",
            "vmware_to_olvm": "VMware to OLVM",
        }
        return labels.get(primary, primary)
    if variable_model == "v2.1":
        scenarios = []
        if _is_true(variables.get("migration_from_vmware")):
            scenarios.append("VMware")
        if _is_true(variables.get("migration_from_aws")):
            scenarios.append("AWS")
        return ", ".join(scenarios) if scenarios else None
    return None


def _to_row(
    stack: dict[str, Any],
    root: dict[str, Any] | None,
    scoring: dict[str, Any],
    selected_root_compartment_ocid: str | None = None,
) -> dict[str, Any]:
    vars_ = stack.get("variables") or {}
    variable_model = _detect_variable_model(vars_)
    observed_versions = sorted(set((root or {}).get("observed_prereq_versions", [])))
    row = {
        "stack_id": stack.get("id"),
        "display_name": stack.get("display-name"),
        "stack_compartment_id": stack.get("compartment-id"),
        "stack_compartment_name": (root or {}).get("root_compartment_name"),
        "configured_root_compartment_ocid": vars_.get("compartment_ocid"),
        "replication_bucket_name": vars_.get("replication_bucket"),
        "prereq_version": observed_versions[0] if len(observed_versions) == 1 else None,
        "observed_prereq_versions": observed_versions,
        "prereq_version_conflict": len(observed_versions) > 1,
        "variable_model": variable_model,
        "scenario": _extract_scenario(vars_, variable_model),
        "score": scoring["score"],
        "latest_apply_succeeded_at": scoring["latest_apply_succeeded_at"],
        "latest_destroy_succeeded_at": scoring["latest_destroy_succeeded_at"],
        "latest_job_operation": scoring["latest_job_operation"],
        "latest_job_state": scoring["latest_job_state"],
        "latest_job_id": scoring["latest_job_id"],
        "latest_job_at": scoring["latest_job_at"],
        "reasons": scoring["reasons"],
    }
    configured_root = row["configured_root_compartment_ocid"]
    if not selected_root_compartment_ocid:
        row["selected_root_match"] = False
        row["selected_root_match_source"] = None
    elif configured_root:
        row["selected_root_match"] = configured_root == selected_root_compartment_ocid
        row["selected_root_match_source"] = "configured_root_compartment_ocid"
    else:
        row["selected_root_match"] = row["stack_compartment_id"] == selected_root_compartment_ocid
        row["selected_root_match_source"] = "stack_compartment_id_fallback"
    return row


def _select_primary(
    candidates: list[dict[str, Any]],
    selected_root_compartment_ocid: str | None,
) -> dict[str, Any] | None:
    if selected_root_compartment_ocid:
        selected_root_candidates = [
            candidate for candidate in candidates if candidate["selected_root_match"]
        ]
        return selected_root_candidates[0] if selected_root_candidates else None
    return candidates[0] if candidates else None


def _field(resource: dict[str, Any], name: str, default: Any = None) -> Any:
    return resource.get(name, resource.get(name.replace("-", "_"), default))


def _defined_tag_value(resource: dict[str, Any], tag_name: str) -> Any:
    defined_tags = _field(resource, "defined-tags", {}) or {}
    return (defined_tags.get("CloudMigrations") or {}).get(tag_name)


def _bar(
    number: int,
    name: str,
    status: str,
    reason_codes: list[str],
    evidence: dict[str, Any],
    next_action: str,
) -> dict[str, Any]:
    return {
        "bar": number,
        "name": name,
        "status": status,
        "reason_codes": reason_codes,
        "evidence": evidence,
        "next_action": next_action,
    }


def _unavailable_bar(number: int, name: str, operation: str, error: Exception) -> dict[str, Any]:
    return _bar(
        number,
        name,
        "unavailable",
        ["evidence_read_failed"],
        {"failed_operation": operation, "error": str(error)},
        f"Restore access for {operation}, then rerun verification.",
    )


def _evaluate_identity(
    namespaces: list[dict[str, Any]],
    tags: list[dict[str, Any]] | None,
    observed_versions: list[str],
) -> dict[str, Any]:
    namespace = next(
        (item for item in namespaces if _field(item, "name") == "CloudMigrations"),
        None,
    )
    if not namespace or _field(namespace, "lifecycle-state") != "ACTIVE":
        return _bar(
            1,
            "Identity Foundation",
            "red",
            ["tag_namespace_missing_or_inactive"],
            {
                "namespace_found": bool(namespace),
                "namespace_state": _field(namespace or {}, "lifecycle-state"),
            },
            "Create or restore the CloudMigrations tag namespace through the prerequisite stack.",
        )
    if tags is None:
        return _unavailable_bar(
            1,
            "Identity Foundation",
            "iam tag list",
            RuntimeError("CloudMigrations tag definitions were not read"),
        )

    active_names = {
        _field(item, "name")
        for item in tags
        if _field(item, "lifecycle-state") == "ACTIVE"
    }
    missing = sorted(REQUIRED_TAGS - active_names)
    versions = sorted(set(v for v in observed_versions if v))
    compatible = len(versions) == 1 and versions[0] in {"2.3", CONTRACT_VERSION}
    evidence = {
        "namespace_id": _field(namespace, "id"),
        "namespace_state": _field(namespace, "lifecycle-state"),
        "active_tag_names": sorted(active_names),
        "missing_tag_names": missing,
        "observed_prereq_versions": versions,
    }
    if not missing and compatible:
        return _bar(
            1,
            "Identity Foundation",
            "green",
            ["identity_contract_satisfied"],
            evidence,
            "None.",
        )
    return _bar(
        1,
        "Identity Foundation",
        "yellow",
        ["partial_tag_contract" if missing else "version_not_proven_compatible"],
        evidence,
        "Update and re-apply the prerequisite stack, then re-read the live tags.",
    )


def _evaluate_compartments(
    children: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, str | None]]:
    found: dict[str, dict[str, Any] | None] = {
        name: next((item for item in children if _field(item, "name") == name), None)
        for name in ("Migration", "MigrationSecrets")
    }
    details = {
        name: {
            "id": _field(item or {}, "id"),
            "state": _field(item or {}, "lifecycle-state"),
            "resource_level": _defined_tag_value(item or {}, "PrerequisiteResourceLevel"),
        }
        for name, item in found.items()
    }
    ids = {name: detail["id"] for name, detail in details.items()}
    good = {
        name
        for name, detail in details.items()
        if detail["id"]
        and detail["state"] == "ACTIVE"
        and detail["resource_level"] == "compartment"
    }
    if len(good) == 2:
        result = _bar(
            2,
            "Compartment Structure",
            "green",
            ["compartment_contract_satisfied"],
            details,
            "None.",
        )
    elif not any(detail["id"] for detail in details.values()):
        result = _bar(
            2,
            "Compartment Structure",
            "red",
            ["required_compartments_missing"],
            details,
            "Apply the prerequisite stack to the selected migration root.",
        )
    else:
        result = _bar(
            2,
            "Compartment Structure",
            "yellow",
            ["compartment_contract_partial_or_stale"],
            details,
            "Correct the missing, inactive, or untagged compartment through the prerequisite stack.",
        )
    return result, ids


def _normal(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


_MATCHING_RULE_RE = re.compile(
    r"^\s*(ALL|ANY)\s*\{\s*(.*?)\s*\}\s*$",
    flags=re.IGNORECASE | re.DOTALL,
)
_MATCHING_RULE_EQUALITY_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9_.]*)\s*=\s*(['\"])(.*?)\2",
    flags=re.IGNORECASE | re.DOTALL,
)


def _matching_rule_matches(
    rule: Any,
    operator: str,
    expected_equalities: tuple[tuple[str, str], ...],
) -> bool:
    match = _MATCHING_RULE_RE.fullmatch(str(rule or ""))
    if not match or match.group(1).upper() != operator:
        return False

    clauses = [clause.strip() for clause in match.group(2).split(",")]
    parsed: list[tuple[str, str]] = []
    for clause in clauses:
        equality = _MATCHING_RULE_EQUALITY_RE.fullmatch(clause)
        if not equality:
            return False
        parsed.append((equality.group(1).lower(), equality.group(3)))

    normalized_expected = [
        (field.lower(), expected_value)
        for field, expected_value in expected_equalities
    ]
    return sorted(parsed) == sorted(normalized_expected)


def _find_dynamic_group_roles(
    dynamic_groups: list[dict[str, Any]], migration_compartment_id: str
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    roles: dict[str, dict[str, Any]] = {}
    invalid: dict[str, str] = {}
    expected: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
        "migration": (
            "ALL",
            (
                ("resource.type", "ocmmigration"),
                ("resource.compartment.id", migration_compartment_id),
            ),
        ),
        "discovery": (
            "ANY",
            (("resource.type", "ocbassetsource"),),
        ),
        "remote_agent": (
            "ANY",
            (("resource.type", "ocbagent"),),
        ),
        "hydration_agent": (
            "ALL",
            (("instance.compartment.id", migration_compartment_id),),
        ),
    }
    for role, (operator, equalities) in expected.items():
        candidates = [
            item
            for item in dynamic_groups
            if _matching_rule_matches(
                _field(item, "matching-rule"),
                operator,
                equalities,
            )
        ]
        active = next(
            (item for item in candidates if _field(item, "lifecycle-state") == "ACTIVE"),
            None,
        )
        if active:
            roles[role] = active
        elif candidates:
            invalid[role] = "inactive"
        else:
            invalid[role] = "missing_or_wrong_matching_rule"
    return roles, invalid


def _policy_missing_requirements(
    policies: list[dict[str, Any]],
    group_name: str,
    requirements: dict[str, tuple[str, ...]],
) -> list[str]:
    statements = [
        _normal(statement)
        for policy in policies
        for statement in (_field(policy, "statements", []) or [])
        if f"dynamic-group {group_name.lower()} to" in _normal(statement)
    ]
    return [
        label
        for label, fragments in requirements.items()
        if not any(
            all(_normal(fragment) in statement for fragment in fragments)
            for statement in statements
        )
    ]


def _authorization_policy_requirements(
    scenario: str,
    migration_compartment_id: str,
    migration_secrets_compartment_id: str,
) -> tuple[
    dict[str, dict[str, tuple[str, ...]]],
    dict[str, dict[str, tuple[str, ...]]],
]:
    migration_id = migration_compartment_id.lower()
    secrets_id = migration_secrets_compartment_id.lower()
    tenancy: dict[str, dict[str, tuple[str, ...]]] = {
        "migration": {
            "read_ocb_inventory": ("read ocb-inventory", "in tenancy"),
            "list_shapes": ("instance_inspect", "request.operation='listshapes'"),
            "read_dedicated_vm_host": (
                "dedicated_vm_host_read",
                "request.operation='getdedicatedvmhost'",
            ),
            "read_capacity_reservation": (
                "capacity_reservation_read",
                "request.operation='getcomputecapacityreservation'",
            ),
            "list_subscriptions": (
                "organizations_subscription_inspect",
                "request.operation='listsubscriptions'",
            ),
            "read_rate_cards": ("read rate-cards", "in tenancy"),
            "read_ocb_asset_metrics": (
                "read metrics",
                "target.metrics.namespace='ocb_asset'",
            ),
            "read_tag_namespaces": ("read tag-namespaces", "in tenancy"),
            "use_cloud_migrations_tags": (
                "use tag-namespaces",
                "target.tag-namespace.name='cloudmigrations'",
            ),
        },
        "discovery": {
            "read_ocb_inventory": ("read ocb-inventory", "in tenancy"),
            "inspect_tenancy": ("tenancy_inspect", "in tenancy"),
        },
        "remote_agent": {},
        "hydration_agent": {},
    }
    root: dict[str, dict[str, tuple[str, ...]]] = {
        "migration": {
            "manage_instances": ("manage instance-family", migration_id),
            "manage_compute_image_capability_schema": (
                "manage compute-image-capability-schema",
                migration_id,
            ),
            "manage_networks": ("manage virtual-network-family", migration_id),
            "manage_volumes": ("manage volume-family", migration_id),
            "manage_objects": ("manage object-family", migration_id),
            "read_inventory_assets": ("read ocb-inventory-asset", migration_id),
            "manage_connectors": (
                "ocb_connector_read",
                "ocb_connector_data_read",
                "ocb_asset_source_read",
                "ocb_asset_source_connector_data_update",
                migration_id,
            ),
            "read_instance_images": (
                "instance_image_inspect",
                "instance_image_read",
                migration_id,
            ),
        },
        "discovery": {
            "read_environments": ("read ocb-environment", migration_id),
            "manage_inventory_assets": ("manage ocb-inventory-asset", migration_id),
            "inspect_compartments": ("inspect compartments", migration_id),
        },
        "remote_agent": {},
        "hydration_agent": {},
    }

    if scenario.startswith("VMware"):
        tenancy["remote_agent"] = {
            "manage_ocb_inventory": ("manage ocb-inventory", "in tenancy"),
            "manage_ocb_agent": (
                "ocb_agent_inspect",
                "ocb_agent_sync",
                "ocb_agent_read",
                "ocb_agent_dependency_inspect",
                "ocb_agent_dependency_read",
                "ocb_agent_key_update",
                "ocb_agent_task_read",
                "ocb_agent_asset_sources_inspect",
                "ocb_agent_task_update",
                "in tenancy",
            ),
        }
        root["remote_agent"] = {
            "manage_buckets": ("manage buckets", migration_id),
            "manage_objects": ("manage object-family", migration_id),
            "manage_replication_tasks": (
                "ocm_replication_task_inspect",
                "ocm_replication_task_read",
                "ocm_replication_task_update",
                migration_id,
            ),
            "use_asset_source_connectors": (
                "use ocb-asset-source-connectors",
                migration_id,
            ),
            "use_connectors": ("use ocb-connectors", migration_id),
            "manage_inventory_assets": ("manage ocb-inventory-asset", migration_id),
            "read_migration_secrets": ("read secret-family", secrets_id),
            "emit_ocb_asset_metrics": (
                "use metrics",
                "target.metrics.namespace='ocb_asset'",
                migration_id,
            ),
            "manage_ocm_connectors": (
                "ocm_connector_inspect",
                "ocm_asset_source_read",
                "ocm_asset_source_connection_push",
                migration_id,
            ),
            "manage_ocb_agents": (
                "ocb_agent_inspect",
                "ocb_agent_sync",
                "ocb_agent_read",
                "ocb_agent_dependency_inspect",
                "ocb_agent_dependency_read",
                "ocb_agent_key_update",
                "ocb_agent_task_read",
                "ocb_agent_asset_sources_inspect",
                "ocb_agent_task_update",
                "ocb_agent_update_command_create",
                migration_id,
            ),
            "manage_asset_sources": (
                "ocb_asset_source_inspect",
                "ocb_asset_source_read",
                "ocb_asset_source_asset_handles_push",
                "ocb_asset_source_connection_push",
                migration_id,
            ),
            "manage_replication_objects": (
                "bucket_inspect",
                "bucket_read",
                "objectstorage_namespace_read",
                "object_create",
                "object_delete",
                "object_inspect",
                "object_overwrite",
                "object_read",
                migration_id,
            ),
        }
        root["discovery"]["read_agents"] = ("read ocb-agents", migration_id)

    if scenario in {"AWS to OCI", "VMware to OLVM"}:
        root["discovery"].update(
            {
                "emit_ocb_asset_metrics": (
                    "use metrics",
                    "target.metrics.namespace='ocb_asset'",
                    migration_id,
                ),
                "read_migration_secrets": ("read secret-family", secrets_id),
            }
        )

    if scenario.endswith("to OCI"):
        root["hydration_agent"] = {
            "manage_hydration_tasks": (
                "ocm_hydration_agent_task_inspect",
                "ocm_hydration_agent_task_update",
                "ocm_hydration_agent_report_status",
                migration_id,
            )
        }
        if scenario == "VMware to OCI":
            root["hydration_agent"]["read_replication_objects"] = (
                "read objects",
                migration_id,
            )
        else:
            root["hydration_agent"].update(
                {
                    "manage_replication_objects": ("manage objects", migration_id),
                    "read_migration_secrets": ("read secret-family", secrets_id),
                }
            )

    return tenancy, root


def _evaluate_authorization(
    scenario: str,
    dynamic_groups: list[dict[str, Any]],
    tenancy_policies: list[dict[str, Any]],
    root_policies: list[dict[str, Any]],
    migration_compartment_id: str,
    migration_secrets_compartment_id: str,
) -> dict[str, Any]:
    tenancy_policies = [
        item
        for item in tenancy_policies
        if _field(item, "lifecycle-state") == "ACTIVE"
    ]
    root_policies = [
        item
        for item in root_policies
        if _field(item, "lifecycle-state") == "ACTIVE"
    ]
    roles, invalid = _find_dynamic_group_roles(dynamic_groups, migration_compartment_id)
    required_roles = {"migration", "discovery"}
    if scenario.startswith("VMware"):
        required_roles.add("remote_agent")
    if scenario.endswith("to OCI"):
        required_roles.add("hydration_agent")

    invalid_required = {
        role: invalid[role] for role in sorted(required_roles) if role not in roles
    }
    if invalid_required:
        return _bar(
            3,
            "Service Authorization",
            "red",
            ["required_dynamic_groups_missing_or_invalid"],
            {"dynamic_group_failures": invalid_required},
            "Update the prerequisite stack or correct the dynamic-group matching rules.",
        )

    tenancy_requirements, compartment_requirements = (
        _authorization_policy_requirements(
            scenario,
            migration_compartment_id,
            migration_secrets_compartment_id,
        )
    )
    missing: dict[str, dict[str, list[str]]] = {}
    group_evidence: dict[str, dict[str, Any]] = {}
    for role in sorted(required_roles):
        group = roles[role]
        group_name = _field(group, "name")
        tenancy_missing = _policy_missing_requirements(
            tenancy_policies, group_name, tenancy_requirements[role]
        )
        compartment_missing = _policy_missing_requirements(
            root_policies, group_name, compartment_requirements[role]
        )
        if tenancy_missing or compartment_missing:
            missing[role] = {
                "tenancy": tenancy_missing,
                "migration_root": compartment_missing,
            }
        group_evidence[role] = {
            "name": group_name,
            "id": _field(group, "id"),
            "matching_rule": _field(group, "matching-rule"),
        }

    evidence = {
        "dynamic_groups": group_evidence,
        "policy_names": sorted(
            {
                _field(item, "name")
                for item in tenancy_policies + root_policies
                if _field(item, "name")
            }
        ),
        "missing_policy_fragments": missing,
        "contract_version": CONTRACT_VERSION,
    }
    if missing:
        return _bar(
            3,
            "Service Authorization",
            "yellow",
            ["policy_contract_partial_or_stale"],
            evidence,
            "Review the missing policy fragments and update the stack or equivalent custom IAM.",
        )
    return _bar(
        3,
        "Service Authorization",
        "green",
        ["authorization_contract_satisfied"],
        evidence,
        "None.",
    )


def _evaluate_encryption(
    vaults: list[dict[str, Any]], keys: list[dict[str, Any]] | None
) -> dict[str, Any]:
    vault = next(
        (item for item in vaults if _field(item, "display-name") == "ocm-secrets"),
        None,
    )
    if not vault or _field(vault, "lifecycle-state") != "ACTIVE":
        return _bar(
            4,
            "Encryption",
            "red",
            ["vault_missing_or_inactive"],
            {
                "vault_found": bool(vault),
                "vault_state": _field(vault or {}, "lifecycle-state"),
            },
            "Create or restore the ocm-secrets vault through the prerequisite stack.",
        )
    if keys is None:
        return _unavailable_bar(
            4,
            "Encryption",
            "kms management key list",
            RuntimeError("Keys in ocm-secrets were not read"),
        )
    key = next((item for item in keys if _field(item, "display-name") == "ocm-key"), None)
    evidence = {
        "vault_id": _field(vault, "id"),
        "vault_state": _field(vault, "lifecycle-state"),
        "key_id": _field(key or {}, "id"),
        "key_state": _field(key or {}, "lifecycle-state"),
    }
    if key and _field(key, "lifecycle-state") == "ENABLED":
        return _bar(4, "Encryption", "green", ["encryption_contract_satisfied"], evidence, "None.")
    return _bar(
        4,
        "Encryption",
        "yellow",
        ["key_missing_or_not_enabled"],
        evidence,
        "Restore or create the ocm-key through the prerequisite stack.",
    )


def _evaluate_storage(
    scenario: str,
    bucket_name: str | None,
    bucket: dict[str, Any] | None,
    migration_compartment_id: str,
) -> dict[str, Any]:
    if scenario == "VMware to OLVM":
        return _bar(
            5,
            "Storage",
            "not_required",
            ["scenario_does_not_require_replication_bucket"],
            {},
            "None.",
        )
    if not bucket_name:
        return _bar(
            5,
            "Storage",
            "unavailable",
            ["configured_bucket_name_unavailable"],
            {},
            "Supply --replication-bucket-name or a readable current stack variable.",
        )
    evidence = {
        "configured_bucket_name": bucket_name,
        "bucket_found": bool(bucket),
        "bucket_compartment_id": _field(bucket or {}, "compartment-id"),
        "expected_compartment_id": migration_compartment_id,
    }
    if not bucket:
        return _bar(
            5,
            "Storage",
            "red",
            ["configured_bucket_missing"],
            evidence,
            "Create the configured replication bucket through the prerequisite stack.",
        )
    if _field(bucket, "compartment-id") != migration_compartment_id:
        return _bar(
            5,
            "Storage",
            "yellow",
            ["configured_bucket_in_wrong_compartment"],
            evidence,
            "Place the configured replication bucket in the Migration compartment.",
        )
    return _bar(5, "Storage", "green", ["storage_contract_satisfied"], evidence, "None.")


def _evaluate_overall(scenario: str, bars: list[dict[str, Any]]) -> dict[str, Any]:
    required = [bar for bar in bars if bar["status"] != "not_required"]
    statuses = {bar["status"] for bar in required}
    if statuses == {"green"}:
        status, decision, codes = "green", "ready", ["all_required_bars_green"]
    elif statuses.intersection({"red", "blocked"}):
        status, decision, codes = "red", "not_ready", ["required_bar_failed"]
    elif "unavailable" in statuses:
        status, decision, codes = "unavailable", "unknown", ["required_evidence_unavailable"]
    else:
        status, decision, codes = "yellow", "not_ready", ["required_bar_partial_or_stale"]
    return _bar(
        6,
        "End-to-End Ready",
        status,
        codes,
        {
            "scenario": scenario,
            "required_bar_statuses": {
                str(bar["bar"]): bar["status"] for bar in required
            },
            "decision": decision,
        },
        "Proceed with discovery only when this decision is ready.",
    )


def _blocked_bar(number: int, name: str, dependency: str) -> dict[str, Any]:
    return _bar(
        number,
        name,
        "blocked",
        ["dependency_not_green"],
        {"dependency": dependency},
        f"Make {dependency} green, then rerun verification.",
    )


def _verify_prerequisites(
    context: OciCliContext,
    tenancy_ocid: str,
    root_compartment_ocid: str,
    scenario: str,
    primary: dict[str, Any] | None,
    explicit_bucket_name: str | None = None,
) -> dict[str, Any]:
    _preflight_root(context, tenancy_ocid, root_compartment_ocid)
    bars: list[dict[str, Any]] = []
    observed_versions = set((primary or {}).get("observed_prereq_versions", []))

    try:
        children = _list_child_compartments(context, root_compartment_ocid)
        for child in children:
            version = _prereq_version_from_tags(child)
            if version:
                observed_versions.add(version)
        compartment_bar, compartment_ids = _evaluate_compartments(children)
    except RuntimeError as error:
        compartment_bar = _unavailable_bar(
            2, "Compartment Structure", "iam compartment list", error
        )
        compartment_ids = {"Migration": None, "MigrationSecrets": None}

    try:
        namespaces = _list_tag_namespaces(context, tenancy_ocid)
        namespace = next(
            (item for item in namespaces if _field(item, "name") == "CloudMigrations"),
            None,
        )
        tags = _list_tags(context, _field(namespace, "id")) if namespace else []
        bars.append(_evaluate_identity(namespaces, tags, sorted(observed_versions)))
    except RuntimeError as error:
        bars.append(_unavailable_bar(1, "Identity Foundation", "IAM tag reads", error))

    bars.append(compartment_bar)

    migration_id = compartment_ids["Migration"]
    secrets_id = compartment_ids["MigrationSecrets"]
    if not migration_id:
        bars.append(_blocked_bar(3, "Service Authorization", "Bar 2"))
    else:
        try:
            authorization = _evaluate_authorization(
                scenario,
                _list_dynamic_groups(context, tenancy_ocid),
                _list_policies(context, tenancy_ocid),
                _list_policies(context, root_compartment_ocid),
                migration_id,
                secrets_id or "__missing_migration_secrets__",
            )
            if not secrets_id and authorization["status"] == "green":
                authorization["status"] = "yellow"
                authorization["reason_codes"] = [
                    "migration_secrets_policy_reference_unverifiable"
                ]
                authorization["next_action"] = (
                    "Restore MigrationSecrets, then verify policy references again."
                )
            bars.append(authorization)
        except RuntimeError as error:
            bars.append(
                _unavailable_bar(
                    3, "Service Authorization", "IAM authorization reads", error
                )
            )

    if not secrets_id:
        bars.append(_blocked_bar(4, "Encryption", "Bar 2"))
    else:
        try:
            vaults = _list_vaults(context, secrets_id)
            vault = next(
                (item for item in vaults if _field(item, "display-name") == "ocm-secrets"),
                None,
            )
            keys = None
            endpoint = _field(vault or {}, "management-endpoint")
            if endpoint:
                keys = _list_keys(context, secrets_id, endpoint)
            bars.append(_evaluate_encryption(vaults, keys))
        except RuntimeError as error:
            bars.append(_unavailable_bar(4, "Encryption", "KMS reads", error))

    if scenario == "VMware to OLVM":
        bars.append(_evaluate_storage(scenario, None, None, migration_id or ""))
    elif not migration_id:
        bars.append(_blocked_bar(5, "Storage", "Bar 2"))
    else:
        bucket_name = explicit_bucket_name or (primary or {}).get("replication_bucket_name")
        if not bucket_name:
            bars.append(_evaluate_storage(scenario, None, None, migration_id))
        else:
            try:
                namespace = _get_object_storage_namespace(context)
                buckets = _list_buckets(context, namespace, migration_id)
                bucket = next(
                    (item for item in buckets if _field(item, "name") == bucket_name),
                    None,
                )
                if bucket is None:
                    try:
                        bucket = _get_bucket(context, namespace, bucket_name)
                    except RuntimeError:
                        # A complete list in the required Migration compartment proves
                        # the configured bucket is absent there. A get may intentionally
                        # obscure existence elsewhere as NotAuthorizedOrNotFound.
                        bucket = None
                bars.append(
                    _evaluate_storage(scenario, bucket_name, bucket, migration_id)
                )
            except RuntimeError as error:
                bars.append(
                    _unavailable_bar(5, "Storage", "Object Storage reads", error)
                )

    overall = _evaluate_overall(scenario, bars)
    bars.append(overall)
    return {
        "schema_version": VERIFIER_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_source": CONTRACT_SOURCE,
        "scenario": scenario,
        "root_compartment_ocid": root_compartment_ocid,
        "bars": bars,
        "decision": overall["evidence"]["decision"],
        "authoritative": overall["evidence"]["decision"] in {"ready", "not_ready"},
        "authority_rule": (
            "ready requires every scenario-required bar green from live evidence; "
            "a proven required failure produces not_ready even when other evidence is "
            "unavailable; otherwise unavailable evidence produces unknown; the skill "
            "may explain but never upgrade this verdict"
        ),
    }


def _print_human(result: dict[str, Any]) -> None:
    tenancy = result["tenancy_ocid"]
    print(f"Tenancy: {tenancy}")
    print(f"Candidates analyzed: {result['candidate_count']}")
    print(f"Coverage: {result['coverage_scope']} (complete={result['coverage_complete']})")
    for warning in result.get("warnings", []):
        print(f"Warning: {warning}")
    print()

    primary = result.get("primary")
    if primary:
        print("Primary prerequisite stack (best candidate):")
        print(f"  display_name: {primary['display_name']}")
        print(f"  stack_id: {primary['stack_id']}")
        print(f"  prereq_version: {primary.get('prereq_version') or 'unknown'}")
        print(f"  variable_model: {primary.get('variable_model') or 'unknown'}")
        if primary.get("prereq_version_conflict"):
            print(f"  observed_prereq_versions: {', '.join(primary['observed_prereq_versions'])}")
        print(f"  scenario: {primary.get('scenario', 'unknown')}")
        print(f"  score: {primary['score']}")
        print(f"  root_compartment: {primary.get('stack_compartment_name')} ({primary.get('stack_compartment_id')})")
        print(f"  configured_root_compartment_ocid: {primary.get('configured_root_compartment_ocid')}")
        print(f"  latest_apply_succeeded_at: {primary.get('latest_apply_succeeded_at')}")
        print(f"  latest_destroy_succeeded_at: {primary.get('latest_destroy_succeeded_at')}")
        print(f"  latest_job: {primary.get('latest_job_operation')} {primary.get('latest_job_state')} at {primary.get('latest_job_at')}")
        print(f"  latest_job_id: {primary.get('latest_job_id')}")
        print("  reasons:")
        for r in primary.get("reasons", []):
            print(f"    - {r}")
    else:
        print("No primary prerequisite stack candidate found.")

    print()
    print("All candidates:")
    for c in result.get("candidates", []):
        print(
            f"  - {c['display_name']} | score={c['score']} | apply={c['latest_apply_succeeded_at']} | "
            f"destroy={c['latest_destroy_succeeded_at']} | stack_id={c['stack_id']}"
        )
    verification = result.get("verification")
    if verification:
        print()
        print(
            f"Readiness: {verification['decision']} "
            f"(authoritative={verification['authoritative']})"
        )
        for bar in verification["bars"]:
            print(
                f"  - Bar {bar['bar']}: {bar['name']} | {bar['status']} | "
                f"{', '.join(bar['reason_codes'])}"
            )


def main() -> int:
    args = _parse_args()
    timeout_seconds = getattr(
        args, "oci_timeout_seconds", DEFAULT_OCI_CMD_TIMEOUT_SECONDS
    )
    if timeout_seconds < 1:
        raise RuntimeError("--oci-timeout-seconds must be at least 1")
    if getattr(args, "verify", False):
        if not args.root_compartment_ocid:
            raise RuntimeError("--verify requires --root-compartment-ocid")
        if not getattr(args, "scenario", None):
            raise RuntimeError("--verify requires --scenario")
    context = OciCliContext(
        profile=args.profile,
        config_file=args.config_file,
        auth=args.auth,
        region=args.region,
        cert_bundle=args.cert_bundle,
        timeout_seconds=timeout_seconds,
    )

    if args.tenancy_ocid:
        tenancy_ocid = args.tenancy_ocid
    elif args.auth in CONFIGLESS_AUTH_MODES:
        raise RuntimeError(
            f"--tenancy-ocid is required with --auth {args.auth}; "
            "that auth mode does not require an OCI config profile."
        )
    else:
        tenancy_ocid = _load_tenancy_from_config(args.config_file, args.profile)

    discover_artifact_roots = not args.root_compartment_ocid or args.scan_all_compartments
    compartments = (
        _discover_compartments(context, tenancy_ocid)
        if discover_artifact_roots
        else []
    )
    roots = _artifact_roots(compartments)

    roots_to_scan = (
        {args.root_compartment_ocid}
        if args.root_compartment_ocid
        else set(roots.keys())
    )
    explicit_stack_compartment_ocids = set(getattr(args, "stack_compartment_ocid", []))
    roots_to_scan.update(explicit_stack_compartment_ocids)
    if args.scan_all_compartments:
        roots_to_scan.add(tenancy_ocid)
        for c in compartments:
            cid = c.get("id")
            if cid:
                roots_to_scan.add(cid)

    if args.scan_all_compartments:
        coverage_scope = "all_accessible_compartments"
        coverage_complete = True
    elif args.root_compartment_ocid and explicit_stack_compartment_ocids:
        coverage_scope = "selected_root_and_explicit_stack_compartments"
        coverage_complete = False
    elif args.root_compartment_ocid:
        coverage_scope = "selected_root_only"
        coverage_complete = False
    elif explicit_stack_compartment_ocids:
        coverage_scope = "explicit_stack_compartments_and_artifact_roots"
        coverage_complete = False
    else:
        coverage_scope = "artifact_roots_only"
        coverage_complete = False

    coverage_limitations: list[str] = []
    if not coverage_complete:
        coverage_limitations.append(
            "RMS stacks outside the scanned compartments may be omitted. "
            "Pass --scan-all-compartments for tenancy-wide accessible coverage, "
            "or pass --stack-compartment-ocid for each known RMS stack compartment."
        )
    by_id = {c.get("id"): c for c in compartments}
    candidates: list[dict[str, Any]] = []
    warnings: list[str] = []
    requested_scan_complete = True
    for root_id in sorted(roots_to_scan):
        try:
            stacks = _list_stacks(context, root_id)
        except RuntimeError as e:
            coverage_complete = False
            requested_scan_complete = False
            coverage_limitations.append(
                f"Stack listing failed in compartment {root_id}; candidates there may be omitted."
            )
            warnings.append(f"Could not list stacks in compartment {root_id}: {e}")
            continue

        root_artifact = roots.get(root_id) or {
            "root_compartment_id": root_id,
            "root_compartment_name": by_id.get(root_id, {}).get("name", "<selected-root>"),
            "has_migration": False,
            "has_migration_secrets": False,
            "migration_compartment_id": None,
            "migration_secrets_compartment_id": None,
            "observed_prereq_versions": [],
        }
        for stack_summary in stacks:
            stack_id = stack_summary.get("id")
            stack_name = stack_summary.get("display-name") or stack_id or "<unknown>"
            stack = stack_summary
            if stack_id:
                try:
                    stack = _get_stack(context, stack_id)
                except RuntimeError as e:
                    coverage_complete = False
                    requested_scan_complete = False
                    coverage_limitations.append(
                        f"Stack details could not be read for {stack_name}; "
                        "prerequisite classification may be incomplete."
                    )
                    warnings.append(f"Could not read stack details for {stack_name}: {e}")
            if not _is_prereq_stack(stack, root_id):
                continue
            configured_root_id = (stack.get("variables") or {}).get("compartment_ocid")
            candidate_root_artifact = roots.get(configured_root_id) or root_artifact
            if not stack_id:
                jobs = []
                warnings.append(f"Could not read job history for {stack_name}: stack id is missing")
            else:
                try:
                    jobs = _list_jobs(context, stack_id)
                except RuntimeError as e:
                    jobs = []
                    warnings.append(f"Could not read job history for {stack_name}: {e}")
            scoring = _stack_score(stack, jobs, candidate_root_artifact)
            row = _to_row(
                stack,
                candidate_root_artifact,
                scoring,
                selected_root_compartment_ocid=args.root_compartment_ocid,
            )
            candidates.append(row)

    candidates.sort(
        key=lambda c: (c["score"], _parse_time(c["latest_apply_succeeded_at"]), c["display_name"] or ""),
        reverse=True,
    )
    primary = _select_primary(candidates, args.root_compartment_ocid)

    result = {
        "tenancy_ocid": tenancy_ocid,
        "selected_root_compartment_ocid": args.root_compartment_ocid,
        "explicit_stack_compartment_ocids": sorted(explicit_stack_compartment_ocids),
        "scanned_compartment_ocids": sorted(roots_to_scan),
        "candidate_count": len(candidates),
        "primary": primary,
        "candidates": candidates,
        "coverage_scope": coverage_scope,
        "coverage_complete": coverage_complete,
        "requested_scan_complete": requested_scan_complete,
        "coverage_limitations": coverage_limitations,
        "warnings": warnings,
        "artifact_roots": sorted(
            [
                {
                    "root_compartment_id": v["root_compartment_id"],
                    "root_compartment_name": v["root_compartment_name"],
                    "has_migration": v["has_migration"],
                    "has_migration_secrets": v["has_migration_secrets"],
                    "observed_prereq_versions": sorted(v["observed_prereq_versions"]),
                }
                for v in roots.values()
            ],
            key=lambda x: x["root_compartment_name"],
        ),
    }
    if getattr(args, "verify", False):
        result["verification"] = _verify_prerequisites(
            context,
            tenancy_ocid,
            args.root_compartment_ocid,
            args.scenario,
            primary,
            getattr(args, "replication_bucket_name", None),
        )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)
