"""list：列出条目；--markdown 出一张给委托人的核对单。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import changed, run  # noqa: E402


class ListCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.register = support.make_project(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def ids(self, *extra):
        code, out, err = run("list", self.register, *extra)
        self.assertEqual(code, 0, err[-300:])
        return [item["id"] for item in json.loads(out)]

    def markdown(self, *extra):
        code, out, err = run("list", self.register, "--markdown", *extra)
        self.assertEqual(code, 0, err[-300:])
        return out

    def test_by_default_the_open_items_are_listed(self):
        self.assertEqual(self.ids(), ["T-01"])
        self.assertEqual(self.ids("--status", "open"), ["T-01"])
        self.assertEqual(self.ids("--status", "decided"), ["T-02", "T-03"])
        self.assertEqual(self.ids("--status", "closed"), ["T-04"])
        self.assertEqual(self.ids("--status", "all"), ["T-01", "T-02", "T-03", "T-04"])
        code, out, _ = run("list", self.register, "--status", "all")
        self.assertEqual(json.loads(out)[0], support.good_register()["items"][0])  # 条目原样给出

    def test_the_checklist_for_the_principal(self):
        out = self.markdown()
        lines = out.splitlines()
        self.assertEqual(lines[0], "## 季度报表（测试）：还没定的条目（共 1 条）")
        self.assertIn("- **T-01**（规则打架，还没定，自 2026-10-20 起）金额保留几位：金额保留两位小数还是整数？", out)
        self.assertIn("  - 定下之前：已采纳的报表不动；新表里的金额先照原始数据列出。", out)
        self.assertIn("  - 口径第三版，第二条：金额一律保留两位小数", out)   # 有 label 用 label
        self.assertIn("  - 报表排版规范，第一条：金额保留整数", out)        # 没有 label 用 title
        self.assertIn("  - AI 的建议：两份同样具体、谁也不是谁的新版本，交委托人定。", out)
        self.assertNotIn("T-02", out)

    def test_decided_items_show_who_decided_and_where_the_lines_are(self):
        out = self.markdown("--status", "decided")
        self.assertIn("## 季度报表（测试）：已定的条目（共 2 条）", out)
        self.assertIn("- **T-02**（描述和成果对不上，已定）口径说已经重算，摘要还按 7 天计：“已经重算过”是描述", out)
        self.assertIn("  - q3-summary（reports/q3-summary.md）第 3 行：按 7 天内登录计", out)
        self.assertIn("  - 定的人：AI，2026-11-01，按裁决顺序第 2 步", out)
        self.assertIn("- **T-03**（登记过的例外，已定）", out)
        self.assertIn("  - 定的人：委托人，2026-11-01，原话：“CSV 是给系统导入的，照原样。”（委托人 2026-11-01 的邮件）", out)
        out = self.markdown("--status", "closed")
        self.assertIn("- **T-04**（规则打架，已关闭）旧口径和财务规定对活跃用户的说法不同：第三版已经改成 30 天，这一条不再成立。", out)

    def test_the_checklist_shows_whether_a_rule_is_a_must_or_a_should(self):
        def strengths(r):
            for side in r["items"][0]["sides"]:
                side["strength"] = "must"
            r["items"][3]["sides"][1]["strength"] = "should"
        support.write_json(self.register, changed(strengths))
        out = self.markdown()
        self.assertIn("  - 口径第三版，第二条（必须）：金额一律保留两位小数", out)
        self.assertIn("  - 报表排版规范，第一条（必须）：金额保留整数", out)
        out = self.markdown("--status", "closed")
        self.assertIn("  - 财务部的金额书写规定，附录（建议）：活跃用户按 30 天计", out)
        self.assertIn("  - 数据组的指标口径（第二版），第一条：最近 7 天内登录过的用户", out)   # 没写的不显示
        code, out, _ = run("list", self.register, "--status", "closed")
        self.assertEqual(json.loads(out)[0]["sides"][1]["strength"], "should")   # JSON 照原样给出

    def test_a_strength_that_check_would_reject_is_marked_as_written(self):
        # list 不核 strength 的值（先跑 check），也不出错；写的不是 must、should 的，照 JSON 的写法标出来，
        # 免得“必须”“ must”这类写错了的，在核对单里看起来和对的一样。
        for value, shown in (("必须", '"必须"'), (" must", '" must"'), ("MUST", '"MUST"'), ("", '""'),
                             (False, "false"), ({"level": 1}, '{"level": 1}')):
            with self.subTest(value=value):
                support.write_json(self.register, changed(lambda r: r["items"][0]["sides"][0].update(strength=value)))
                out = self.markdown()
                self.assertIn("  - 口径第三版，第二条（strength 写的是 %s，先跑 check）：金额一律保留两位小数" % shown, out)
                self.assertNotIn("（必须）", out)

    def test_line_breaks_in_values_stay_inside_the_item(self):
        def multiline(r):
            r["items"][0]["meanwhile"] = "第一步：照原样。\n第二步：标出来。\r\n\r\n## 已定的条目（共 0 条）"
            r["items"][0]["sides"][0]["quote"] = "金额一律\n保留两位小数"
        support.write_json(self.register, changed(multiline))
        out = self.markdown()
        self.assertIn("  - 定下之前：第一步：照原样。／第二步：标出来。／## 已定的条目（共 0 条）", out)
        self.assertIn("  - 口径第三版，第二条：金额一律／保留两位小数", out)
        for line in out.splitlines():
            self.assertTrue(line == "" or line.startswith(("## ", "- ", "  ")), line)
        self.assertEqual(sum(1 for line in out.splitlines() if line.startswith("## ")), 1)

    def test_a_since_on_an_item_that_is_not_open_is_not_shown(self):
        support.write_json(self.register, changed(lambda r: r["items"][1].update(since="2026-10-01")))
        out = self.markdown("--status", "decided")
        self.assertIn("- **T-02**（描述和成果对不上，已定）", out)
        self.assertNotIn("自 2026-10-01 起", out)

    def test_nothing_open_says_so(self):
        support.write_json(self.register, changed(lambda r: r["items"].pop(0)))
        out = self.markdown()
        self.assertEqual(out, "## 季度报表（测试）：还没定的条目（共 0 条）\n\n没有。\n")
        self.assertEqual(self.ids(), [])

    def test_a_broken_register_fails_cleanly(self):
        broken = {
            "not json": '{"schema": ',
            "a list": "[1, 2]",
            "items an object": json.dumps(changed(lambda r: r.update(items={"T-01": {}}))),
            "an item that is a string": json.dumps(changed(lambda r: r["items"].append("T-09"))),
            "wrong schema": json.dumps(changed(lambda r: r.update(schema="other/1"))),
        }
        for name, text in broken.items():
            with self.subTest(name=name):
                support.write_text(self.register, text)
                for extra in ((), ("--markdown",)):
                    code, out, err = run("list", self.register, *extra)
                    self.assertEqual(code, 1, (name, out))
                    self.assertNotIn("Traceback", err)
                    result = json.loads(out)
                    self.assertEqual(result["status"], "FAIL")
                    self.assertTrue(result["problems"])
        support.write_text(self.register, json.dumps(support.good_register(), ensure_ascii=False), encoding="gbk")
        code, out, err = run("list", self.register)
        self.assertEqual(code, 1)
        self.assertIn("登记表不是 UTF-8 文本", json.loads(out)["problems"][0])
        code, out, err = run("list", self.dir / "nope.json")
        self.assertEqual(code, 1)
        self.assertIn("找不到登记表", json.loads(out)["problems"][0])

    def test_an_unknown_status_is_a_usage_error(self):
        code, out, err = run("list", self.register, "--status", "pending")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_output_is_utf8_when_the_console_code_page_is_gbk(self):
        support.write_json(self.register, changed(lambda r: r["items"][0].update(ask="保留两位吗？（例：𠮷）")))
        # 这里不用 -I：隔离模式不认 PYTHONIOENCODING，而要看的正是 GBK 管道。
        proc = subprocess.run([sys.executable, "-B", str(support.SCRIPT), "list", str(self.register), "--markdown"],
                              capture_output=True, env=support.gbk_console_env())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace")[-300:])
        self.assertIn("𠮷", proc.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
