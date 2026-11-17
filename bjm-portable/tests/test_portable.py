"""Regression checks for the portable, domain-independent router."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workflow.py"
SPEC = importlib.util.spec_from_file_location("bjm_portable_workflow", SCRIPT)
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)

BUILT_IN_DOMAINS = (
    "software",
    "creative",
    "research",
    "documents",
    "data",
    "operations",
    "general",
)


class PortableRoutingTests(unittest.TestCase):
    def test_format_preserves_content_in_every_domain(self):
        for domain in (*BUILT_IN_DOMAINS, "event-logistics"):
            with self.subTest(domain=domain):
                result = workflow.route("format", domain)
                self.assertEqual(result["domain"], domain)
                self.assertEqual(result["route"], "format")
                self.assertEqual(result["method"], "preserve-content")
                self.assertEqual(
                    set(result["checks"]), {"content-preserved", "format-matches-request"}
                )
                self.assertEqual(result["modules"], [])

    def test_same_document_has_distinct_format_and_revise_methods(self):
        formatted = workflow.route("format", "documents")
        revised = workflow.route("revise", "documents")
        self.assertEqual(formatted["route"], "format")
        self.assertEqual(revised["route"], "revise")
        self.assertNotEqual(formatted["method"], revised["method"])
        self.assertNotEqual(set(formatted["checks"]), set(revised["checks"]))

    def test_complexity_does_not_turn_an_explanation_into_a_repair(self):
        for domain, expected_method in (
            ("software", "diagnose"),
            ("general", "explain-with-evidence"),
            ("operations", "explain-with-evidence"),
        ):
            with self.subTest(domain=domain):
                result = workflow.route("explain", domain, complex=True)
                self.assertEqual(result["route"], "explain")
                self.assertEqual(result["method"], expected_method)
                self.assertNotIn("incremental-implementation", result["modules"])
                self.assertNotIn("test-driven-development", result["modules"])

    def test_structured_depth_preserves_the_requested_intent(self):
        simple = workflow.route("revise", "data")
        structured = workflow.route("revise", "data", complex=True)
        self.assertEqual(simple["depth"], "quick")
        self.assertEqual(structured["depth"], "structured")
        self.assertEqual(simple["route"], structured["route"])
        self.assertEqual(simple["method"], structured["method"])

    def test_custom_domain_uses_the_general_profile(self):
        generic = workflow.route("revise", "general")
        custom = workflow.route("revise", "event-logistics")
        self.assertEqual(custom["domain"], "event-logistics")
        self.assertEqual(custom["method"], generic["method"])
        self.assertEqual(custom["checks"], generic["checks"])
        self.assertTrue(custom["checks"])
        self.assertEqual(custom["modules"], [])

    def test_nonsoftware_domains_have_no_engineering_dependencies(self):
        for domain in ("research", "documents", "data", "operations"):
            with self.subTest(domain=domain):
                result = workflow.route("create", domain, complex=True)
                self.assertEqual(result["route"], "create")
                self.assertEqual(result["depth"], "structured")
                self.assertEqual(result["modules"], [])
                self.assertIsInstance(result["checks"], list)
                self.assertTrue(result["checks"])
                self.assertTrue(all(isinstance(check, str) and check for check in result["checks"]))
                self.assertEqual(len(result["checks"]), len(set(result["checks"])))

    def test_specialized_profiles_extend_instead_of_replace_generic_checks(self):
        for intent, domain, criterion in (
            ("research", "research", "source-versions-recorded"),
            ("revise", "documents", "meaning-preserved"),
            ("create", "data", "calculations-reconciled"),
            ("publish", "operations", "execution-scope-verified"),
        ):
            with self.subTest(intent=intent, domain=domain):
                generic = workflow.route(intent, "general")
                specialized = workflow.route(intent, domain)
                self.assertLess(set(generic["checks"]), set(specialized["checks"]))
                self.assertIn(criterion, specialized["checks"])

    def test_malformed_custom_domains_are_rejected(self):
        for domain in ("", "../general", "data science"):
            with self.subTest(domain=domain):
                with self.assertRaises(ValueError):
                    workflow.route("revise", domain)

    def test_cli_routes_custom_domain_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "route",
                    "--intent", "revise", "--domain", "event-logistics", "--complex",
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        cli_route = json.loads(result.stdout)
        self.assertEqual(cli_route, workflow.route("revise", "event-logistics", complex=True))


if __name__ == "__main__":
    unittest.main()
