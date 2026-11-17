"""collide：新叫法在已采纳的成果里已有的用法；没读全的不算“没撞上”。"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import changed, run  # noqa: E402


class CollideCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.register = support.make_project(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def collide(self, *words, root=None, extra=()):
        code, out, err = run("collide", "--register", self.register, "--texts-root", root or self.dir, *extra, *words)
        self.assertNotIn("Traceback", err)
        return code, json.loads(out)

    def test_prior_uses_are_listed_by_text_and_line(self):
        code, result = self.collide("活跃用户", "留存", "日活")
        self.assertEqual(code, 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["checked"], ["q3-summary", "q3-metrics"])
        self.assertEqual(result["texts"], ["q3-summary", "q3-metrics"])
        self.assertEqual((result["missing_texts"], result["unreadable_texts"]), ([], []))
        self.assertEqual([(h["text"], h["line"]) for h in result["words"]["活跃用户"]],
                         [("q3-summary", 3), ("q3-metrics", 2)])
        self.assertEqual([(h["text"], h["line"]) for h in result["words"]["留存"]],
                         [("q3-summary", 9), ("q3-metrics", 4)])
        self.assertEqual(result["words"]["日活"], [])
        self.assertEqual(result["words"]["活跃用户"][1]["snippet"], "活跃用户,1204")

    def test_a_missing_text_makes_the_result_incomplete(self):
        (self.dir / "reports" / "q3-summary.md").unlink()
        code, result = self.collide("活跃用户")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertEqual(result["missing_texts"], [{"text": "q3-summary", "path": "reports/q3-summary.md"}])
        self.assertEqual(result["checked"], ["q3-metrics"])
        self.assertEqual([h["line"] for h in result["words"]["活跃用户"]], [2])   # 读到的照样列

    def test_the_wrong_texts_root_is_not_a_clean_result(self):
        code, result = self.collide("活跃用户", root=self.dir / "elsewhere")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertIn("--texts-root 不是目录", result["error"])

    def test_a_register_without_texts_checks_nothing(self):
        support.write_json(self.register, changed(lambda r: r.update(texts={})))
        code, result = self.collide("活跃用户")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertIn("texts", result["error"])

    def test_a_text_that_is_not_utf8_is_named_and_not_counted_as_read(self):
        support.write_text(self.dir / "reports" / "q3-metrics.csv", support.CSV, encoding="gbk")
        code, result = self.collide("活跃用户")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertEqual(result["checked"], ["q3-summary"])
        [entry] = result["unreadable_texts"]
        self.assertEqual((entry["text"], entry["path"]), ("q3-metrics", "reports/q3-metrics.csv"))
        self.assertIn("不是 UTF-8 文本（第 1 行", entry["reason"])

    def test_matching_is_exact_unless_ignore_case(self):
        support.write_text(self.dir / "reports" / "q3-summary.md", "Open the Workspace menu.\nworkspace_id = 7\n")
        code, result = self.collide("workspace")
        self.assertEqual([h["line"] for h in result["words"]["workspace"]], [2])
        code, result = self.collide("workspace", extra=("--ignore-case",))
        self.assertEqual([h["line"] for h in result["words"]["workspace"]], [1, 2])
        # 只按字面找：不认词形、不分词，找 work 也会命中 workspace。
        code, result = self.collide("work")
        self.assertEqual([h["line"] for h in result["words"]["work"]], [2])

    def test_the_snippet_shows_the_word_on_a_long_line(self):
        line = "甲" * 150 + "留存率" + "乙" * 150
        support.write_text(self.dir / "reports" / "q3-summary.md", line + "\n")
        code, result = self.collide("留存率")
        [hit] = result["words"]["留存率"]
        self.assertIn("留存率", hit["snippet"])
        self.assertLess(len(hit["snippet"]), 100)
        self.assertTrue(hit["snippet"].startswith("…") and hit["snippet"].endswith("…"), hit["snippet"])

    def test_a_word_given_twice_counts_once(self):
        code, result = self.collide("留存", "留存")
        self.assertEqual(list(result["words"]), ["留存"])
        self.assertEqual([(h["text"], h["line"]) for h in result["words"]["留存"]],
                         [("q3-summary", 9), ("q3-metrics", 4)])

    def test_the_snippet_keeps_forty_characters_on_each_side(self):
        support.write_text(self.dir / "reports" / "q3-summary.md", "甲" * 100 + "留存率" + "乙" * 100 + "\n")
        code, result = self.collide("留存率")
        [hit] = result["words"]["留存率"]
        self.assertEqual(hit["snippet"], "…" + "甲" * 40 + "留存率" + "乙" * 40 + "…")

    def test_ignore_case_finds_the_word_on_a_long_line_with_letters_that_fold_longer(self):
        # ß 折叠后是 ss，长度变了；截取的位置仍要落在命中的词上。
        line = "ß" * 100 + "甲" * 100 + "Refund 退款" + "乙" * 100
        support.write_text(self.dir / "reports" / "q3-summary.md", line + "\n")
        code, result = self.collide("refund", extra=("--ignore-case",))
        [hit] = result["words"]["refund"]
        self.assertTrue(hit["snippet"].startswith("…" + "甲" * 40 + "Refund"), hit["snippet"])

    def test_a_register_without_texts_says_texts_is_empty(self):
        for value in ("absent", None):
            with self.subTest(value=value):
                def drop(r):
                    if value == "absent":
                        del r["texts"]
                    else:
                        r["texts"] = None
                support.write_json(self.register, changed(drop))
                code, result = self.collide("活跃用户")
                self.assertEqual((code, result["complete"]), (1, False))
                self.assertIn("texts 是空的", result["error"])

    def test_a_text_that_is_a_directory_is_unreadable_not_missing(self):
        (self.dir / "reports" / "q3-summary.md").unlink()
        (self.dir / "reports" / "q3-summary.md").mkdir()
        code, result = self.collide("活跃用户")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertEqual(result["missing_texts"], [])
        [entry] = result["unreadable_texts"]
        self.assertEqual(entry["text"], "q3-summary")
        self.assertIn("不是普通文件", entry["reason"])

    def test_an_empty_texts_root_is_a_usage_error(self):
        code, out, err = run("collide", "--register", self.register, "--texts-root", "", "活跃用户")
        self.assertEqual(code, 2)
        self.assertIn("--texts-root 不能是空的", err)
        self.assertNotIn("Traceback", err)

    def test_an_empty_word_is_a_usage_error(self):
        code, out, err = run("collide", "--register", self.register, "--texts-root", self.dir, "活跃用户", " ")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_a_broken_register_fails_cleanly(self):
        for text in ('{"schema": ', "[1, 2]", json.dumps(changed(lambda r: r.update(texts=["a.md"]))),
                     json.dumps(changed(lambda r: r.update(schema="other/1")))):
            with self.subTest(text=text[:30]):
                support.write_text(self.register, text)
                code, out, err = run("collide", "--register", self.register, "--texts-root", self.dir, "活跃用户")
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", err)
                self.assertFalse(json.loads(out)["complete"])
        code, out, err = run("collide", "--register", self.dir / "nope.json", "--texts-root", self.dir, "活跃用户")
        self.assertEqual(code, 1)
        self.assertIn("找不到登记表", json.loads(out)["error"])

    def test_a_text_path_that_is_not_a_string_counts_as_missing(self):
        support.write_json(self.register, changed(lambda r: r["texts"].update({"q3-summary": 7})))
        code, result = self.collide("活跃用户")
        self.assertEqual((code, result["complete"]), (1, False))
        self.assertEqual(result["missing_texts"], [{"text": "q3-summary", "path": 7}])


if __name__ == "__main__":
    unittest.main()
