import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/blind_review.py"
SPEC = importlib.util.spec_from_file_location("blind_review", SCRIPT)
blind_review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blind_review)


class FailingBuffer:
    def __init__(self, fail_on):
        self.fail_on = fail_on

    def write(self, data):
        if self.fail_on == "write":
            raise OSError(28, "No space left on device")
        return len(data)

    def flush(self):
        if self.fail_on == "flush":
            raise OSError(28, "No space left on device")


class FailingStdout:
    def __init__(self, fail_on):
        self.buffer = FailingBuffer(fail_on)

    def fileno(self):
        raise io.UnsupportedOperation("no file descriptor")

    def flush(self):
        pass


class BlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.brief = root / "brief.txt"
        self.baseline = root / "baseline-output.txt"
        self.candidate = root / "candidate-output.txt"
        self.key = root / "manager-key.json"
        self.packet = root / "reviewer-packet.json"
        self.brief.write_bytes("列出开放时间，保留时区。\n".encode())
        self.baseline.write_bytes("开放时间 09:00 UTC。\r\n".encode())
        self.candidate.write_bytes("每日 09:00 UTC 开放。\n".encode())

    def arguments(self, *extra):
        return [str(self.baseline), str(self.candidate),
                "--brief", str(self.brief), "--key-out", str(self.key), *extra]

    def run_cli(self, *extra, stdout=subprocess.PIPE):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *self.arguments(*extra)],
            stdout=stdout, stderr=subprocess.PIPE,
        )

    def run_main(self, stdout, *extra):
        stderr = io.StringIO()
        with patch.object(sys, "argv", ["blind_review.py", *self.arguments(*extra)]), \
                patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr), \
                self.assertRaises(SystemExit) as caught:
            blind_review.main()
        return caught.exception.code, stderr.getvalue()

    def assert_packet_matches_key(self, packet_bytes):
        packet = json.loads(packet_bytes)
        key = json.loads(self.key.read_bytes())
        self.assertEqual(set(packet), {"brief", "outputs"})
        self.assertEqual(set(packet["outputs"]), {"A", "B"})
        self.assertEqual(set(key), {"packet_sha256", "roles"})
        self.assertEqual(packet["brief"], self.brief.read_bytes().decode())
        self.assertEqual(key["packet_sha256"], hashlib.sha256(packet_bytes).hexdigest())
        originals = {"baseline": self.baseline, "candidate": self.candidate}
        self.assertEqual(sorted(key["roles"].values()), ["baseline", "candidate"])
        for label, role in key["roles"].items():
            self.assertEqual(packet["outputs"][label], originals[role].read_bytes().decode())
        for value in (str(self.baseline), str(self.candidate), str(self.key), self.directory.name):
            self.assertNotIn(value.encode(), packet_bytes)

    def test_cli_separates_mapping_and_preserves_original_text(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_packet_matches_key(result.stdout)

    def test_packet_out_writes_a_new_file_that_matches_the_mapping(self):
        result = self.run_cli("--packet-out", str(self.packet))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assert_packet_matches_key(self.packet.read_bytes())

    def test_both_random_orders_keep_the_mapping_consistent(self):
        for index, expected_role in enumerate(("baseline", "candidate")):
            with self.subTest(index=index), patch.object(blind_review.secrets, "randbelow", return_value=index):
                packet, key = blind_review.prepare(self.brief, self.baseline, self.candidate, [])
                self.assertEqual(json.loads(key)["roles"]["A"], expected_role)
                expected_file = getattr(self, expected_role)
                self.assertEqual(json.loads(packet)["outputs"]["A"], expected_file.read_bytes().decode())

    def test_rejects_version_paths_in_outputs_without_rewriting_them(self):
        output = b"Step 1: read runs\\S1-holdout\\schedule.json.\n"
        self.candidate.write_bytes(output)
        self.assertIn(b"S1-holdout", self.candidate.read_bytes())
        result = self.run_cli("--identity-marker", "runs/s1-holdout")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(b"holdout", result.stderr)
        self.assertFalse(self.key.exists())
        self.assertEqual(self.candidate.read_bytes(), output)

    def test_rejects_markers_written_in_other_forms(self):
        cases = (
            ("C:\\runs\\current", '{"path": "C:\\\\runs\\\\current\\\\x.json"}'),
            ("runs/current", '{"path": "runs\\/current"}'),
            ("runs/current", "runs//current"),
            ("runs/current", "runs/./current"),
            ("runs/current", "ＲＵＮＳ/ｃｕｒｒｅｎｔ"),
            ("runs/current", "runs／current"),
            ("runs/current", "runs＼current"),
            ("runs/current", "runs%2Fcurrent"),
            ("runs/current", "runs/\u200bcurrent"),
            ("runs/current", "runs / current"),
            ("runs/current", "runs/\ncurrent"),
            ("./runs/current", "runs/current/x"),
            ("runs/current/", "runs/current."),
            (" runs/current", "/runs/current"),
            ("caf\u00e9/v2", "cafe\u0301/v2"),
        )
        for marker, text in cases:
            with self.subTest(marker=marker, text=text):
                self.candidate.write_bytes(text.encode())
                with self.assertRaisesRegex(ValueError, "^candidate contains a known version identifier"):
                    blind_review.prepare(self.brief, self.baseline, self.candidate, [marker])
        self.candidate.write_bytes("每日 09:00 UTC 开放。\n".encode())
        for marker in {marker for marker, _ in cases}:
            with self.subTest(clean_marker=marker):
                blind_review.prepare(self.brief, self.baseline, self.candidate, [marker])

    def test_rejects_markers_and_input_filenames_in_brief(self):
        for brief in (f"Deliverable is {self.baseline.name.upper()}", "上一轮在 runs/current 里"):
            with self.subTest(brief=brief):
                self.brief.write_bytes(brief.encode())
                result = self.run_cli("--identity-marker", "runs/current")
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr.startswith(b"blind review: brief "), result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertFalse(self.key.exists())

    def test_rejects_unreadable_or_empty_material_and_names_the_input(self):
        for role, value, message in (
            ("candidate", b"", b"candidate is empty"),
            ("candidate", b" \r\n\t", b"candidate is empty"),
            ("candidate", b"\xef\xbb\xbf", b"candidate is empty"),
            ("candidate", "\u200b\u2060".encode(), b"candidate is empty"),
            ("candidate", b"\xff", b"candidate is not valid UTF-8"),
            ("candidate", "开放".encode("gbk"), b"candidate is not valid UTF-8"),
            ("brief", "开放".encode("gbk"), b"brief is not valid UTF-8"),
            ("baseline", "开放".encode("utf-16"), b"baseline is not valid UTF-8"),
        ):
            with self.subTest(role=role, value=value):
                path = getattr(self, role)
                original = path.read_bytes()
                path.write_bytes(value)
                result = self.run_cli()
                path.write_bytes(original)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertFalse(self.key.exists())

    def test_cannot_overwrite_an_existing_mapping_or_packet(self):
        self.key.write_bytes(b"existing mapping")
        for extra in ((), ("--packet-out", str(self.packet))):
            with self.subTest(extra=extra):
                result = self.run_cli(*extra)
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr.startswith(b"blind review: "), result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(self.key.read_bytes(), b"existing mapping")
                self.assertFalse(self.packet.exists())

        self.key.unlink()
        self.packet.write_bytes(b"existing packet")
        result = self.run_cli("--packet-out", str(self.packet))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.packet.read_bytes(), b"existing packet")
        self.assertFalse(self.key.exists())

        self.packet.unlink()
        result = self.run_cli("--packet-out", str(self.key))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.key.exists())

    def test_failed_packet_file_leaves_no_mapping_behind(self):
        missing = Path(self.directory.name) / "missing" / "packet.json"
        result = self.run_cli("--packet-out", str(missing))
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith(b"blind review: "), result.stderr)
        self.assertFalse(self.key.exists())
        self.assertFalse(missing.exists())

    def test_failed_standard_output_leaves_no_mapping_behind(self):
        for stdout in (FailingStdout("write"), FailingStdout("flush"), None):
            with self.subTest(stdout=stdout and stdout.buffer.fail_on):
                code, stderr = self.run_main(stdout)
                self.assertEqual(code, 1)
                self.assertTrue(stderr.startswith("blind review: "), stderr)
                self.assertFalse(self.key.exists())
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_packet_matches_key(result.stdout)

    @unittest.skipUnless(os.path.exists("/dev/full"), "needs /dev/full")
    def test_full_disk_on_standard_output_reports_the_error(self):
        with open("/dev/full", "wb") as full:
            result = self.run_cli(stdout=full)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(result.stderr.startswith(b"blind review: "), result.stderr)
        self.assertNotIn(b"Exception ignored", result.stderr)
        self.assertFalse(self.key.exists())

    def test_reports_format_differences_without_rewriting(self):
        self.assertEqual(blind_review.format_differences("x\r\n", "y\n"), ["line endings"])
        self.assertEqual(blind_review.format_differences("\ufeffx\n", "y\n"), ["byte order mark"])
        self.assertEqual(blind_review.format_differences("x", "y\n"), ["line breaks at the end"])
        self.assertEqual(blind_review.format_differences("x\n\n", "y\n"), ["line breaks at the end"])
        self.assertEqual(blind_review.format_differences("x\ny\n", "z\n"), [])
        self.assertEqual(blind_review.format_differences("x", "y\nz"), [])

        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"line endings", result.stderr)
        self.assertIn("开放时间 09:00 UTC。\r\n", json.loads(result.stdout)["outputs"].values())

        with self.subTest(stderr="closed"):
            self.key.unlink()
            stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
            with patch.object(sys, "argv", ["blind_review.py", *self.arguments()]), \
                    patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", None):
                blind_review.main()
            stdout.flush()
            self.assert_packet_matches_key(stdout.buffer.getvalue())

        if os.path.exists("/dev/full"):
            for extra, code in ((("--packet-out", str(self.packet)), 0),
                                (("--identity-marker", "09:00"), 1)):
                with self.subTest(stderr="full", extra=extra):
                    self.key.unlink(missing_ok=True)
                    self.packet.unlink(missing_ok=True)
                    with open("/dev/full", "wb") as full:
                        result = subprocess.run(
                            [sys.executable, "-B", str(SCRIPT), *self.arguments(*extra)],
                            stdout=subprocess.PIPE, stderr=full,
                        )
                    self.assertEqual(result.returncode, code)
                    self.assertEqual(self.key.exists(), code == 0)
                    if code == 0:
                        self.assert_packet_matches_key(self.packet.read_bytes())
                    else:
                        self.assertFalse(self.packet.exists())
