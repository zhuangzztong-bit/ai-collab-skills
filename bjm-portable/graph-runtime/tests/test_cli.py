from contextlib import closing, contextmanager
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
WORKFLOW = PACKAGE / "workflow.py"
TWO_CHAPTERS = PACKAGE / "examples" / "two_chapters.json"
SPEC = importlib.util.spec_from_file_location("bjm_graph_engine", PACKAGE / "engine.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


class WorkflowCLITest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.command = [
            sys.executable,
            str(WORKFLOW),
            "--db",
            str(self.workspace / "workflow.db"),
            "--run-id",
            "demo",
        ]

    def cli(self, *arguments, expected=0):
        result = subprocess.run(
            [*self.command, *arguments],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"{arguments!r}\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        if expected:
            self.assertTrue(result.stderr.strip())
            return result.stderr
        return json.loads(result.stdout)

    def write_graph(self, nodes):
        graph = self.workspace / "graph.json"
        graph.write_text(json.dumps({"version": "test-graph", "nodes": nodes}), encoding="utf-8")
        return str(graph)

    @contextmanager
    def running_process(self, node):
        process = subprocess.Popen(
            [*self.command, "run"], cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                self.assertIsNone(process.poll(), "runner exited before reaching its action")
                if self.cli("status")["nodes"][node]["status"] == "RUNNING":
                    break
                time.sleep(0.02)
            else:
                self.fail("runner did not persist RUNNING before the test deadline")
            yield
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)

    def test_timeout_retries_only_the_failed_branch_after_restart(self):
        self.cli("init", str(TWO_CHAPTERS))
        failed = self.cli("run", "--workers", "2", "--fail-before", "review-b")["nodes"]
        self.assertEqual(failed["review-a"]["status"], "SUCCEEDED")
        self.assertEqual(failed["review-b"]["status"], "FAILED")
        self.assertEqual(failed["review-b"]["attempt"], 1)
        self.assertEqual(failed["approve"]["status"], "PENDING")
        self.assertEqual(self.cli("status")["nodes"], failed)
        before = self.cli("events")

        self.cli("retry", "review-b")
        resumed = self.cli("run", "--workers", "2")["nodes"]
        for node in ("draft-a", "draft-b", "review-a"):
            with self.subTest(node=node):
                self.assertEqual(resumed[node], failed[node])
        self.assertEqual(resumed["review-b"]["status"], "SUCCEEDED")
        self.assertEqual(resumed["review-b"]["attempt"], 2)
        self.assertEqual(resumed["approve"]["status"], "AWAITING_APPROVAL")

        after = self.cli("events")
        self.assertTrue(before)
        self.assertEqual(after[: len(before)], before)
        self.assertGreater(len(after), len(before))
        ids = [event["id"] for event in after]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertTrue(any(event["node_id"] == "review-b" for event in after[len(before) :]))

    def test_revising_one_chapter_invalidates_its_review_and_old_approval(self):
        self.cli("init", str(TWO_CHAPTERS))
        initial = self.cli("run")["nodes"]
        self.assertEqual(initial["approve"]["status"], "AWAITING_APPROVAL")
        old_token = initial["approve"]["token"]
        self.assertTrue(old_token)
        accepted = self.cli("approve", "approve", "--", old_token)["nodes"]
        self.assertEqual(accepted["approve"]["status"], "SUCCEEDED")

        edited = self.cli("edit", "draft-a", json.dumps({"text": "Revised chapter A."}))["nodes"]
        for node in ("draft-a", "review-a", "approve"):
            with self.subTest(node=node):
                self.assertEqual(edited[node]["status"], "PENDING")
                self.assertGreater(edited[node]["revision"], accepted[node]["revision"])
        self.assertIsNone(edited["approve"]["token"])

        rerun = self.cli("run")["nodes"]
        for node in ("draft-b", "review-b"):
            with self.subTest(node=node):
                self.assertEqual(rerun[node], accepted[node])
        for node in ("draft-a", "review-a"):
            with self.subTest(node=node):
                self.assertEqual(rerun[node]["status"], "SUCCEEDED")
                self.assertEqual(rerun[node]["attempt"], accepted[node]["attempt"] + 1)
                self.assertNotEqual(rerun[node]["fingerprint"], accepted[node]["fingerprint"])

        self.assertEqual(rerun["approve"]["status"], "AWAITING_APPROVAL")
        new_token = rerun["approve"]["token"]
        self.assertTrue(new_token)
        self.assertNotEqual(new_token, old_token)
        stale = self.cli("approve", "approve", "--", old_token, expected=2)
        self.assertIn("stale or invalid approval token", stale)
        error = self.cli("approve", "approve", "--", "旧审批令牌", expected=2)
        self.assertNotIn("Traceback", error)
        self.assertEqual(self.cli("status")["nodes"]["approve"], rerun["approve"])
        final = self.cli("approve", "approve", "--", new_token)["nodes"]
        self.assertEqual(final["approve"]["status"], "SUCCEEDED")

    def test_approval_tokens_never_start_with_a_dash(self):
        coordinator = engine.Engine(self.workspace / "tokens.db")
        gate = {"id": "gate-0", "kind": "approval", "deps": [], "inputs": {}}
        coordinator.init("pinned", {"version": "token-test", "nodes": [gate]})
        generated = iter(["-first", "-second", "plain-token"])
        with patch.object(engine.secrets, "token_urlsafe", side_effect=lambda size: next(generated)):
            pinned = coordinator.run("pinned", handler=None)["nodes"]
        self.assertEqual(pinned["gate-0"]["token"], "plain-token")

        many = [{"id": f"gate-{index}", "kind": "approval", "deps": [], "inputs": {}} for index in range(640)]
        coordinator.init("many", {"version": "token-test", "nodes": many})
        tokens = [node["token"] for node in coordinator.run("many", handler=None)["nodes"].values()]
        self.assertEqual(len(tokens), 640)
        self.assertFalse([token for token in tokens if not token or token.startswith("-")])

    def test_a_dash_token_saved_by_an_older_version_is_approved_after_double_dash(self):
        self.cli("init", str(TWO_CHAPTERS))
        token = self.cli("run")["nodes"]["approve"]["token"]
        older = "-A" + token[2:]
        with closing(sqlite3.connect(self.workspace / "workflow.db")) as db, db:
            db.execute("UPDATE nodes SET token = ? WHERE run_id = ? AND id = ?", (older, "demo", "approve"))
        error = self.cli("approve", "approve", older, expected=2)
        self.assertIn("usage:", error)
        self.assertEqual(self.cli("status")["nodes"]["approve"]["status"], "AWAITING_APPROVAL")
        final = self.cli("approve", "approve", "--", older)["nodes"]
        self.assertEqual(final["approve"]["status"], "SUCCEEDED")

    def test_process_loss_requires_resolution_for_an_unsafe_action(self):
        graph = self.write_graph(
            [
                {
                    "id": "prepare",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Prepare the external action"},
                    "retry_safe": True,
                },
                {
                    "id": "action",
                    "kind": "task",
                    "deps": ["prepare"],
                    "inputs": {"text": "Simulated external action", "delay_seconds": 10},
                    "retry_safe": False,
                },
                {"id": "confirm", "kind": "approval", "deps": ["action"], "inputs": {}},
            ]
        )
        self.cli("init", graph)
        with self.running_process("action"):
            pass

        resumed = self.cli("run")["nodes"]
        self.assertEqual(resumed["action"]["status"], "UNCERTAIN")
        self.assertEqual(resumed["action"]["attempt"], 1)
        self.assertEqual(resumed["confirm"]["status"], "PENDING")
        self.cli("retry", "action", expected=2)
        self.assertEqual(self.cli("run")["nodes"], resumed)

        receipt = {"receipt": "externally-verified-42"}
        self.cli("resolve", "action", json.dumps(receipt))
        resolved = self.cli("run")["nodes"]
        self.assertEqual(resolved["action"]["status"], "SUCCEEDED")
        self.assertEqual(resolved["action"]["attempt"], 1)
        self.assertEqual(resolved["action"]["output"], receipt)
        self.assertEqual(resolved["confirm"]["status"], "AWAITING_APPROVAL")
        for node in ("prepare", "action"):
            with self.subTest(node=node):
                self.cli("edit", node, json.dumps({"text": "Would repeat the action"}), expected=2)
        self.assertEqual(self.cli("status")["nodes"], resolved)

    def test_process_loss_requeues_a_safe_action(self):
        graph = self.write_graph(
            [
                {
                    "id": "safe",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Safe simulated step", "delay_seconds": 2},
                    "retry_safe": True,
                },
            ]
        )
        self.cli("init", graph)
        with self.running_process("safe"):
            self.assertEqual(self.cli("status")["nodes"]["safe"]["attempt"], 1)

        resumed = self.cli("run")["nodes"]["safe"]
        self.assertEqual(resumed["status"], "SUCCEEDED")
        self.assertEqual(resumed["attempt"], 2)
        self.assertEqual(resumed["output"]["text"], "Safe simulated step")

    def test_active_runner_excludes_a_second_process(self):
        graph = self.write_graph(
            [
                {
                    "id": "active",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Only one process may start this step", "delay_seconds": 10},
                },
            ]
        )
        self.cli("init", graph)
        with self.running_process("active"):
            error = self.cli("run", expected=2)
            self.assertIn("another coordinator", error)
            active = self.cli("status")["nodes"]["active"]
            self.assertEqual(active["status"], "RUNNING")
            self.assertEqual(active["attempt"], 1)

    def test_rejects_a_cycle_before_initializing_the_run(self):
        graph = self.write_graph(
            [
                {"id": "a", "kind": "task", "deps": ["b"], "inputs": {}},
                {"id": "b", "kind": "task", "deps": ["a"], "inputs": {}},
            ]
        )
        self.cli("init", graph, expected=2)
        self.cli("status", expected=2)
        self.assertEqual(self.cli("init", str(TWO_CHAPTERS))["run_id"], "demo")


if __name__ == "__main__":
    unittest.main()
