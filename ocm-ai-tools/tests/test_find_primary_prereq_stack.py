import argparse
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "migration-prereqs"
    / "scripts"
    / "find_primary_prereq_stack.py"
)
SPEC = importlib.util.spec_from_file_location("find_primary_prereq_stack", SCRIPT)
DETECTOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = DETECTOR
SPEC.loader.exec_module(DETECTOR)


class DetectorTests(unittest.TestCase):
    def test_selected_root_is_scanned_without_surviving_compartments(self):
        args = argparse.Namespace(
            profile="DEFAULT",
            config_file="/tmp/oci-config",
            auth=None,
            region=None,
            cert_bundle=None,
            tenancy_ocid="test-tenancy",
            root_compartment_ocid="test-root",
            stack_compartment_ocid=[],
            scan_all_compartments=False,
            json=True,
        )
        stack = {
            "id": "test-stack",
            "display-name": "OCM Prerequisites",
            "compartment-id": args.root_compartment_ocid,
            "variables": {
                "tenancy_ocid": args.tenancy_ocid,
                "compartment_ocid": args.root_compartment_ocid,
                "enabled_migration_scenario": "VMware to OCI",
            },
        }
        jobs = [
            {
                "operation": "APPLY",
                "lifecycle-state": "FAILED",
                "time-finished": "2026-07-20T12:00:00+00:00",
            }
        ]

        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(
                DETECTOR, "_discover_compartments", return_value=[]
            ) as discover_compartments,
            mock.patch.object(DETECTOR, "_list_stacks", return_value=[stack]),
            mock.patch.object(DETECTOR, "_get_stack", return_value=stack),
            mock.patch.object(DETECTOR, "_list_jobs", return_value=jobs),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["primary"]["stack_id"], stack["id"])
        self.assertEqual(result["primary"]["latest_job_state"], "FAILED")
        self.assertEqual(result["coverage_scope"], "selected_root_only")
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(result["requested_scan_complete"])
        self.assertEqual(result["scanned_compartment_ocids"], ["test-root"])
        self.assertTrue(result["coverage_limitations"])
        discover_compartments.assert_not_called()

    def test_configless_auth_requires_explicit_tenancy_without_reading_config(self):
        for auth in (
            "instance_principal",
            "resource_principal",
            "oke_workload_identity",
        ):
            with self.subTest(auth=auth):
                args = argparse.Namespace(
                    profile="DEFAULT",
                    config_file="/missing/oci-config",
                    auth=auth,
                    region=None,
                    cert_bundle=None,
                    tenancy_ocid=None,
                    root_compartment_ocid="test-root",
                    stack_compartment_ocid=[],
                    scan_all_compartments=False,
                    json=True,
                )
                with mock.patch.object(DETECTOR, "_parse_args", return_value=args):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        rf"--tenancy-ocid is required with --auth {auth}",
                    ):
                        DETECTOR.main()

    def test_configless_auth_with_explicit_tenancy_does_not_read_config(self):
        for auth in (
            "instance_principal",
            "resource_principal",
            "oke_workload_identity",
        ):
            with self.subTest(auth=auth):
                args = argparse.Namespace(
                    profile="DEFAULT",
                    config_file="/missing/oci-config",
                    auth=auth,
                    region=None,
                    cert_bundle=None,
                    tenancy_ocid="test-tenancy",
                    root_compartment_ocid="test-root",
                    stack_compartment_ocid=[],
                    scan_all_compartments=False,
                    json=True,
                )
                with (
                    mock.patch.object(DETECTOR, "_parse_args", return_value=args),
                    mock.patch.object(
                        DETECTOR, "_load_tenancy_from_config"
                    ) as load_tenancy,
                    mock.patch.object(
                        DETECTOR, "_discover_compartments"
                    ) as discover_compartments,
                    mock.patch.object(
                        DETECTOR, "_list_stacks", return_value=[]
                    ) as list_stacks,
                ):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(DETECTOR.main(), 0)

                load_tenancy.assert_not_called()
                discover_compartments.assert_not_called()
                self.assertEqual(list_stacks.call_args.args[0].auth, auth)

    def test_explicit_stack_compartment_finds_stack_stored_outside_selected_root(self):
        args = argparse.Namespace(
            profile="DEFAULT",
            config_file="/tmp/oci-config",
            auth=None,
            region=None,
            cert_bundle=None,
            tenancy_ocid="test-tenancy",
            root_compartment_ocid="test-root",
            stack_compartment_ocid=["rms-stack-compartment"],
            scan_all_compartments=False,
            json=True,
        )
        stack = {
            "id": "test-stack",
            "display-name": "OCM Prerequisites",
            "compartment-id": "rms-stack-compartment",
            "variables": {
                "tenancy_ocid": args.tenancy_ocid,
                "compartment_ocid": args.root_compartment_ocid,
                "enabled_migration_scenario": "VMware to OCI",
            },
        }
        scanned = []

        def list_stacks(_context, compartment_id):
            scanned.append(compartment_id)
            return [stack] if compartment_id == "rms-stack-compartment" else []

        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(DETECTOR, "_discover_compartments", return_value=[]),
            mock.patch.object(DETECTOR, "_list_stacks", side_effect=list_stacks),
            mock.patch.object(DETECTOR, "_get_stack", return_value=stack),
            mock.patch.object(DETECTOR, "_list_jobs", return_value=[]),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        result = json.loads(stdout.getvalue())
        self.assertEqual(
            result["coverage_scope"],
            "selected_root_and_explicit_stack_compartments",
        )
        self.assertEqual(
            result["scanned_compartment_ocids"],
            ["rms-stack-compartment", "test-root"],
        )
        self.assertEqual(sorted(scanned), result["scanned_compartment_ocids"])
        self.assertEqual(result["primary"]["stack_id"], "test-stack")
        self.assertTrue(result["primary"]["selected_root_match"])
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(result["requested_scan_complete"])

    def test_selected_root_does_not_scan_unrelated_artifact_roots(self):
        args = argparse.Namespace(
            profile="DEFAULT",
            config_file="/tmp/oci-config",
            auth=None,
            region=None,
            cert_bundle=None,
            tenancy_ocid="test-tenancy",
            root_compartment_ocid="selected-root",
            stack_compartment_ocid=[],
            scan_all_compartments=False,
            json=True,
        )
        compartments = [
            {
                "id": "unrelated-migration",
                "name": "Migration",
                "compartment-id": "unrelated-root",
            }
        ]
        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(
                DETECTOR, "_discover_compartments", return_value=compartments
            ),
            mock.patch.object(DETECTOR, "_list_stacks", return_value=[]) as list_stacks,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        self.assertEqual(
            [call.args[1] for call in list_stacks.call_args_list],
            ["selected-root"],
        )

    def test_separate_stack_compartment_detection_does_not_depend_on_display_name(self):
        stack = {
            "display-name": "central-rms-deployment",
            "compartment-id": "rms-stack-compartment",
            "variables": {
                "tenancy_ocid": "test-tenancy",
                "compartment_ocid": "test-root",
                "enabled_migration_scenario": "VMware to OCI",
            },
        }

        self.assertTrue(
            DETECTOR._is_prereq_stack(stack, "rms-stack-compartment")
        )

    def test_stack_listing_failure_is_visible_and_marks_coverage_incomplete(self):
        args = argparse.Namespace(
            profile="DEFAULT",
            config_file="/tmp/oci-config",
            auth=None,
            region=None,
            cert_bundle=None,
            tenancy_ocid="test-tenancy",
            root_compartment_ocid="test-root",
            stack_compartment_ocid=[],
            scan_all_compartments=False,
            json=True,
        )
        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(DETECTOR, "_discover_compartments", return_value=[]),
            mock.patch.object(DETECTOR, "_list_stacks", side_effect=RuntimeError("not authorized")),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        result = json.loads(stdout.getvalue())
        self.assertFalse(result["coverage_complete"])
        self.assertFalse(result["requested_scan_complete"])
        self.assertEqual(result["candidate_count"], 0)
        self.assertIn("not authorized", result["warnings"][0])

    def test_unreadable_stack_details_make_scan_classification_incomplete(self):
        args = argparse.Namespace(
            profile="DEFAULT",
            config_file="/tmp/oci-config",
            auth=None,
            region=None,
            cert_bundle=None,
            tenancy_ocid="test-tenancy",
            root_compartment_ocid="test-root",
            stack_compartment_ocid=[],
            scan_all_compartments=True,
            json=True,
        )
        stack = {
            "id": "test-stack",
            "display-name": "OCM Prerequisites",
            "compartment-id": "test-root",
        }

        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(DETECTOR, "_discover_compartments", return_value=[]),
            mock.patch.object(
                DETECTOR,
                "_list_stacks",
                side_effect=lambda _context, compartment_id: (
                    [stack] if compartment_id == "test-root" else []
                ),
            ),
            mock.patch.object(
                DETECTOR, "_get_stack", side_effect=RuntimeError("details denied")
            ),
            mock.patch.object(DETECTOR, "_list_jobs", return_value=[]),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        result = json.loads(stdout.getvalue())
        self.assertFalse(result["coverage_complete"])
        self.assertFalse(result["requested_scan_complete"])
        self.assertTrue(
            any("classification may be incomplete" in item for item in result["coverage_limitations"])
        )

    def test_selected_root_candidate_beats_stronger_candidate_in_another_root(self):
        candidates = [
            {
                "stack_id": "other-root-stack",
                "score": 5,
                "selected_root_match": False,
            },
            {
                "stack_id": "selected-root-stack",
                "score": 0,
                "selected_root_match": True,
            },
        ]

        primary = DETECTOR._select_primary(candidates, "selected-root")

        self.assertEqual(primary["stack_id"], "selected-root-stack")

    def test_selected_root_with_no_matching_candidate_has_no_primary(self):
        candidates = [
            {
                "stack_id": "other-root-stack",
                "score": 5,
                "selected_root_match": False,
            },
        ]

        self.assertIsNone(DETECTOR._select_primary(candidates, "selected-root"))

    def test_candidate_matches_selected_root_by_stack_or_configured_root(self):
        scoring = {
            "score": 0,
            "latest_apply_succeeded_at": None,
            "latest_destroy_succeeded_at": None,
            "latest_job_operation": None,
            "latest_job_state": None,
            "latest_job_id": None,
            "latest_job_at": None,
            "reasons": [],
        }
        by_stack_compartment = DETECTOR._to_row(
            {"compartment-id": "selected-root", "variables": {}},
            None,
            scoring,
            "selected-root",
        )
        by_configured_root = DETECTOR._to_row(
            {
                "compartment-id": "different-root",
                "variables": {"compartment_ocid": "selected-root"},
            },
            None,
            scoring,
            "selected-root",
        )

        self.assertTrue(by_stack_compartment["selected_root_match"])
        self.assertEqual(
            by_stack_compartment["selected_root_match_source"],
            "stack_compartment_id_fallback",
        )
        self.assertTrue(by_configured_root["selected_root_match"])
        self.assertEqual(
            by_configured_root["selected_root_match_source"],
            "configured_root_compartment_ocid",
        )

    def test_configured_root_wins_when_stack_compartment_disagrees(self):
        scoring = {
            "score": 0,
            "latest_apply_succeeded_at": None,
            "latest_destroy_succeeded_at": None,
            "latest_job_operation": None,
            "latest_job_state": None,
            "latest_job_id": None,
            "latest_job_at": None,
            "reasons": [],
        }

        row = DETECTOR._to_row(
            {
                "compartment-id": "selected-root",
                "variables": {"compartment_ocid": "configured-other-root"},
            },
            None,
            scoring,
            "selected-root",
        )

        self.assertFalse(row["selected_root_match"])
        self.assertEqual(
            row["selected_root_match_source"],
            "configured_root_compartment_ocid",
        )

    def test_invalid_oci_json_is_reported(self):
        completed = subprocess.CompletedProcess([], 0, stdout="not-json", stderr="")
        with mock.patch.object(DETECTOR.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                DETECTOR._oci(
                    DETECTOR.OciCliContext("DEFAULT", "/tmp/oci-config"),
                    ["iam", "region", "list"],
                )

    def test_oci_passes_session_auth_region_and_cert_bundle_as_global_options(self):
        completed = subprocess.CompletedProcess([], 0, stdout='{"data": []}', stderr="")
        context = DETECTOR.OciCliContext(
            profile="session-profile",
            config_file="/tmp/oci-config",
            auth="security_token",
            region="r1",
            cert_bundle="/tmp/ca-bundle.pem",
        )
        with mock.patch.object(DETECTOR.subprocess, "run", return_value=completed) as run:
            self.assertEqual(DETECTOR._oci(context, ["iam", "region", "list"]), [])

        command = run.call_args.args[0]
        self.assertEqual(
            command,
            [
                "oci",
                "--profile",
                "session-profile",
                "--config-file",
                "/tmp/oci-config",
                "--output",
                "json",
                "--auth",
                "security_token",
                "--region",
                "r1",
                "--cert-bundle",
                "/tmp/ca-bundle.pem",
                "iam",
                "region",
                "list",
            ],
        )

    def test_oci_omits_optional_global_options_by_default(self):
        completed = subprocess.CompletedProcess([], 0, stdout='{"data": []}', stderr="")
        context = DETECTOR.OciCliContext("DEFAULT", "/tmp/oci-config")
        with mock.patch.object(DETECTOR.subprocess, "run", return_value=completed) as run:
            self.assertEqual(DETECTOR._oci(context, ["iam", "region", "list"]), [])

        command = run.call_args.args[0]
        self.assertNotIn("--auth", command)
        self.assertNotIn("--region", command)
        self.assertNotIn("--cert-bundle", command)

    def test_oci_accepts_suppressed_output_for_an_empty_list(self):
        completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        context = DETECTOR.OciCliContext("DEFAULT", "/tmp/oci-config")
        with mock.patch.object(DETECTOR.subprocess, "run", return_value=completed):
            self.assertEqual(
                DETECTOR._oci(context, ["iam", "compartment", "list"], allow_empty=True),
                [],
            )

    def test_oci_rejects_suppressed_output_for_a_get(self):
        completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        context = DETECTOR.OciCliContext("DEFAULT", "/tmp/oci-config")
        with mock.patch.object(DETECTOR.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "produced no JSON output"):
                DETECTOR._oci(context, ["resource-manager", "stack", "get"])

    def test_oci_uses_configured_timeout_and_reports_neutral_diagnostics(self):
        context = DETECTOR.OciCliContext(
            "DEFAULT",
            "/tmp/oci-config",
            timeout_seconds=75,
        )
        with mock.patch.object(
            DETECTOR.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["oci"], timeout=75),
        ) as run:
            with self.assertRaises(RuntimeError) as raised:
                DETECTOR._oci(context, ["iam", "compartment", "list"])

        self.assertEqual(run.call_args.kwargs["timeout"], 75)
        self.assertIn("timed out after 75s", str(raised.exception))
        self.assertIn("endpoint latency", str(raised.exception))
        self.assertNotIn("usually means authentication is stale", str(raised.exception))

    def test_bool_additive_scenario_is_rendered_as_customer_label(self):
        variables = {
            "enabled_migration_scenario": "AWS to OCI",
            "add_vmware_to_olvm": True,
        }
        self.assertEqual(
            DETECTOR._extract_scenario(variables, "v2.3+"),
            "AWS to OCI, VMware to OLVM",
        )

    def test_primary_migration_scenario_uses_transitional_model(self):
        variables = {"primary_migration_scenario": "aws_to_oci"}
        variable_model = DETECTOR._detect_variable_model(variables)

        self.assertEqual(variable_model, "pre-v2.3-rename")
        self.assertEqual(
            DETECTOR._extract_scenario(variables, variable_model),
            "AWS to OCI",
        )

    def test_v21_boolean_variables_preserve_both_enabled_sources(self):
        variables = {
            "migration_from_vmware": "true",
            "migration_from_aws": True,
        }
        variable_model = DETECTOR._detect_variable_model(variables)

        self.assertEqual(variable_model, "v2.1")
        self.assertEqual(
            DETECTOR._extract_scenario(variables, variable_model),
            "VMware, AWS",
        )

    def test_exact_version_comes_from_resource_tags_not_current_variables(self):
        compartments = [
            {
                "id": "migration-compartment",
                "name": "Migration",
                "compartment-id": "test-root",
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteVersion": "2.4"},
                },
            },
        ]
        root = DETECTOR._artifact_roots(compartments)["test-root"]
        stack = {
            "variables": {
                "enabled_migration_scenario": "AWS to OCI",
                "primary_prerequisite_stack": True,
            },
        }

        row = DETECTOR._to_row(stack, root, DETECTOR._stack_score(stack, [], root))

        self.assertEqual(row["prereq_version"], "2.4")
        self.assertEqual(row["variable_model"], "v2.3+")
        self.assertFalse(row["prereq_version_conflict"])

    def test_conflicting_resource_versions_are_preserved(self):
        compartments = [
            {
                "id": "migration-compartment",
                "name": "Migration",
                "compartment-id": "test-root",
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteVersion": "2.3"},
                },
            },
            {
                "id": "secrets-compartment",
                "name": "MigrationSecrets",
                "compartment-id": "test-root",
                "defined_tags": {
                    "CloudMigrations": {"PrerequisiteVersion": "2.4"},
                },
            },
        ]
        root = DETECTOR._artifact_roots(compartments)["test-root"]

        row = DETECTOR._to_row({}, root, DETECTOR._stack_score({}, [], root))

        self.assertIsNone(row["prereq_version"])
        self.assertEqual(row["observed_prereq_versions"], ["2.3", "2.4"])
        self.assertTrue(row["prereq_version_conflict"])

    def test_latest_failed_job_is_exposed_even_with_success_history(self):
        jobs = [
            {
                "operation": "APPLY",
                "lifecycle-state": "SUCCEEDED",
                "id": "successful-job",
                "time-finished": "2026-07-19T12:00:00+00:00",
            },
            {
                "operation": "APPLY",
                "lifecycle-state": "FAILED",
                "id": "failed-job",
                "time-finished": "2026-07-20T12:00:00+00:00",
            },
        ]
        result = DETECTOR._stack_score({}, jobs, None)
        self.assertEqual(result["latest_job_operation"], "APPLY")
        self.assertEqual(result["latest_job_state"], "FAILED")
        self.assertEqual(result["latest_job_id"], "failed-job")
        self.assertIn("latest job is APPLY FAILED", result["reasons"])

    def test_destroy_after_apply_marks_the_stack_as_torn_down(self):
        jobs = [
            {
                "operation": "APPLY",
                "lifecycle-state": "SUCCEEDED",
                "time-finished": "2026-07-19T12:00:00+00:00",
            },
            {
                "operation": "DESTROY",
                "lifecycle-state": "SUCCEEDED",
                "time-finished": "2026-07-20T12:00:00+00:00",
            },
        ]

        result = DETECTOR._stack_score({}, jobs, None)

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["latest_job_operation"], "DESTROY")
        self.assertIn("latest successful mutation is DESTROY", result["reasons"])

    def test_identity_bar_is_green_only_with_full_live_contract_and_compatible_version(self):
        namespaces = [
            {
                "id": "namespace",
                "name": "CloudMigrations",
                "lifecycle-state": "ACTIVE",
            }
        ]
        tags = [
            {"name": name, "lifecycle-state": "ACTIVE"}
            for name in DETECTOR.REQUIRED_TAGS
        ]

        result = DETECTOR._evaluate_identity(namespaces, tags, ["2.4"])

        self.assertEqual(result["status"], "green")
        self.assertEqual(result["reason_codes"], ["identity_contract_satisfied"])

    def test_custom_iam_names_can_satisfy_deterministic_content_contract(self):
        migration_id = "migration-compartment"
        secrets_id = "secrets-compartment"
        groups = [
            {
                "id": "migration-group",
                "name": "central-migration-principal",
                "lifecycle-state": "ACTIVE",
                "matching-rule": (
                    "ALL { resource.type = 'ocmmigration', "
                    f"resource.compartment.id = '{migration_id}' }}"
                ),
            },
            {
                "id": "discovery-group",
                "name": "central-discovery-principal",
                "lifecycle-state": "ACTIVE",
                "matching-rule": "Any { resource.type = 'ocbassetsource' }",
            },
            {
                "id": "hydration-group",
                "name": "central-hydration-principal",
                "lifecycle-state": "ACTIVE",
                "matching-rule": (
                    f"ALL {{ instance.compartment.id = '{migration_id}' }}"
                ),
            },
        ]
        tenancy_policy = {
            "name": "central-tenancy-policy",
            "lifecycle-state": "ACTIVE",
            "statements": [
                (
                    "Allow dynamic-group central-migration-principal to read "
                    "ocb-inventory in tenancy"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ INSTANCE_INSPECT } in tenancy where any "
                    "{ request.operation='ListShapes' }"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ DEDICATED_VM_HOST_READ } in tenancy where any "
                    "{ request.operation='GetDedicatedVmHost' }"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ CAPACITY_RESERVATION_READ } in tenancy where any "
                    "{ request.operation='GetComputeCapacityReservation' }"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ ORGANIZATIONS_SUBSCRIPTION_INSPECT } in tenancy where any "
                    "{ request.operation='ListSubscriptions' }"
                ),
                (
                    "Allow dynamic-group central-migration-principal to read "
                    "rate-cards in tenancy"
                ),
                (
                    "Allow dynamic-group central-migration-principal to read "
                    "metrics in tenancy where target.metrics.namespace='ocb_asset'"
                ),
                (
                    "Allow dynamic-group central-migration-principal to read "
                    "tag-namespaces in tenancy"
                ),
                (
                    "Allow dynamic-group central-migration-principal to use "
                    "tag-namespaces in tenancy where "
                    "target.tag-namespace.name='CloudMigrations'"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to read "
                    "ocb-inventory in tenancy"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to "
                    "{ TENANCY_INSPECT } in tenancy"
                ),
            ],
        }
        root_policy = {
            "name": "central-root-policy",
            "lifecycle-state": "ACTIVE",
            "statements": [
                (
                    "Allow dynamic-group central-migration-principal to manage "
                    f"instance-family in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to manage "
                    f"compute-image-capability-schema in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to manage "
                    f"virtual-network-family in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to manage "
                    f"volume-family in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to manage "
                    f"object-family in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to read "
                    f"ocb-inventory-asset in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ OCB_CONNECTOR_READ, OCB_CONNECTOR_DATA_READ, "
                    "OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_CONNECTOR_DATA_UPDATE } "
                    f"in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-migration-principal to "
                    "{ INSTANCE_IMAGE_INSPECT, INSTANCE_IMAGE_READ } "
                    f"in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to read "
                    f"ocb-environment in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to manage "
                    f"ocb-inventory-asset in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to inspect "
                    f"compartments in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to use "
                    f"metrics in compartment id {migration_id} where "
                    "target.metrics.namespace='ocb_asset'"
                ),
                (
                    "Allow dynamic-group central-discovery-principal to read "
                    f"secret-family in compartment id {secrets_id}"
                ),
                (
                    "Allow dynamic-group central-hydration-principal to "
                    "{ OCM_HYDRATION_AGENT_TASK_INSPECT, "
                    "OCM_HYDRATION_AGENT_TASK_UPDATE, "
                    "OCM_HYDRATION_AGENT_REPORT_STATUS } "
                    f"in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-hydration-principal to manage "
                    f"objects in compartment id {migration_id}"
                ),
                (
                    "Allow dynamic-group central-hydration-principal to read "
                    f"secret-family in compartment id {secrets_id}"
                ),
            ],
        }

        result = DETECTOR._evaluate_authorization(
            "AWS to OCI",
            groups,
            [tenancy_policy],
            [root_policy],
            migration_id,
            secrets_id,
        )

        self.assertEqual(result["status"], "green")
        self.assertEqual(
            result["evidence"]["dynamic_groups"]["migration"]["name"],
            "central-migration-principal",
        )

        missing_permission_result = DETECTOR._evaluate_authorization(
            "AWS to OCI",
            groups,
            [tenancy_policy],
            [
                {
                    **root_policy,
                    "statements": [
                        statement
                        for statement in root_policy["statements"]
                        if "INSTANCE_IMAGE_INSPECT" not in statement
                    ],
                }
            ],
            migration_id,
            secrets_id,
        )
        self.assertEqual(missing_permission_result["status"], "yellow")
        self.assertIn(
            "read_instance_images",
            missing_permission_result["evidence"]["missing_policy_fragments"][
                "migration"
            ]["migration_root"],
        )

        inactive_result = DETECTOR._evaluate_authorization(
            "AWS to OCI",
            groups,
            [{**tenancy_policy, "lifecycle-state": "INACTIVE"}],
            [root_policy],
            migration_id,
            secrets_id,
        )
        self.assertEqual(inactive_result["status"], "yellow")

    def test_dynamic_group_matching_does_not_accept_prefix_values(self):
        roles, invalid = DETECTOR._find_dynamic_group_roles(
            [
                {
                    "name": "wrong-migration",
                    "lifecycle-state": "ACTIVE",
                    "matching-rule": (
                        "ALL { resource.type = 'ocmmigration-extra', "
                        "resource.compartment.id = 'migration-compartment-extra' }"
                    ),
                }
            ],
            "migration-compartment",
        )

        self.assertNotIn("migration", roles)
        self.assertEqual(invalid["migration"], "missing_or_wrong_matching_rule")

    def test_dynamic_group_matching_rejects_overbroad_any_rule(self):
        roles, invalid = DETECTOR._find_dynamic_group_roles(
            [
                {
                    "name": "overbroad-migration",
                    "lifecycle-state": "ACTIVE",
                    "matching-rule": (
                        "ANY { resource.type = 'ocmmigration', "
                        "resource.compartment.id = 'migration-compartment' }"
                    ),
                }
            ],
            "migration-compartment",
        )

        self.assertNotIn("migration", roles)
        self.assertEqual(invalid["migration"], "missing_or_wrong_matching_rule")

    def test_dynamic_group_matching_rejects_extra_any_clause(self):
        roles, invalid = DETECTOR._find_dynamic_group_roles(
            [
                {
                    "name": "overbroad-discovery",
                    "lifecycle-state": "ACTIVE",
                    "matching-rule": (
                        "ANY { resource.type = 'ocbassetsource', "
                        "resource.type = 'instance' }"
                    ),
                }
            ],
            "migration-compartment",
        )

        self.assertNotIn("discovery", roles)
        self.assertEqual(invalid["discovery"], "missing_or_wrong_matching_rule")

    def test_v24_authorization_requirements_are_scenario_specific(self):
        aws_tenancy, aws_root = DETECTOR._authorization_policy_requirements(
            "AWS to OCI", "migration", "secrets"
        )
        vmware_tenancy, vmware_root = DETECTOR._authorization_policy_requirements(
            "VMware to OCI", "migration", "secrets"
        )
        olvm_tenancy, olvm_root = DETECTOR._authorization_policy_requirements(
            "VMware to OLVM", "migration", "secrets"
        )

        self.assertFalse(aws_tenancy["remote_agent"])
        self.assertIn("read_migration_secrets", aws_root["discovery"])
        self.assertIn("manage_replication_objects", aws_root["hydration_agent"])
        self.assertIn("manage_ocb_agent", vmware_tenancy["remote_agent"])
        self.assertIn("read_agents", vmware_root["discovery"])
        self.assertIn("read_replication_objects", vmware_root["hydration_agent"])
        self.assertIn("manage_ocb_agent", olvm_tenancy["remote_agent"])
        self.assertIn("read_migration_secrets", olvm_root["discovery"])
        self.assertFalse(olvm_root["hydration_agent"])

    def test_overall_verdict_cannot_upgrade_unavailable_evidence_to_ready(self):
        bars = [
            DETECTOR._bar(i, f"Bar {i}", "green", [], {}, "None.")
            for i in range(1, 5)
        ]
        bars.append(
            DETECTOR._bar(
                5,
                "Storage",
                "unavailable",
                ["configured_bucket_name_unavailable"],
                {},
                "Supply the configured bucket name.",
            )
        )

        result = DETECTOR._evaluate_overall("VMware to OCI", bars)

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["evidence"]["decision"], "unknown")

    def test_proven_required_failure_precedes_unavailable_evidence(self):
        bars = [
            DETECTOR._bar(
                1,
                "Identity Foundation",
                "red",
                ["tag_namespace_missing_or_inactive"],
                {},
                "Restore the tag namespace.",
            ),
            DETECTOR._bar(2, "Compartment Structure", "green", [], {}, "None."),
            DETECTOR._bar(3, "Service Authorization", "green", [], {}, "None."),
            DETECTOR._bar(4, "Encryption", "green", [], {}, "None."),
            DETECTOR._bar(
                5,
                "Storage",
                "unavailable",
                ["configured_bucket_name_unavailable"],
                {},
                "Supply the configured bucket name.",
            ),
        ]

        result = DETECTOR._evaluate_overall("AWS to OCI", bars)

        self.assertEqual(result["status"], "red")
        self.assertEqual(result["reason_codes"], ["required_bar_failed"])
        self.assertEqual(result["evidence"]["decision"], "not_ready")

    def test_missing_secrets_compartment_does_not_block_independent_storage_read(self):
        migration = {
            "id": "migration-compartment",
            "name": "Migration",
            "lifecycle-state": "ACTIVE",
            "defined-tags": {
                "CloudMigrations": {"PrerequisiteResourceLevel": "compartment"}
            },
        }
        green_authorization = DETECTOR._bar(
            3,
            "Service Authorization",
            "green",
            ["authorization_contract_satisfied"],
            {},
            "None.",
        )
        with (
            mock.patch.object(DETECTOR, "_preflight_root"),
            mock.patch.object(DETECTOR, "_list_tag_namespaces", return_value=[]),
            mock.patch.object(DETECTOR, "_list_child_compartments", return_value=[migration]),
            mock.patch.object(DETECTOR, "_list_dynamic_groups", return_value=[]),
            mock.patch.object(DETECTOR, "_list_policies", return_value=[]),
            mock.patch.object(
                DETECTOR,
                "_evaluate_authorization",
                return_value=green_authorization,
            ),
            mock.patch.object(
                DETECTOR, "_get_object_storage_namespace", return_value="namespace"
            ),
            mock.patch.object(
                DETECTOR,
                "_list_buckets",
                return_value=[
                    {
                        "name": "customer-migration-data",
                        "compartment-id": "migration-compartment",
                    }
                ],
            ),
            mock.patch.object(DETECTOR, "_list_vaults") as list_vaults,
        ):
            result = DETECTOR._verify_prerequisites(
                DETECTOR.OciCliContext("DEFAULT", "/tmp/oci-config"),
                "tenancy",
                "root",
                "AWS to OCI",
                {"replication_bucket_name": "customer-migration-data"},
            )

        statuses = {bar["bar"]: bar["status"] for bar in result["bars"]}
        self.assertEqual(statuses[2], "yellow")
        self.assertEqual(statuses[3], "yellow")
        self.assertEqual(statuses[4], "blocked")
        self.assertEqual(statuses[5], "green")
        self.assertEqual(statuses[6], "red")
        self.assertEqual(result["decision"], "not_ready")
        self.assertTrue(result["authoritative"])
        list_vaults.assert_not_called()

    def test_parse_args_exposes_the_public_cli_contract(self):
        argv = [
            str(SCRIPT),
            "--profile",
            "SESSION",
            "--config-file",
            "/config",
            "--auth",
            "security_token",
            "--region",
            "us-phoenix-1",
            "--cert-bundle",
            "/ca.pem",
            "--oci-timeout-seconds",
            "45",
            "--tenancy-ocid",
            "tenancy",
            "--root-compartment-ocid",
            "root",
            "--stack-compartment-ocid",
            "stack-a",
            "--stack-compartment-ocid",
            "stack-b",
            "--scan-all-compartments",
            "--verify",
            "--scenario",
            "AWS to OCI",
            "--replication-bucket-name",
            "replication",
            "--json",
        ]

        with mock.patch.object(sys, "argv", argv):
            args = DETECTOR._parse_args()

        self.assertEqual(args.profile, "SESSION")
        self.assertEqual(args.config_file, "/config")
        self.assertEqual(args.auth, "security_token")
        self.assertEqual(args.region, "us-phoenix-1")
        self.assertEqual(args.cert_bundle, "/ca.pem")
        self.assertEqual(args.oci_timeout_seconds, 45)
        self.assertEqual(args.tenancy_ocid, "tenancy")
        self.assertEqual(args.root_compartment_ocid, "root")
        self.assertEqual(args.stack_compartment_ocid, ["stack-a", "stack-b"])
        self.assertTrue(args.scan_all_compartments)
        self.assertTrue(args.verify)
        self.assertEqual(args.scenario, "AWS to OCI")
        self.assertEqual(args.replication_bucket_name, "replication")
        self.assertTrue(args.json)

    def test_load_tenancy_from_config_selects_the_requested_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.write_text(
                "# comment\n"
                "[DEFAULT]\n"
                "tenancy = default-tenancy\n"
                "\n"
                "[SESSION]\n"
                "region = us-ashburn-1\n"
                "tenancy = session-tenancy\n",
                encoding="utf-8",
            )

            self.assertEqual(
                DETECTOR._load_tenancy_from_config(str(config), "SESSION"),
                "session-tenancy",
            )
            with self.assertRaisesRegex(RuntimeError, "Could not find tenancy"):
                DETECTOR._load_tenancy_from_config(str(config), "MISSING")

    def test_oci_reports_cli_failures_without_losing_the_cli_diagnostic(self):
        failure = subprocess.CalledProcessError(
            1,
            ["oci"],
            output="",
            stderr="ServiceError: NotAuthorizedOrNotFound",
        )
        with mock.patch.object(DETECTOR.subprocess, "run", side_effect=failure):
            with self.assertRaisesRegex(
                RuntimeError,
                "ServiceError: NotAuthorizedOrNotFound",
            ) as raised:
                DETECTOR._oci(
                    DETECTOR.OciCliContext("SESSION", "/config"),
                    ["iam", "compartment", "list"],
                )

        self.assertIn("oci --profile SESSION --config-file /config", str(raised.exception))

    def test_oci_read_helpers_build_the_expected_commands(self):
        context = DETECTOR.OciCliContext("SESSION", "/config")

        def fake_oci(_context, args, **_kwargs):
            return "namespace" if args == ["os", "ns", "get"] else []

        with mock.patch.object(DETECTOR, "_oci", side_effect=fake_oci) as oci:
            DETECTOR._discover_compartments(context, "tenancy")
            DETECTOR._list_stacks(context, "stack-compartment")
            DETECTOR._list_jobs(context, "stack")
            DETECTOR._get_stack(context, "stack")
            DETECTOR._preflight_root(context, "tenancy", "tenancy")
            DETECTOR._preflight_root(context, "tenancy", "root")
            DETECTOR._list_tag_namespaces(context, "tenancy")
            DETECTOR._list_tags(context, "namespace")
            DETECTOR._list_child_compartments(context, "root")
            DETECTOR._list_dynamic_groups(context, "tenancy")
            DETECTOR._list_policies(context, "root")
            DETECTOR._list_vaults(context, "secrets")
            DETECTOR._list_keys(context, "secrets", "https://kms.example")
            self.assertEqual(DETECTOR._get_object_storage_namespace(context), "namespace")
            DETECTOR._get_bucket(context, "namespace", "replication")
            DETECTOR._list_buckets(context, "namespace", "migration")

        self.assertEqual(oci.call_count, 16)
        self.assertEqual(
            oci.call_args_list[0],
            mock.call(
                context,
                [
                    "iam",
                    "compartment",
                    "list",
                    "--compartment-id",
                    "tenancy",
                    "--compartment-id-in-subtree",
                    "true",
                    "--access-level",
                    "ACCESSIBLE",
                    "--lifecycle-state",
                    "ACTIVE",
                    "--all",
                ],
                allow_empty=True,
            ),
        )
        self.assertIn(
            mock.call(
                context,
                [
                    "kms",
                    "management",
                    "key",
                    "list",
                    "--endpoint",
                    "https://kms.example",
                    "--compartment-id",
                    "secrets",
                    "--all",
                ],
                allow_empty=True,
            ),
            oci.call_args_list,
        )
        self.assertEqual(
            oci.call_args_list[-1],
            mock.call(
                context,
                [
                    "os",
                    "bucket",
                    "list",
                    "--namespace-name",
                    "namespace",
                    "--compartment-id",
                    "migration",
                    "--all",
                ],
                allow_empty=True,
            ),
        )

    def test_identity_evaluation_distinguishes_missing_unavailable_and_stale(self):
        missing = DETECTOR._evaluate_identity([], [], [])
        self.assertEqual(missing["status"], "red")
        self.assertEqual(
            missing["reason_codes"],
            ["tag_namespace_missing_or_inactive"],
        )

        namespace = [
            {"id": "namespace", "name": "CloudMigrations", "lifecycle-state": "ACTIVE"}
        ]
        unavailable = DETECTOR._evaluate_identity(namespace, None, ["2.4"])
        self.assertEqual(unavailable["status"], "unavailable")

        partial = DETECTOR._evaluate_identity(
            namespace,
            [{"name": "ServiceUse", "lifecycle-state": "ACTIVE"}],
            ["2.4"],
        )
        self.assertEqual(partial["status"], "yellow")
        self.assertEqual(partial["reason_codes"], ["partial_tag_contract"])

        incompatible = DETECTOR._evaluate_identity(
            namespace,
            [
                {"name": name, "lifecycle-state": "ACTIVE"}
                for name in DETECTOR.REQUIRED_TAGS
            ],
            ["2.4", "2.5"],
        )
        self.assertEqual(incompatible["status"], "yellow")
        self.assertEqual(
            incompatible["reason_codes"],
            ["version_not_proven_compatible"],
        )

    def test_compartment_evaluation_covers_green_red_and_partial_contracts(self):
        def compartment(name, state="ACTIVE", level="compartment"):
            return {
                "id": name.lower(),
                "name": name,
                "lifecycle-state": state,
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteResourceLevel": level}
                },
            }

        green, ids = DETECTOR._evaluate_compartments(
            [compartment("Migration"), compartment("MigrationSecrets")]
        )
        self.assertEqual(green["status"], "green")
        self.assertEqual(ids, {"Migration": "migration", "MigrationSecrets": "migrationsecrets"})

        red, _ = DETECTOR._evaluate_compartments([])
        self.assertEqual(red["status"], "red")

        partial, _ = DETECTOR._evaluate_compartments(
            [compartment("Migration"), compartment("MigrationSecrets", level=None)]
        )
        self.assertEqual(partial["status"], "yellow")

    def test_encryption_evaluation_covers_every_status(self):
        missing = DETECTOR._evaluate_encryption([], [])
        self.assertEqual(missing["status"], "red")

        vault = {
            "id": "vault",
            "display-name": "ocm-secrets",
            "lifecycle-state": "ACTIVE",
        }
        unavailable = DETECTOR._evaluate_encryption([vault], None)
        self.assertEqual(unavailable["status"], "unavailable")

        disabled = DETECTOR._evaluate_encryption(
            [vault],
            [{"id": "key", "display-name": "ocm-key", "lifecycle-state": "DISABLED"}],
        )
        self.assertEqual(disabled["status"], "yellow")

        enabled = DETECTOR._evaluate_encryption(
            [vault],
            [{"id": "key", "display-name": "ocm-key", "lifecycle-state": "ENABLED"}],
        )
        self.assertEqual(enabled["status"], "green")

    def test_storage_evaluation_covers_every_status(self):
        cases = [
            ("VMware to OLVM", None, None, "not_required"),
            ("AWS to OCI", None, None, "unavailable"),
            ("AWS to OCI", "replication", None, "red"),
            (
                "AWS to OCI",
                "replication",
                {"name": "replication", "compartment-id": "other"},
                "yellow",
            ),
            (
                "AWS to OCI",
                "replication",
                {"name": "replication", "compartment-id": "migration"},
                "green",
            ),
        ]
        for scenario, bucket_name, bucket, expected in cases:
            with self.subTest(expected=expected):
                result = DETECTOR._evaluate_storage(
                    scenario,
                    bucket_name,
                    bucket,
                    "migration",
                )
                self.assertEqual(result["status"], expected)

    def test_overall_evaluation_reports_ready_and_partial(self):
        green_bars = [
            DETECTOR._bar(number, f"Bar {number}", "green", [], {}, "None.")
            for number in range(1, 6)
        ]
        ready = DETECTOR._evaluate_overall("AWS to OCI", green_bars)
        self.assertEqual(ready["status"], "green")
        self.assertEqual(ready["evidence"]["decision"], "ready")

        green_bars[2] = DETECTOR._bar(3, "Authorization", "yellow", [], {}, "Fix it.")
        partial = DETECTOR._evaluate_overall("AWS to OCI", green_bars)
        self.assertEqual(partial["status"], "yellow")
        self.assertEqual(partial["evidence"]["decision"], "not_ready")

    def test_full_green_verification_is_ready_for_every_supported_scenario(self):
        namespace = {
            "id": "namespace",
            "name": "CloudMigrations",
            "lifecycle-state": "ACTIVE",
        }
        tags = [
            {"name": name, "lifecycle-state": "ACTIVE"}
            for name in DETECTOR.REQUIRED_TAGS
        ]
        children = [
            {
                "id": "migration",
                "name": "Migration",
                "lifecycle-state": "ACTIVE",
                "defined-tags": {
                    "CloudMigrations": {
                        "PrerequisiteResourceLevel": "compartment",
                        "PrerequisiteVersion": "2.4",
                    }
                },
            },
            {
                "id": "secrets",
                "name": "MigrationSecrets",
                "lifecycle-state": "ACTIVE",
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteResourceLevel": "compartment"}
                },
            },
        ]
        green_authorization = DETECTOR._bar(
            3,
            "Service Authorization",
            "green",
            ["authorization_contract_satisfied"],
            {},
            "None.",
        )
        vault = {
            "id": "vault",
            "display-name": "ocm-secrets",
            "lifecycle-state": "ACTIVE",
            "management-endpoint": "https://kms.example",
        }
        key = {"id": "key", "display-name": "ocm-key", "lifecycle-state": "ENABLED"}
        bucket = {"name": "replication", "compartment-id": "migration"}

        for scenario in DETECTOR.SUPPORTED_SCENARIOS:
            with self.subTest(scenario=scenario):
                with (
                    mock.patch.object(DETECTOR, "_preflight_root"),
                    mock.patch.object(DETECTOR, "_list_tag_namespaces", return_value=[namespace]),
                    mock.patch.object(DETECTOR, "_list_tags", return_value=tags),
                    mock.patch.object(DETECTOR, "_list_child_compartments", return_value=children),
                    mock.patch.object(DETECTOR, "_list_dynamic_groups", return_value=[]),
                    mock.patch.object(DETECTOR, "_list_policies", return_value=[]),
                    mock.patch.object(
                        DETECTOR,
                        "_evaluate_authorization",
                        return_value=green_authorization,
                    ),
                    mock.patch.object(DETECTOR, "_list_vaults", return_value=[vault]),
                    mock.patch.object(DETECTOR, "_list_keys", return_value=[key]),
                    mock.patch.object(
                        DETECTOR,
                        "_get_object_storage_namespace",
                        return_value="namespace",
                    ),
                    mock.patch.object(DETECTOR, "_list_buckets", return_value=[bucket]),
                    mock.patch.object(DETECTOR, "_get_bucket") as get_bucket,
                ):
                    result = DETECTOR._verify_prerequisites(
                        DETECTOR.OciCliContext("SESSION", "/config"),
                        "tenancy",
                        "root",
                        scenario,
                        {
                            "observed_prereq_versions": [],
                            "replication_bucket_name": "replication",
                        },
                    )

                self.assertEqual(result["decision"], "ready")
                self.assertTrue(result["authoritative"])
                self.assertEqual(result["bars"][-1]["status"], "green")
                self.assertEqual(
                    result["bars"][0]["evidence"]["observed_prereq_versions"],
                    ["2.4"],
                )
                get_bucket.assert_not_called()

    def test_verification_preserves_unavailable_read_failures(self):
        namespace = {
            "id": "namespace",
            "name": "CloudMigrations",
            "lifecycle-state": "ACTIVE",
        }
        tags = [
            {"name": name, "lifecycle-state": "ACTIVE"}
            for name in DETECTOR.REQUIRED_TAGS
        ]
        children = [
            {
                "id": name.lower(),
                "name": name,
                "lifecycle-state": "ACTIVE",
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteResourceLevel": "compartment"}
                },
            }
            for name in ("Migration", "MigrationSecrets")
        ]
        with (
            mock.patch.object(DETECTOR, "_preflight_root"),
            mock.patch.object(DETECTOR, "_list_tag_namespaces", return_value=[namespace]),
            mock.patch.object(DETECTOR, "_list_tags", return_value=tags),
            mock.patch.object(DETECTOR, "_list_child_compartments", return_value=children),
            mock.patch.object(
                DETECTOR,
                "_list_dynamic_groups",
                side_effect=RuntimeError("IAM denied"),
            ),
            mock.patch.object(
                DETECTOR,
                "_list_vaults",
                side_effect=RuntimeError("KMS denied"),
            ),
            mock.patch.object(
                DETECTOR,
                "_get_object_storage_namespace",
                side_effect=RuntimeError("Object Storage denied"),
            ),
        ):
            result = DETECTOR._verify_prerequisites(
                DETECTOR.OciCliContext("SESSION", "/config"),
                "tenancy",
                "root",
                "AWS to OCI",
                {
                    "observed_prereq_versions": ["2.4"],
                    "replication_bucket_name": "replication",
                },
            )

        statuses = {bar["bar"]: bar["status"] for bar in result["bars"]}
        self.assertEqual(statuses[1], "green")
        self.assertEqual(statuses[2], "green")
        self.assertEqual(statuses[3], "unavailable")
        self.assertEqual(statuses[4], "unavailable")
        self.assertEqual(statuses[5], "unavailable")
        self.assertEqual(result["decision"], "unknown")
        self.assertFalse(result["authoritative"])

    def test_authorization_rejects_missing_scenario_required_dynamic_groups(self):
        result = DETECTOR._evaluate_authorization(
            "VMware to OCI",
            [],
            [],
            [],
            "migration",
            "secrets",
        )

        self.assertEqual(result["status"], "red")
        self.assertEqual(
            result["reason_codes"],
            ["required_dynamic_groups_missing_or_invalid"],
        )
        self.assertEqual(
            set(result["evidence"]["dynamic_group_failures"]),
            {"migration", "discovery", "remote_agent", "hydration_agent"},
        )

    def test_verification_blocks_dependents_when_identity_and_compartments_are_unreadable(self):
        with (
            mock.patch.object(DETECTOR, "_preflight_root"),
            mock.patch.object(
                DETECTOR,
                "_list_tag_namespaces",
                side_effect=RuntimeError("IAM tags denied"),
            ),
            mock.patch.object(
                DETECTOR,
                "_list_child_compartments",
                side_effect=RuntimeError("compartments denied"),
            ),
        ):
            result = DETECTOR._verify_prerequisites(
                DETECTOR.OciCliContext("SESSION", "/config"),
                "tenancy",
                "root",
                "AWS to OCI",
                None,
            )

        statuses = {bar["bar"]: bar["status"] for bar in result["bars"]}
        self.assertEqual(statuses[1], "unavailable")
        self.assertEqual(statuses[2], "unavailable")
        self.assertEqual(statuses[3], "blocked")
        self.assertEqual(statuses[4], "blocked")
        self.assertEqual(statuses[5], "blocked")
        self.assertEqual(result["decision"], "not_ready")

    def test_verification_uses_bucket_get_only_as_a_read_fallback(self):
        namespace = {
            "id": "namespace",
            "name": "CloudMigrations",
            "lifecycle-state": "ACTIVE",
        }
        tags = [
            {"name": name, "lifecycle-state": "ACTIVE"}
            for name in DETECTOR.REQUIRED_TAGS
        ]
        children = [
            {
                "id": name.lower(),
                "name": name,
                "lifecycle-state": "ACTIVE",
                "defined-tags": {
                    "CloudMigrations": {"PrerequisiteResourceLevel": "compartment"}
                },
            }
            for name in ("Migration", "MigrationSecrets")
        ]
        green_authorization = DETECTOR._bar(
            3,
            "Service Authorization",
            "green",
            ["authorization_contract_satisfied"],
            {},
            "None.",
        )
        vault = {
            "id": "vault",
            "display-name": "ocm-secrets",
            "lifecycle-state": "ACTIVE",
            "management-endpoint": "https://kms.example",
        }
        key = {"id": "key", "display-name": "ocm-key", "lifecycle-state": "ENABLED"}

        for get_result, expected_status in (
            ({"name": "replication", "compartment-id": "other"}, "yellow"),
            (RuntimeError("not found"), "red"),
        ):
            with self.subTest(expected_status=expected_status):
                with (
                    mock.patch.object(DETECTOR, "_preflight_root"),
                    mock.patch.object(DETECTOR, "_list_tag_namespaces", return_value=[namespace]),
                    mock.patch.object(DETECTOR, "_list_tags", return_value=tags),
                    mock.patch.object(DETECTOR, "_list_child_compartments", return_value=children),
                    mock.patch.object(DETECTOR, "_list_dynamic_groups", return_value=[]),
                    mock.patch.object(DETECTOR, "_list_policies", return_value=[]),
                    mock.patch.object(
                        DETECTOR,
                        "_evaluate_authorization",
                        return_value=green_authorization,
                    ),
                    mock.patch.object(DETECTOR, "_list_vaults", return_value=[vault]),
                    mock.patch.object(DETECTOR, "_list_keys", return_value=[key]),
                    mock.patch.object(
                        DETECTOR,
                        "_get_object_storage_namespace",
                        return_value="namespace",
                    ),
                    mock.patch.object(DETECTOR, "_list_buckets", return_value=[]),
                    mock.patch.object(
                        DETECTOR,
                        "_get_bucket",
                        side_effect=get_result if isinstance(get_result, Exception) else None,
                        return_value=None if isinstance(get_result, Exception) else get_result,
                    ) as get_bucket,
                ):
                    result = DETECTOR._verify_prerequisites(
                        DETECTOR.OciCliContext("SESSION", "/config"),
                        "tenancy",
                        "root",
                        "AWS to OCI",
                        {
                            "observed_prereq_versions": ["2.4"],
                            "replication_bucket_name": "replication",
                        },
                    )

                self.assertEqual(result["bars"][4]["status"], expected_status)
                get_bucket.assert_called_once_with(
                    mock.ANY,
                    "namespace",
                    "replication",
                )

    def test_main_can_discover_artifact_roots_from_a_profile_and_render_human_output(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.write_text(
                "[SESSION]\ntenancy = tenancy\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                profile="SESSION",
                config_file=str(config),
                auth=None,
                region=None,
                cert_bundle=None,
                oci_timeout_seconds=30,
                tenancy_ocid=None,
                root_compartment_ocid=None,
                stack_compartment_ocid=[],
                scan_all_compartments=False,
                verify=False,
                scenario=None,
                replication_bucket_name=None,
                json=False,
            )
            compartments = [
                {"id": "root", "name": "Root", "compartment-id": "tenancy"},
                {
                    "id": "migration",
                    "name": "Migration",
                    "compartment-id": "root",
                    "defined-tags": {
                        "CloudMigrations": {"PrerequisiteVersion": "2.4"}
                    },
                },
                {
                    "id": "secrets",
                    "name": "MigrationSecrets",
                    "compartment-id": "root",
                },
            ]
            with (
                mock.patch.object(DETECTOR, "_parse_args", return_value=args),
                mock.patch.object(DETECTOR, "_discover_compartments", return_value=compartments),
                mock.patch.object(DETECTOR, "_list_stacks", return_value=[]),
                mock.patch.object(DETECTOR, "_print_human") as print_human,
            ):
                self.assertEqual(DETECTOR.main(), 0)

        rendered = print_human.call_args.args[0]
        self.assertEqual(rendered["tenancy_ocid"], "tenancy")
        self.assertEqual(rendered["coverage_scope"], "artifact_roots_only")
        self.assertEqual(rendered["scanned_compartment_ocids"], ["root"])
        self.assertEqual(
            rendered["artifact_roots"],
            [
                {
                    "root_compartment_id": "root",
                    "root_compartment_name": "Root",
                    "has_migration": True,
                    "has_migration_secrets": True,
                    "observed_prereq_versions": ["2.4"],
                }
            ],
        )

    def test_human_output_reports_candidates_warnings_and_verification(self):
        result = {
            "tenancy_ocid": "tenancy",
            "candidate_count": 1,
            "coverage_scope": "selected_root_only",
            "coverage_complete": False,
            "warnings": ["partial scan"],
            "primary": {
                "display_name": "OCM Prerequisites",
                "stack_id": "stack",
                "prereq_version": None,
                "prereq_version_conflict": True,
                "observed_prereq_versions": ["2.3", "2.4"],
                "variable_model": "v2.3+",
                "scenario": "AWS to OCI",
                "score": 3,
                "stack_compartment_name": "Root",
                "stack_compartment_id": "root",
                "configured_root_compartment_ocid": "root",
                "latest_apply_succeeded_at": "2026-01-01T00:00:00+00:00",
                "latest_destroy_succeeded_at": None,
                "latest_job_operation": "APPLY",
                "latest_job_state": "SUCCEEDED",
                "latest_job_id": "job",
                "latest_job_at": "2026-01-01T00:00:00+00:00",
                "reasons": ["has APPLY SUCCEEDED"],
            },
            "candidates": [
                {
                    "display_name": "OCM Prerequisites",
                    "score": 3,
                    "latest_apply_succeeded_at": "2026-01-01T00:00:00+00:00",
                    "latest_destroy_succeeded_at": None,
                    "stack_id": "stack",
                }
            ],
            "verification": {
                "decision": "ready",
                "authoritative": True,
                "bars": [
                    DETECTOR._bar(
                        1,
                        "Identity Foundation",
                        "green",
                        ["identity_contract_satisfied"],
                        {},
                        "None.",
                    )
                ],
            },
        }

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            DETECTOR._print_human(result)
        rendered = stdout.getvalue()
        self.assertIn("Warning: partial scan", rendered)
        self.assertIn("Primary prerequisite stack", rendered)
        self.assertIn("observed_prereq_versions: 2.3, 2.4", rendered)
        self.assertIn("latest_job_id: job", rendered)
        self.assertIn("All candidates:", rendered)
        self.assertIn("Readiness: ready (authoritative=True)", rendered)
        self.assertIn("Bar 1: Identity Foundation | green", rendered)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            DETECTOR._print_human({**result, "candidate_count": 0, "primary": None, "candidates": []})
        self.assertIn("No primary prerequisite stack candidate found.", stdout.getvalue())

    def test_main_verify_adds_the_deterministic_verification_to_json(self):
        args = argparse.Namespace(
            profile="SESSION",
            config_file="/config",
            auth="security_token",
            region="us-ashburn-1",
            cert_bundle=None,
            oci_timeout_seconds=30,
            tenancy_ocid="tenancy",
            root_compartment_ocid="root",
            stack_compartment_ocid=[],
            scan_all_compartments=False,
            verify=True,
            scenario="AWS to OCI",
            replication_bucket_name="replication",
            json=True,
        )
        verification = {"decision": "ready", "authoritative": True, "bars": []}
        with (
            mock.patch.object(DETECTOR, "_parse_args", return_value=args),
            mock.patch.object(DETECTOR, "_list_stacks", return_value=[]),
            mock.patch.object(
                DETECTOR,
                "_verify_prerequisites",
                return_value=verification,
            ) as verify,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(DETECTOR.main(), 0)

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["verification"], verification)
        verify.assert_called_once_with(
            DETECTOR.OciCliContext(
                "SESSION",
                "/config",
                auth="security_token",
                region="us-ashburn-1",
                timeout_seconds=30,
            ),
            "tenancy",
            "root",
            "AWS to OCI",
            None,
            "replication",
        )

    def test_main_rejects_invalid_verification_arguments_before_oci_reads(self):
        base = {
            "profile": "SESSION",
            "config_file": "/config",
            "auth": "security_token",
            "region": None,
            "cert_bundle": None,
            "oci_timeout_seconds": 30,
            "tenancy_ocid": "tenancy",
            "root_compartment_ocid": "root",
            "stack_compartment_ocid": [],
            "scan_all_compartments": False,
            "verify": True,
            "scenario": "AWS to OCI",
            "replication_bucket_name": None,
            "json": True,
        }
        invalid = [
            ({**base, "oci_timeout_seconds": 0}, "at least 1"),
            ({**base, "root_compartment_ocid": None}, "requires --root-compartment-ocid"),
            ({**base, "scenario": None}, "requires --scenario"),
        ]
        for values, message in invalid:
            with self.subTest(message=message):
                with mock.patch.object(
                    DETECTOR,
                    "_parse_args",
                    return_value=argparse.Namespace(**values),
                ):
                    with self.assertRaisesRegex(RuntimeError, message):
                        DETECTOR.main()

    def test_cli_help_and_validation_errors_are_safe_without_oci_access(self):
        help_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--root-compartment-ocid", help_result.stdout)
        self.assertIn("--stack-compartment-ocid", help_result.stdout)
        self.assertIn("--verify", help_result.stdout)
        self.assertIn("--scenario", help_result.stdout)

        invalid_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--tenancy-ocid",
                "tenancy",
                "--oci-timeout-seconds",
                "0",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(invalid_result.returncode, 2)
        self.assertIn("--oci-timeout-seconds must be at least 1", invalid_result.stderr)


if __name__ == "__main__":
    unittest.main()
