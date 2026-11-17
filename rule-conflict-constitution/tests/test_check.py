"""check：登记表的结构、来源的版本和哈希、证据的原句和行号。"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import changed, run  # noqa: E402


class CheckCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.register = support.make_project(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def check(self, *extra, register=None, path=None):
        if register is not None:
            support.write_json(self.register, register)
        code, out, err = run("check", path or self.register, *extra)
        self.assertNotIn("Traceback", err)
        self.assertTrue(out.strip().startswith("{"), (out[-300:], err[-300:]))
        result = json.loads(out)
        self.assertEqual(code, 0 if result["status"] == "OK" else 1, result)
        return result

    def check_full(self, register=None):
        return self.check("--texts-root", self.dir, register=register)

    def assert_problem(self, result, needle):
        self.assertEqual(result["status"], "FAIL", needle)
        self.assertTrue(any(needle in p for p in result["problems"]), (needle, result["problems"]))


class GoodRegister(CheckCase):
    def test_full_check_passes_and_reports_what_it_counted(self):
        result = self.check_full()
        self.assertEqual(result["status"], "OK", result["problems"])
        self.assertEqual(result["problems"], [])
        self.assertTrue(result["texts_checked"])
        self.assertEqual(result["counts"], {"open": 1, "decided": 2, "closed": 1})
        self.assertEqual(result["kinds"], {"conflict": 2, "mismatch": 1, "collision": 0, "stale": 0, "exception": 1})
        sources = result["sources"]
        self.assertEqual((sources["in_force"], sources["superseded"], sources["pending"]), (3, 1, 0))
        self.assertEqual(sources["stale"], [])
        # 每份读到的本地来源都给出现在的摘要，登记 sha256 时可以照抄。
        self.assertEqual(sources["digests"]["metrics-v3"], support.original_digest(support.METRICS))
        self.assertEqual(sources["digests"]["layout"], support.original_digest(support.LAYOUT))
        self.assertNotIn("finance", sources["digests"])

    def test_what_was_not_checked_is_said(self):
        full = self.check_full()
        # 外部依据没有本地文件，引它的原句核不了，要说出来。
        self.assertTrue(any("finance" in w and "没有核" in w for w in full["warnings"]), full["warnings"])
        plain = self.check()
        self.assertEqual(plain["status"], "OK", plain["problems"])
        self.assertFalse(plain["texts_checked"])
        self.assertTrue(any("--texts-root" in w for w in plain["warnings"]), plain["warnings"])

    def test_without_texts_root_text_lines_are_not_checked(self):
        def wrong_line(r):
            r["items"][1]["sides"][1]["line"] = 4
        self.assertEqual(self.check(register=changed(wrong_line))["status"], "OK")
        self.assert_problem(self.check_full(changed(wrong_line)), "第 4 行")


class BrokenShapes(CheckCase):
    def test_each_broken_shape_is_reported(self):
        def drop(key, index=None):
            def change(r):
                target = r if index is None else r[index[0]][index[1]]
                del target[key]
            return change

        cases = [
            ("conflict-register/1", lambda r: r.update(schema="conflict-register/0")),
            ("project", drop("project")),
            ("updated", drop("updated")),
            ("sources 必须是非空列表", lambda r: r.update(sources=[])),
            ("来源 layout 缺 title", drop("title", ("sources", 2))),
            ("来源 layout 缺 version", drop("version", ("sources", 2))),
            ("来源 layout：status", lambda r: r["sources"][2].update(status="active")),
            ("不存在的来源 nope", lambda r: r["items"][0]["sides"][0].update(source="nope")),
            ("要写 where", lambda r: r["items"][0]["sides"][0].pop("where")),
            ("不存在的成果 q9", lambda r: r["items"][1]["sides"][1].update(text="q9")),
            ("T-01 是 open，要写 ask", drop("ask", ("items", 0))),
            ("T-01 是 open，要写 meanwhile", drop("meanwhile", ("items", 0))),
            ("T-01 是 open，却写了 resolution", lambda r: r["items"][0].update(resolution="已经定了")),
            ("T-02 是 decided，要写 resolution", drop("resolution", ("items", 1))),
            ("T-04 是 closed，要写 resolution", drop("resolution", ("items", 3))),
            ("principal 或 ai", lambda r: r["items"][1]["decided_by"].update(who="author")),
            ("decided_by.when", lambda r: r["items"][1]["decided_by"].pop("when")),
            ("原话", lambda r: r["items"][2]["decided_by"].pop("words")),
            ("出处", lambda r: r["items"][2]["decided_by"].pop("source")),
            ("superseded，但没写 superseded_by", lambda r: r["sources"][1].pop("superseded_by")),
            ("in_force，却写了 superseded_by", lambda r: r["sources"][2].update(superseded_by="metrics-v3")),
            ("in_force 或 pending", lambda r: r["sources"][1].update(superseded_by="metrics-v2")),
            ("只引了被取代的来源", lambda r: [s.update(source="metrics-v2") for s in r["items"][0]["sides"]]),
            ("至少要有 2 项", lambda r: r["items"][0].update(sides=r["items"][0]["sides"][:1])),
            ("至少要有 1 项", lambda r: r["items"][2].update(sides=[])),
            ("条目 id T-01 出现了两次", lambda r: r["items"][1].update(id="T-01")),
            ("来源 id layout 出现了两次", lambda r: r["sources"].append(dict(r["sources"][2]))),
            ("kind 必须是", lambda r: r["items"][0].update(kind="clash")),
            ("status 必须是 open、decided、closed", lambda r: r["items"][0].update(status="pending")),
            ("T-01 缺 title", drop("title", ("items", 0))),
            ("不能两个都写", lambda r: r["items"][1]["sides"][1].update(source="layout", where="第一条")),
            ("必须引一个来源", lambda r: r["items"][0]["sides"][0].pop("source")),
            ("line 必须是正整数", lambda r: r["items"][1]["sides"][1].update(line=0)),
            ("line 必须是正整数", lambda r: r["items"][1]["sides"][1].update(line="3")),
            ("line 必须是正整数", lambda r: r["items"][1]["sides"][1].update(line=True)),
            ("要写 quote", lambda r: r["items"][1]["sides"][1].pop("quote")),
            ("要写 file", lambda r: r["sources"][2].pop("file")),
            ("找不到文件 rules/missing.md", lambda r: r["sources"][2].update(file="rules/missing.md")),
            ("items 必须是列表", lambda r: r.update(items={})),
            ("texts 必须是对象", lambda r: r.update(texts=["reports/q3-summary.md"])),
        ]
        for needle, change in cases:
            with self.subTest(needle=needle):
                self.assert_problem(self.check_full(changed(change)), needle)

    def test_an_ai_decision_names_step_one_to_four_as_an_integer(self):
        for step in (1, 4):
            result = self.check_full(changed(lambda r: r["items"][1]["decided_by"].update(rule_applied=step)))
            self.assertEqual(result["status"], "OK", (step, result["problems"]))
        for step in (5, 0, True, "1", 1.0, None):
            with self.subTest(step=step):
                result = self.check_full(changed(lambda r: r["items"][1]["decided_by"].update(rule_applied=step)))
                self.assert_problem(result, "第 5 步只能由委托人定")

    def test_external_is_only_a_json_true(self):
        local = {"id": "layout", "title": "报表排版规范", "file": "rules/missing.md", "version": "1",
                 "date": "2026-09-01", "status": "in_force", "sha256": "0" * 64}
        for value in ("false", "true", 1, 0, [], {}):
            with self.subTest(value=value):
                result = self.check_full(changed(lambda r: r["sources"].__setitem__(2, dict(local, external=value))))
                self.assert_problem(result, "external 只能是 JSON 的 true 或 false")
                # 写错了的 external 不算外部依据，文件照样要核。
                self.assert_problem(result, "找不到文件 rules/missing.md")
        result = self.check_full(changed(lambda r: r["sources"].__setitem__(2, dict(local, external=False))))
        self.assert_problem(result, "找不到文件 rules/missing.md")
        self.assertFalse(any("external 只能是" in p for p in result["problems"]))
        result = self.check_full(changed(lambda r: r["sources"][2].update(external=None)))
        self.assertEqual(result["status"], "OK", result["problems"])

    def test_a_duplicate_json_key_is_reported(self):
        text = json.dumps(support.good_register(), ensure_ascii=False)
        text = text.replace('"texts": {', '"texts": {"q3-summary": "reports/other.md", ', 1)
        support.write_text(self.register, text)
        result = self.check("--texts-root", self.dir)
        self.assert_problem(result, "键 q3-summary 出现了两次")

    def test_wrong_shapes_fail_with_a_message_and_no_traceback(self):
        shapes = {
            "sides null": lambda r: r["items"][0].update(sides=None),
            "sides a string": lambda r: r["items"][0].update(sides="第一条"),
            "a side that is a list": lambda r: r["items"][0].update(sides=[["metrics-v3"], ["layout"]]),
            "a source id that is a list": lambda r: r["items"][0]["sides"][0].update(source=["metrics-v3"]),
            "a text path that is a number": lambda r: r["texts"].update({"q3-summary": 7}),
            "an item that is a string": lambda r: r["items"].append("T-09"),
            "a source that is a string": lambda r: r["sources"].append("layout"),
            "a file that is a number": lambda r: r["sources"][2].update(file=7),
            "superseded_by a list": lambda r: r["sources"][1].update(superseded_by=["metrics-v3"]),
            "status a list": lambda r: r["items"][0].update(status=["open"]),
            "kind a list": lambda r: r["items"][0].update(kind=["conflict"]),
            "decided_by a string": lambda r: r["items"][1].update(decided_by="ai"),
            "sha256 a number": lambda r: r["sources"][0].update(sha256=12),
            "id a number": lambda r: r["items"][0].update(id=1),
        }
        for name, change in shapes.items():
            with self.subTest(name=name):
                result = self.check_full(changed(change))
                self.assertEqual(result["status"], "FAIL", name)
                self.assertTrue(result["problems"], name)
                # 每种形状都要说出具体是哪里不对，不能落到兜底的“核到一半停了”。
                self.assertFalse(any("核到一半停了" in p for p in result["problems"]), (name, result["problems"]))
        # 不是列表的 sides 照实报出来，别的地方照样核，不收成一句笼统的“格式不对”。
        result = self.check_full(changed(lambda r: (r["items"][0].update(sides=None), r["items"][1].pop("title"))))
        self.assert_problem(result, "至少要有 2 项")
        self.assert_problem(result, "T-02 缺 title")
        for top in ([1, 2], "text", None, 3):
            with self.subTest(top=top):
                support.write_json(self.register, top)
                self.assert_problem(self.check(), "登记表最外层必须是一个 JSON 对象")


class Evidence(CheckCase):
    def test_a_text_quote_must_be_on_the_named_line(self):
        result = self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(line=4)))
        self.assert_problem(result, "原句不在 q3-summary 第 4 行")

    def test_a_line_past_the_end_is_reported(self):
        result = self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(line=400)))
        self.assert_problem(result, "q3-summary 只有 30 行")

    def test_a_source_quote_must_be_in_the_file(self):
        result = self.check_full(changed(lambda r: r["items"][0]["sides"][0].update(quote="金额一律保留三位小数")))
        self.assert_problem(result, "原句在 rules/metrics.md 里找不到")

    def test_a_quote_from_the_note_before_the_marker_does_not_count(self):
        result = self.check_full(changed(lambda r: r["items"][0]["sides"][0].update(quote="数据组给的口径说明")))
        self.assert_problem(result, "原句在 rules/metrics.md 里找不到")

    def test_a_quote_from_a_superseded_file_is_checked_when_the_file_is_named(self):
        result = self.check_full(changed(lambda r: r["items"][3]["sides"][0].update(quote="最近 14 天内登录过的用户")))
        self.assert_problem(result, "原句在 rules/old/metrics-v2.md 里找不到")

    def test_a_missing_text_is_reported_under_texts_root(self):
        (self.dir / "reports" / "q3-summary.md").unlink()
        self.assert_problem(self.check_full(), "成果 q3-summary：在 --texts-root 下找不到 reports/q3-summary.md")

    def test_texts_root_must_be_a_directory(self):
        result = self.check("--texts-root", self.dir / "elsewhere")
        self.assert_problem(result, "--texts-root 不是目录")

    def test_line_numbers_count_line_breaks_only(self):
        # 换页符、U+2028 不算换行；CRLF 和 LF 一样；开头的 BOM 不算。
        lines = support.summary_text().split("\n")
        lines[0] = "# 第三季度报表摘要\x0c附注 续"
        text = "﻿" + "\r\n".join(lines)
        support.write_text(self.dir / "reports" / "q3-summary.md", text)
        result = self.check_full()
        self.assertEqual(result["status"], "OK", result["problems"])


class SourceVersions(CheckCase):
    def test_the_hash_pins_the_text_after_the_marker(self):
        rules = self.dir / "rules" / "metrics.md"
        self.assertEqual(self.check()["status"], "OK")
        # 标记之前的加注可以改；标记之后的原文不能改。
        support.write_text(rules, "> 加注改了一句。\n\n" + support.MARKER + "\n" + support.METRICS_BODY)
        self.assertEqual(self.check()["status"], "OK")
        # Windows 上另存（CRLF、带 BOM）的同一份原文，哈希一样。
        support.write_text(rules, "﻿" + support.METRICS.replace("\n", "\r\n"))
        self.assertEqual(self.check()["status"], "OK")
        support.write_text(rules, support.METRICS_NOTE + support.MARKER + "\n"
                           + support.METRICS_BODY.replace("第三版", "第四版"))
        result = self.check()
        self.assert_problem(result, "rules/metrics.md 在登记之后改过")
        self.assertEqual(result["sources"]["stale"], ["metrics-v3"])
        now = support.original_digest(rules.read_text(encoding="utf-8"))
        self.assertTrue(any(now in p for p in result["problems"]), result["problems"])
        self.assertEqual(result["sources"]["digests"]["metrics-v3"], now)

    def test_a_file_without_marker_is_hashed_whole(self):
        def pin(r):
            r["sources"][2]["sha256"] = support.original_digest(support.LAYOUT)
        self.assertEqual(self.check(register=changed(pin))["status"], "OK")
        support.write_text(self.dir / "rules" / "layout.md", support.LAYOUT + "三、新加的一条。\n")
        self.assert_problem(self.check(), "rules/layout.md 在登记之后改过")

    def test_sha256_in_capitals_is_the_same_digest_and_a_bad_one_is_named(self):
        upper = changed(lambda r: r["sources"][0].update(sha256=r["sources"][0]["sha256"].upper()))
        self.assertEqual(self.check(register=upper)["status"], "OK")
        bad = changed(lambda r: r["sources"][0].update(sha256="abc"))
        self.assert_problem(self.check(register=bad), "64 位十六进制")



class Markers(CheckCase):
    """原文标记有中文、英文两种写法；去掉首尾空白后整行正好是它才算；两种都有时，以文件里第一处为准。"""

    def write_rules(self, text):
        support.write_text(self.dir / "rules" / "metrics.md", text)

    def test_either_marker_pins_only_the_text_after_it(self):
        expected = hashlib.sha256(support.METRICS_BODY.encode("utf-8")).hexdigest()
        for marker in (support.MARKER, support.MARKER_EN):
            with self.subTest(marker=marker):
                self.write_rules(support.METRICS_NOTE + marker + "\n" + support.METRICS_BODY)
                result = self.check_full(support.good_register())
                self.assertEqual(result["status"], "OK", result["problems"])
                self.assertEqual(result["sources"]["digests"]["metrics-v3"], expected)
                # 标记之前的加注不算原文：从加注里引的原句找不到。
                note = self.check_full(changed(lambda r: r["items"][0]["sides"][0].update(quote="数据组给的口径说明")))
                self.assert_problem(note, "原句在 rules/metrics.md 里找不到")

    def test_the_english_marker_may_have_spaces_around_it(self):
        self.write_rules(support.METRICS_NOTE + "  " + support.MARKER_EN + "\t \n" + support.METRICS_BODY)
        result = self.check()
        self.assertEqual(result["status"], "OK", result["problems"])

    def test_a_marker_must_be_the_whole_line(self):
        for line in (support.MARKER_EN + " 以下照录", "<!-- Original text begins -->", "<!-- original text begins-->",
                     "引言：" + support.MARKER):
            with self.subTest(line=line):
                text = support.METRICS_NOTE + line + "\n" + support.METRICS_BODY
                self.write_rules(text)
                result = self.check()
                # 不算标记：全文都是原文，摘要变了，报“改过”。
                self.assertEqual(result["sources"]["digests"]["metrics-v3"],
                                 hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assert_problem(result, "rules/metrics.md 在登记之后改过")

    def test_when_both_markers_appear_the_first_one_counts(self):
        middle = "> 中间这段也算原文。\n\n"
        for first, second in ((support.MARKER, support.MARKER_EN), (support.MARKER_EN, support.MARKER)):
            with self.subTest(first=first):
                self.write_rules(support.METRICS_NOTE + first + "\n" + middle + second + "\n" + support.METRICS_BODY)
                original = middle + second + "\n" + support.METRICS_BODY
                expected = hashlib.sha256(original.encode("utf-8")).hexdigest()

                def pin(r):
                    r["sources"][0]["sha256"] = expected
                    r["items"][0]["sides"][0]["quote"] = "中间这段也算原文"
                result = self.check_full(changed(pin))
                self.assertEqual(result["status"], "OK", result["problems"])
                self.assertEqual(result["sources"]["digests"]["metrics-v3"], expected)
                # 只算第二处标记之后的文字，就和登记的摘要对不上。
                self.assertNotEqual(expected, hashlib.sha256(support.METRICS_BODY.encode("utf-8")).hexdigest())

class NotUtf8(CheckCase):
    def test_a_text_that_is_not_utf8_is_named_and_the_rest_is_still_checked(self):
        support.write_text(self.dir / "reports" / "q3-metrics.csv", "指标,数值\n收入,85320.00\n", encoding="gbk")
        result = self.check_full(changed(lambda r: r["items"][0].update(ask="")))
        self.assert_problem(result, "成果 q3-metrics：reports/q3-metrics.csv 不是 UTF-8 文本（第 1 行")
        self.assert_problem(result, "T-01 是 open，要写 ask")   # 别的问题照样报

    def test_a_source_that_is_not_utf8_is_named(self):
        support.write_text(self.dir / "rules" / "layout.md", "# 排版\n\n一、金额保留整数。\n", encoding="gbk")
        result = self.check_full()
        self.assert_problem(result, "来源 layout：rules/layout.md 不是 UTF-8 文本（第 1 行")

    def test_a_register_that_is_not_utf8_is_named(self):
        support.write_text(self.register, json.dumps(support.good_register(), ensure_ascii=False), encoding="gbk")
        result = self.check()
        self.assert_problem(result, "登记表不是 UTF-8 文本")

    def test_a_register_that_is_not_json_or_not_there(self):
        support.write_text(self.register, '{"schema": "conflict-register/1",\n "project": }\n')
        self.assert_problem(self.check(), "登记表不是合法的 JSON（第 2 行")
        self.assert_problem(self.check(path=self.dir / "nope.json"), "找不到登记表")
        self.assert_problem(self.check(path=self.dir), "给的是目录，不是登记表文件")


class Encodings(CheckCase):
    def test_a_register_with_a_bom_passes(self):
        support.write_text(self.register, "﻿" + json.dumps(support.good_register(), ensure_ascii=False))
        result = self.check_full()
        self.assertEqual(result["status"], "OK", result["problems"])

    def test_a_bom_before_a_file_without_marker_keeps_the_digest(self):
        def pin(r):
            r["sources"][2]["sha256"] = support.original_digest(support.LAYOUT)
        support.write_json(self.register, changed(pin))
        support.write_text(self.dir / "rules" / "layout.md", "﻿" + support.LAYOUT)
        result = self.check()
        self.assertEqual(result["status"], "OK", result["problems"])
        self.assertEqual(result["sources"]["digests"]["layout"], support.original_digest(support.LAYOUT))

    def test_a_text_with_a_bom_can_be_quoted_on_line_one(self):
        support.write_text(self.dir / "reports" / "q3-summary.md", "﻿" + support.summary_text())
        result = self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(line=1, quote="# 第三季度")))
        self.assertEqual(result["status"], "OK", result["problems"])

    def test_line_numbers_follow_a_lone_cr(self):
        support.write_text(self.dir / "reports" / "q3-summary.md", support.summary_text().replace("\n", "\r"))
        self.assertEqual(self.check_full()["status"], "OK")
        self.assert_problem(self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(line=4))),
                            "原句不在 q3-summary 第 4 行")

    def test_the_line_of_a_bad_byte_is_counted_like_the_text(self):
        for newline in (b"\n", b"\r\n", b"\r"):
            with self.subTest(newline=newline):
                data = newline.join(["指标,数值".encode(), "活跃用户,1204".encode(), b"\xff\xfe"]) + newline
                (self.dir / "reports" / "q3-metrics.csv").write_bytes(data)
                self.assert_problem(self.check_full(), "q3-metrics.csv 不是 UTF-8 文本（第 3 行")

    def test_a_marker_line_with_spaces_around_it_still_counts(self):
        rules = self.dir / "rules" / "metrics.md"
        support.write_text(rules, "> 另一段加注。\n\n  " + support.MARKER + "  \n" + support.METRICS_BODY)
        self.assertEqual(self.check()["status"], "OK")


class StatusRules(CheckCase):
    def test_an_open_item_with_only_decided_by_is_reported(self):
        result = self.check_full(changed(lambda r: r["items"][0].update(decided_by={"who": "ai", "when": "2026-11-01",
                                                                                     "rule_applied": 4})))
        self.assert_problem(result, "T-01 是 open，却写了 resolution 或 decided_by")

    def test_a_wrong_schema_is_the_only_problem(self):
        result = self.check_full(changed(lambda r: (r.update(schema="conflict-register/2"), r.pop("project"))))
        self.assertEqual(len(result["problems"]), 1, result["problems"])
        self.assert_problem(result, "schema 必须是 conflict-register/1")

    def test_a_register_named_rule_conflicts_is_refused(self):
        # 小说写作工坊的登记表叫 rule-conflicts/1，格式和这里不同（decided_by.who 的取值就不一样），
        # 所以这里另起名 conflict-register/1；拿那种登记表来跑，三个命令都只报 schema 不对，不往下核。
        register = changed(lambda r: r.update(schema="rule-conflicts/1"))
        result = self.check_full(register)
        self.assertEqual(result["problems"], ["schema 必须是 conflict-register/1（现在是 rule-conflicts/1）"])
        for args in (("list", self.register), ("list", self.register, "--markdown"),
                     ("collide", "--register", self.register, "--texts-root", self.dir, "活跃用户")):
            code, out, err = run(*args)
            self.assertEqual(code, 1, (args[0], out[-300:], err[-300:]))
            self.assertNotIn("Traceback", err)
            self.assertIn("schema 必须是 conflict-register/1（现在是 rule-conflicts/1）", out)

    def test_an_exception_is_decided_by_the_principal(self):
        result = self.check_full(changed(lambda r: r["items"][2].update(
            decided_by={"who": "ai", "when": "2026-11-01", "rule_applied": 3})))
        self.assert_problem(result, "T-03 是 exception（委托人明示有意为之的做法），decided_by.who 必须是 principal")

    def test_a_closed_item_that_names_a_decider_is_checked(self):
        result = self.check_full(changed(lambda r: r["items"][3].update(decided_by={"who": "robot"})))
        self.assert_problem(result, "T-04：decided_by.who 必须是 principal 或 ai")
        ok = changed(lambda r: r["items"][3].update(decided_by={"who": "ai", "when": "2026-11-01", "rule_applied": 1}))
        self.assertEqual(self.check_full(ok)["status"], "OK")


class Strength(CheckCase):
    """规则一边可以写 strength：must（必须）或 should（建议）。写了就核，成果一边不写。"""

    def test_a_rule_side_may_say_must_or_should_or_leave_it_out(self):
        for value in ("must", "should", None):
            with self.subTest(value=value):
                result = self.check_full(changed(lambda r: [s.update(strength=value) for s in r["items"][0]["sides"]]))
                self.assertEqual(result["status"], "OK", result["problems"])
                self.assertFalse(any("strength" in w for w in result["warnings"]), result["warnings"])

    def test_any_other_strength_is_reported_with_what_was_written(self):
        # 写错的值照 JSON 的写法列出来，空字符串也看得见。
        for value, shown in (("MUST", '"MUST"'), ("必须", '"必须"'), ("", '""'), ("may", '"may"'), (1, "1"),
                             (True, "true"), (["must"], '["must"]')):
            with self.subTest(value=value):
                result = self.check_full(changed(lambda r: r["items"][0]["sides"][1].update(strength=value)))
                self.assertIn("条目 T-01 第 2 项 sides：strength 只能是 must（必须）或 should（建议），现在是 %s" % shown,
                              result["problems"])
                self.assertEqual(len(result["problems"]), 1, result["problems"])

    def test_strength_is_written_on_the_rule_side_only(self):
        result = self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(strength="must")))
        self.assertEqual(result["problems"],
                         ["条目 T-02 第 2 项 sides：strength 只写在规则一边（source），成果一边（text）不写"])
        # 成果一边写 null，和不写一样。
        result = self.check_full(changed(lambda r: r["items"][1]["sides"][1].update(strength=None)))
        self.assertEqual(result["status"], "OK", result["problems"])


class SourceDetails(CheckCase):
    def test_superseded_by_an_unknown_id_is_named_once(self):
        result = self.check_full(changed(lambda r: r["sources"][1].update(superseded_by="metrics-v9")))
        self.assertEqual(result["problems"], ["来源 metrics-v2：superseded_by 写的 metrics-v9 不在 sources 里"])

    def test_a_missing_superseded_by_is_reported_once(self):
        result = self.check_full(changed(lambda r: r["sources"][1].pop("superseded_by")))
        self.assertEqual(result["problems"], ["来源 metrics-v2 是 superseded，但没写 superseded_by（被哪一份取代）"])

    def test_a_duplicate_key_names_the_object_it_is_in(self):
        text = json.dumps(support.good_register(), ensure_ascii=False)
        text = text.replace('"id": "T-02",', '"id": "T-02", "kind": "conflict",', 1)
        support.write_text(self.register, text)
        self.assert_problem(self.check_full(), "id 为 T-02 的对象里键 kind 出现了两次")

    def test_a_local_source_without_sha256_is_warned(self):
        result = self.check_full()
        self.assertTrue(any(w.startswith("来源 layout 没有记 sha256") for w in result["warnings"]), result["warnings"])
        self.assertFalse(any(w.startswith("来源 metrics-v3 没有记") for w in result["warnings"]), result["warnings"])

    def test_sha256_without_a_local_file_is_warned_and_its_format_checked(self):
        result = self.check_full(changed(lambda r: r["sources"][3].update(sha256="0" * 64)))
        self.assertEqual(result["status"], "OK", result["problems"])
        self.assertTrue(any("来源 finance 写了 sha256，但是外部依据" in w for w in result["warnings"]), result["warnings"])
        self.assert_problem(self.check_full(changed(lambda r: r["sources"][3].update(sha256="xyz"))),
                            "来源 finance：sha256 必须是 64 位十六进制字符")

    def test_unknown_keys_are_warned_with_a_guess(self):
        def typos(r):
            r["sources"][0]["SHA256"] = r["sources"][0].pop("sha256")
            r["items"][1]["resoluton"] = "多写了一个键"
            r["items"][1]["sides"][1]["lines"] = 3
        result = self.check_full(changed(typos))
        self.assertEqual(result["status"], "OK", result["problems"])
        for needle in ("来源 metrics-v3 里有不认识的键 SHA256，程序不读它（是不是 sha256？）",
                       "条目 T-02 里有不认识的键 resoluton，程序不读它（是不是 resolution？）",
                       "条目 T-02 第 2 项 sides 里有不认识的键 lines，程序不读它（是不是 line？）",
                       "来源 metrics-v3 没有记 sha256"):
            self.assertTrue(any(needle in w for w in result["warnings"]), (needle, result["warnings"]))
        # note 在哪个对象里都可以写，不提醒。
        result = self.check_full(changed(lambda r: r["items"][0].update(note="给人看的")))
        self.assertFalse(any("note" in w for w in result["warnings"]), result["warnings"])


class Paths(CheckCase):
    def test_a_path_that_is_a_directory_is_not_called_missing(self):
        target = self.dir / "rules" / "layout.md"
        target.unlink()
        target.mkdir()
        self.assert_problem(self.check(), "来源 layout：rules/layout.md 不是普通文件")
        (self.dir / "reports" / "q3-summary.md").unlink()
        (self.dir / "reports" / "q3-summary.md").mkdir()
        self.assert_problem(self.check_full(), "成果 q3-summary：reports/q3-summary.md 不是普通文件")

    def test_an_absolute_path_has_no_relative_note(self):
        missing = str(self.dir / "elsewhere" / "layout.md")
        result = self.check(register=changed(lambda r: r["sources"][2].update(file=missing)))
        self.assertIn("来源 layout：找不到文件 %s" % missing, result["problems"])

    def test_a_name_too_long_is_reported_and_the_rest_still_checked(self):
        long_name = "rules/" + "a" * 300 + ".md"
        result = self.check_full(changed(lambda r: (r["sources"][2].update(file=long_name),
                                                    r["texts"].update({"q3-summary": "reports/" + "b" * 300}),
                                                    r["items"][0].update(ask=""))))
        # Linux 上报“读不了”（文件名太长）。Windows 可能把这种路径报成找不到
        # （Python 把 Windows 的“文件名超出范围”错误记成 ENOENT），在 Windows 上这样报也算报出来了。
        layout = ["来源 layout：读不了 rules/aaa"]
        summary = ["成果 q3-summary：读不了 reports/bbb"]
        if support.WINDOWS:
            layout.append("来源 layout：找不到文件 rules/aaa")
            summary.append("成果 q3-summary：在 --texts-root 下找不到 reports/bbb")
        for needles in (layout, summary):
            self.assertTrue(any(n in p for n in needles for p in result["problems"]), (needles, result["problems"]))
        self.assert_problem(result, "T-01 是 open，要写 ask")
        self.assertFalse(any("核到一半停了" in p for p in result["problems"]), result["problems"])

    def test_texts_null_counts_as_not_written(self):
        def no_texts(r):
            r["texts"] = None
            r["items"] = [item for item in r["items"] if all("text" not in s for s in item["sides"])]
        result = self.check_full(changed(no_texts))
        self.assertEqual(result["status"], "OK", result["problems"])

    def test_an_empty_texts_root_is_a_usage_error(self):
        code, out, err = run("check", self.register, "--texts-root", " ")
        self.assertEqual(code, 2)
        self.assertIn("--texts-root 不能是空的", err)
        self.assertNotIn("Traceback", err)


class NotStandardJson(CheckCase):
    def test_values_that_standard_json_does_not_have_fail_cleanly(self):
        good = json.dumps(support.good_register(), ensure_ascii=False)
        cases = {
            "NaN": (good.replace('"line": 3,', '"line": NaN,', 1), "登记表里有 NaN"),
            "Infinity": (good.replace('"line": 3,', '"line": Infinity,', 1), "登记表里有 Infinity"),
            "-Infinity": (good.replace('"line": 3,', '"line": -Infinity,', 1), "登记表里有 -Infinity"),
            "1e400": (good.replace('"line": 3,', '"line": 1e400,', 1), "超出范围的数"),
            "lone surrogate in a value": (good.replace('"id": "T-02"', '"id": "T-\\udc00"', 1), "不成对的"),
            "lone surrogate in a key": (good.replace('"texts": {', '"texts": {"x\\ud800": "a.md", ', 1), "不成对的"),
        }
        for name, (text, needle) in cases.items():
            with self.subTest(name=name):
                self.assertNotEqual(text, good)
                support.write_text(self.register, text)
                self.assert_problem(self.check_full(), needle)
                for args in (("list", self.register, "--status", "all"),
                             ("list", self.register, "--status", "all", "--markdown"),
                             ("collide", "--register", self.register, "--texts-root", self.dir, "活跃用户")):
                    code, out, err = run(*args)
                    self.assertEqual(code, 1, (args[0], out[-200:], err[-300:]))
                    self.assertNotIn("Traceback", err)
                    json.loads(out)


if __name__ == "__main__":
    unittest.main()
