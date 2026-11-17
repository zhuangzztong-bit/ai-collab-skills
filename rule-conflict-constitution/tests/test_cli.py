"""命令行：帮助文字、用法错误的退出码、只用标准库。"""

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import run  # noqa: E402


class CommandLine(unittest.TestCase):
    def test_help_runs_under_isolated_mode_and_says_what_it_cannot_judge(self):
        code, out, err = run("--help")
        self.assertEqual(code, 0, err[-300:])
        for word in ("check", "list", "collide", "conflict-register/1", "退出码", support.MARKER, support.MARKER_EN):
            self.assertIn(word, out)
        self.assertIn("判断不了", out)
        for command in ("check", "list", "collide"):
            code, out, err = run(command, "--help")
            self.assertEqual(code, 0, (command, err[-300:]))

    def test_usage_errors_exit_2_without_a_traceback(self):
        for args in ((), ("frobnicate",), ("check",), ("collide", "--register", "x.json", "词")):
            with self.subTest(args=args):
                code, out, err = run(*args)
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err)

    @unittest.skipIf(support.WINDOWS, "Windows 的命令行参数是 Unicode，传不了不能按 UTF-8 解的字节")
    def test_arguments_that_are_not_utf8_do_not_crash(self):
        # 命令行参数里有不能按 UTF-8 解的字节（比如终端用的是别的编码）：要查的词按用法错误退出 2，
        # 登记表路径照常报“找不到”，都不出错误堆栈。
        base = [sys.executable, "-I", "-B", str(support.SCRIPT)]
        with tempfile.TemporaryDirectory() as tmp:
            register = support.make_project(tmp)
            word = subprocess.run([os.fsencode(a) for a in base + ["collide", "--register", str(register),
                                                                    "--texts-root", tmp]] + [b"\xff\xfe"],
                                  capture_output=True)
            self.assertEqual(word.returncode, 2)
            self.assertNotIn(b"Traceback", word.stderr)
            path = subprocess.run([os.fsencode(a) for a in base + ["check"]] + [os.fsencode(tmp) + b"/\xff.json"],
                                  capture_output=True)
        self.assertEqual(path.returncode, 1)
        self.assertNotIn(b"Traceback", path.stderr)
        self.assertIn("找不到登记表", json.loads(path.stdout.decode("utf-8"))["problems"][0])

    def test_only_the_standard_library_is_imported(self):
        tree = ast.parse(support.SCRIPT.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module.split(".")[0])
        allowed = {"argparse", "codecs", "difflib", "hashlib", "json", "math", "pathlib", "re", "stat", "sys"}
        self.assertLessEqual(names, allowed, names - allowed)

    def test_the_wording_is_the_general_one(self):
        # 通用版不用写小说时的叫法。
        files = [support.SCRIPT, support.TEMPLATE] + sorted(p for p in support.EXAMPLES.rglob("*") if p.is_file())
        for path in files:
            text = path.read_text(encoding="utf-8")
            for word in ("小说", "作者", "工坊", "正文", "章节"):
                self.assertNotIn(word, text, (path.name, word))


if __name__ == "__main__":
    unittest.main()
