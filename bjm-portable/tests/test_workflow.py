import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workflow.py"
SPEC = importlib.util.spec_from_file_location("bjm_workflow", SCRIPT)
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


def task_state():
    return {
        "versions": {"manuscript": "rev-1", "export": "rev-1", "test_suite": "rev-1"},
        "checks": [
            {"id": "fidelity", "kind": "review", "depends_on": ["manuscript", "export"]},
            {"id": "export_test", "kind": "test", "depends_on": ["export", "test_suite"]},
        ],
        "evidence": {
            "fidelity": {
                "result": "PASS",
                "versions": {"manuscript": "rev-1", "export": "rev-1"},
                "reference": "Comparison of source chapter and exported chapter",
                "context_isolation": "shared",
            },
            "export_test": {
                "result": "PASS",
                "versions": {"export": "rev-1", "test_suite": "rev-1"},
                "reference": "test-output.txt",
                "exit_code": 0,
                "executed": 2,
            },
        },
    }


class RoutingTests(unittest.TestCase):
    def test_same_creative_material_different_requested_actions(self):
        conversion = workflow.route("format", "creative")
        revision = workflow.route("revise", "creative")
        self.assertEqual((conversion["route"], revision["route"]), ("format", "revise"))
        self.assertNotIn("test-driven-development", conversion["modules"])
        self.assertNotIn("incremental-implementation", conversion["modules"])

    def test_complexity_does_not_turn_explanation_into_repair(self):
        diagnosis = workflow.route("explain", "software", complex=True)
        self.assertEqual(diagnosis["route"], "explain")
        self.assertNotIn("incremental-implementation", diagnosis["modules"])

    def test_complex_repair_selects_an_engineering_method(self):
        repair = workflow.route("repair", "software", complex=True)
        self.assertEqual(repair["route"], "repair")
        self.assertTrue(
            {
                "debugging-and-error-recovery",
                "test-driven-development",
                "incremental-implementation",
            }.intersection(repair["modules"]),
            repair,
        )

    def test_unrecognized_route_rejected(self):
        with self.assertRaises(ValueError):
            workflow.route("everything", "software")


class EvidenceTests(unittest.TestCase):
    def test_resume_invalidates_only_checks_using_changed_input(self):
        state = task_state()
        state["revision_count"] = 2
        self.assertEqual(workflow.evaluate(state)["status"], "READY")
        state["versions"]["manuscript"] = "rev-2"
        saved = copy.deepcopy(state)
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "RECHECK")
        self.assertEqual(result["checks"], {"fidelity": "STALE", "export_test": "PASS"})
        self.assertEqual(result["recheck"], ["fidelity"])
        self.assertEqual(result["revision_count"], 2)
        self.assertEqual(state, saved)

        state["evidence"]["fidelity"]["versions"]["manuscript"] = "rev-2"
        self.assertEqual(workflow.evaluate(state)["status"], "READY")

    def test_exit_zero_with_no_executed_tests_is_not_pass(self):
        state = task_state()
        state["evidence"]["export_test"]["executed"] = 0
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "RECHECK")
        self.assertEqual(result["checks"]["export_test"], "UNTESTED")

    def test_nonzero_test_exit_does_not_accept_a_passing_label(self):
        state = task_state()
        state["evidence"]["export_test"]["exit_code"] = 1
        result = workflow.evaluate(state)
        self.assertNotEqual(result["status"], "READY")
        self.assertNotEqual(result["checks"]["export_test"], "PASS")

    def test_missing_evidence_version_does_not_clear_required_check(self):
        state = task_state()
        del state["evidence"]["fidelity"]["versions"]["manuscript"]
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "RECHECK")
        self.assertNotEqual(result["checks"]["fidelity"], "PASS")

    def test_self_review_cannot_satisfy_isolated_review_requirement(self):
        state = task_state()
        state["checks"][0]["requires_isolation"] = True
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "RECHECK")
        self.assertEqual(result["checks"]["fidelity"], "UNTESTED")
        state["evidence"]["fidelity"]["context_isolation"] = "isolated"
        self.assertEqual(workflow.evaluate(state)["status"], "READY")

    def test_failing_required_check_stops_only_when_budget_is_exhausted(self):
        state = task_state()
        state["evidence"]["export_test"].update(result="FAIL", exit_code=1)
        state.update(revision_count=2, max_revisions=3)
        self.assertEqual(workflow.evaluate(state)["status"], "REVISE")
        state["revision_count"] = 3
        self.assertEqual(workflow.evaluate(state)["status"], "STOPPED")

        state["evidence"]["export_test"].update(result="PASS", exit_code=0)
        self.assertEqual(workflow.evaluate(state)["status"], "READY")

    def test_optional_failure_is_visible_without_blocking_required_checks(self):
        state = task_state()
        state["checks"][1]["required"] = False
        state["evidence"]["export_test"].update(result="FAIL", exit_code=1)
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["checks"]["export_test"], "FAIL")

    def test_not_applicable_has_a_versioned_explanation(self):
        state = task_state()
        state["checks"][1]["allow_not_applicable"] = True
        state["evidence"]["export_test"] = {
            "result": "NOT_APPLICABLE",
            "versions": {"export": "rev-1", "test_suite": "rev-1"},
            "reference": "Review notes for the formatting-only output",
            "reason": "The deliverable is plain text and has no executable entry point.",
        }
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["checks"]["export_test"], "NOT_APPLICABLE")

    def test_not_applicable_without_reason_does_not_clear_check(self):
        state = task_state()
        state["checks"][1]["allow_not_applicable"] = True
        state["evidence"]["export_test"] = {
            "result": "NOT_APPLICABLE",
            "versions": {"export": "rev-1", "test_suite": "rev-1"},
            "reference": "Review notes",
        }
        result = workflow.evaluate(state)
        self.assertNotEqual(result["status"], "READY")

    def test_not_applicable_cannot_override_a_required_check_on_its_own(self):
        state = task_state()
        state["evidence"]["export_test"] = {
            "result": "NOT_APPLICABLE",
            "versions": {"export": "rev-1", "test_suite": "rev-1"},
            "reference": "Review notes",
            "reason": "The check was declared inapplicable by the receipt.",
        }
        self.assertNotEqual(workflow.evaluate(state)["status"], "READY")

    def test_duplicate_check_id_is_invalid(self):
        state = task_state()
        state["checks"].append(copy.deepcopy(state["checks"][0]))
        with self.assertRaises(ValueError):
            workflow.evaluate(state)

    def test_required_checks_are_not_optional_by_omission(self):
        state = task_state()
        for check in state["checks"]:
            check["required"] = False
        with self.assertRaises(ValueError):
            workflow.evaluate(state)

    def test_a_check_requires_version_dependencies(self):
        state = task_state()
        state["checks"][1]["depends_on"] = []
        with self.assertRaises(ValueError):
            workflow.evaluate(state)


class DecisionTests(unittest.TestCase):
    def test_ready_artifact_does_not_authorize_external_action(self):
        state = task_state()
        state["external_action"] = {
            "action": "publish",
            "target": "production",
            "artifact_ref": "export",
            "artifact_version": "rev-1",
        }
        self.assertEqual(workflow.evaluate(state)["status"], "BLOCKED")
        state["external_action"]["authorized"] = True
        self.assertEqual(workflow.evaluate(state)["status"], "BLOCKED")

    def test_approval_must_match_action_target_and_artifact_version(self):
        state = task_state()
        state["external_action"] = {
            "action": "publish",
            "target": "production",
            "artifact_ref": "export",
            "artifact_version": "rev-1",
            "approval": {
                "action": "publish",
                "target": "production",
                "artifact_version": "rev-1",
                "reference": "User approval for the export revision",
            },
        }
        self.assertEqual(workflow.evaluate(state)["status"], "READY")
        for field, replacement in [
            ("action", "send"),
            ("target", "staging"),
            ("artifact_version", "rev-2"),
        ]:
            changed = copy.deepcopy(state)
            changed["external_action"][field] = replacement
            with self.subTest(field=field):
                self.assertEqual(workflow.evaluate(changed)["status"], "BLOCKED")

    def test_matching_old_approval_cannot_publish_after_export_changes(self):
        state = task_state()
        state["external_action"] = {
            "action": "publish",
            "target": "production",
            "artifact_ref": "export",
            "artifact_version": "rev-1",
            "approval": {
                "action": "publish",
                "target": "production",
                "artifact_version": "rev-1",
                "reference": "User approval for export rev-1 only",
            },
        }
        state["versions"]["export"] = "rev-2"
        for receipt in state["evidence"].values():
            receipt["versions"]["export"] = "rev-2"
        result = workflow.evaluate(state)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(all(value == "PASS" for value in result["checks"].values()))

    def test_stop_takes_precedence_over_recheck(self):
        state = task_state()
        state["versions"]["manuscript"] = "rev-2"
        state["stop_reason"] = "The user stopped the task."
        self.assertEqual(workflow.evaluate(state)["status"], "STOPPED")

    def test_missing_required_input_blocks_before_repair(self):
        state = task_state()
        state["evidence"]["export_test"].update(result="FAIL", exit_code=1)
        state["blocked_reason"] = "The canonical source could not be retrieved."
        self.assertEqual(workflow.evaluate(state)["status"], "BLOCKED")


class CommandLineTests(unittest.TestCase):
    def invoke(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_evaluate_accepts_json_and_emits_json(self):
        state = task_state()
        state["versions"]["manuscript"] = "rev-2"
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder, "checkpoint.json")
            checkpoint.write_text(json.dumps(state), encoding="utf-8")
            process = self.invoke("evaluate", str(checkpoint))
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "RECHECK")
        self.assertEqual(result["recheck"], ["fidelity"])

    def test_fingerprint_uses_exact_file_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder, "chapter one.txt")
            second = Path(folder, "chapter two.txt")
            first.write_bytes("甲\n".encode("utf-8"))
            second.write_bytes("甲\r\n".encode("utf-8"))
            process = self.invoke("fingerprint", str(first), str(second))
            expected = {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (first, second)
            }
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result, expected)

    def test_evaluate_rejects_invalid_shape_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder, "checkpoint.json")
            missing = self.invoke("evaluate", str(checkpoint))
            checkpoint.write_text("[]", encoding="utf-8")
            invalid = self.invoke("evaluate", str(checkpoint))
        for process in (missing, invalid):
            self.assertEqual(process.returncode, 2)
            self.assertEqual(process.stdout, "")
            self.assertIn("workflow:", process.stderr)

    def test_evaluate_blocks_when_required_source_version_is_missing(self):
        state = task_state()
        del state["versions"]["manuscript"]
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder, "checkpoint.json")
            checkpoint.write_text(json.dumps(state), encoding="utf-8")
            process = self.invoke("evaluate", str(checkpoint))
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("manuscript", result["reason"])
        self.assertEqual(result["checks"]["export_test"], "PASS")

    def test_file_change_and_saved_checkpoint_only_invalidate_dependent_review(self):
        state = task_state()
        with tempfile.TemporaryDirectory() as folder:
            inputs = {
                ref: str(Path(folder, ref + ".txt")) for ref in state["versions"]
            }
            for ref, path in inputs.items():
                Path(path).write_text(ref + " version one", encoding="utf-8")

            def file_versions():
                result = self.invoke("fingerprint", *inputs.values())
                self.assertEqual(result.returncode, 0, result.stderr)
                digest_by_path = json.loads(result.stdout)
                return {ref: digest_by_path[path] for ref, path in inputs.items()}

            state["versions"] = file_versions()
            for check in state["checks"]:
                state["evidence"][check["id"]]["versions"] = {
                    ref: state["versions"][ref] for ref in check["depends_on"]
                }
            state["revision_count"] = 2
            checkpoint = Path(folder, "checkpoint.json")
            checkpoint.write_text(json.dumps(state), encoding="utf-8")
            initial = self.invoke("evaluate", str(checkpoint))
            self.assertEqual(initial.returncode, 0, initial.stderr)
            self.assertEqual(json.loads(initial.stdout)["status"], "READY")

            Path(inputs["manuscript"]).write_text("manuscript version two", encoding="utf-8")
            restored = json.loads(checkpoint.read_text(encoding="utf-8"))
            restored["versions"] = file_versions()
            checkpoint.write_text(json.dumps(restored), encoding="utf-8")
            resumed = self.invoke("evaluate", str(checkpoint))

        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        result = json.loads(resumed.stdout)
        self.assertEqual(result["status"], "RECHECK")
        self.assertEqual(result["recheck"], ["fidelity"])
        self.assertEqual(result["checks"]["export_test"], "PASS")
        self.assertEqual(result["revision_count"], 2)


if __name__ == "__main__":
    unittest.main()
