"""examples/：例子能跑通，README 里贴的输出就是实际运行的输出。"""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import run  # noqa: E402

EXAMPLE = support.EXAMPLES / "help-center"
REGISTER = EXAMPLE / "conflict-register.json"
README = support.EXAMPLES / "README.md"
DOC = support.REPO / "docs" / "conflict-resolution.md"
EN_DOC = support.REPO / "en" / "docs" / "conflict-resolution.md"


def blocks(text):
    """README 里每个 ``` 代码块的内容。"""
    found, inside, current = [], False, []
    for line in text.split("\n"):
        if line.startswith("```"):
            if inside:
                found.append("\n".join(current) + "\n")
                current = []
            inside = not inside
        elif inside:
            current.append(line)
    return found


class Example(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.blocks = blocks(cls.readme)

    def assert_in_readme(self, output):
        self.assertIn(output, self.blocks, "README 里没有贴这段输出：\n" + output)

    def test_check_passes_and_covers_every_kind(self):
        code, out, err = run("check", REGISTER, "--texts-root", EXAMPLE)
        result = json.loads(out)
        self.assertEqual((code, result["status"]), (0, "OK"), result["problems"])
        self.assertTrue(result["texts_checked"])
        self.assertEqual(result["sources"]["stale"], [])
        for kind, count in result["kinds"].items():
            self.assertGreaterEqual(count, 1, kind)
        self.assertGreaterEqual(result["counts"]["open"], 1)
        self.assert_in_readme(out)

    def test_list_outputs_are_the_ones_in_the_readme(self):
        code, out, err = run("list", REGISTER, "--status", "open", "--markdown")
        self.assertEqual(code, 0, err)
        self.assert_in_readme(out)
        self.assertIn("还没定", out)
        # docs/conflict-resolution.md 也贴了这张核对单，要和实际输出一字不差。
        self.assertIn(out, blocks(DOC.read_text(encoding="utf-8")))

    def test_the_example_records_how_strong_the_rules_in_a_conflict_are(self):
        register = json.loads(REGISTER.read_text(encoding="utf-8"))
        sides = [side for item in register["items"] for side in item["sides"] if "strength" in side]
        self.assertTrue(sides)
        self.assertTrue(all("source" in side and side["strength"] in ("must", "should") for side in sides), sides)
        code, out, err = run("list", REGISTER, "--status", "open", "--markdown")
        self.assertIn("（必须）", out)

    def test_collide_outputs_are_the_ones_in_the_readme(self):
        code, out, err = run("collide", "--register", REGISTER, "--texts-root", EXAMPLE, "标签", "收藏")
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertTrue(result["complete"])
        self.assertTrue(result["words"]["标签"])
        self.assertEqual(result["words"]["收藏"], [])
        self.assert_in_readme(out)

    def test_the_failures_shown_in_the_readme_are_real(self):
        code, out, err = run("collide", "--register", REGISTER, "--texts-root", EXAMPLE / "texts", "标签")
        self.assertEqual(code, 1, err)
        self.assertFalse(json.loads(out)["complete"])
        self.assert_in_readme(out)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "help-center"
            shutil.copytree(str(EXAMPLE), str(copy))
            register = copy / "conflict-register.json"
            text = register.read_text(encoding="utf-8")
            old = '{"text": "faq-account", "line": 7,'
            self.assertEqual(text.count(old), 1)
            register.write_bytes(text.replace(old, old.replace("7", "8")).encode("utf-8"))
            code, out, err = run("check", register, "--texts-root", copy)
        self.assertEqual(code, 1, err)
        self.assertEqual(json.loads(out)["problems"], ["条目 HC-02 第 2 项 sides：原句不在 faq-account 第 8 行"])
        self.assert_in_readme(out)

    def test_the_changed_source_shown_in_the_docs_is_real(self):
        # docs/conflict-resolution.md 写明了在哪里加了哪几个字，并贴了 check 报的那一句；照着改一遍，报的要一字不差。
        doc = DOC.read_text(encoding="utf-8")
        self.assertIn("的句号前加了“，语气亲切”几个字", doc)
        [shown] = [block for block in blocks(doc) if block.startswith("来源 writing-guide-v2：")]
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "help-center"
            shutil.copytree(str(EXAMPLE), str(copy))
            rules = copy / "rules" / "writing-guide.md"
            text = rules.read_text(encoding="utf-8")
            old = "2. 退款类文章也用“你”。"
            self.assertEqual(text.count(old), 1)
            rules.write_bytes(text.replace(old, "2. 退款类文章也用“你”，语气亲切。").encode("utf-8"))
            code, out, err = run("check", copy / "conflict-register.json", "--texts-root", copy)
        self.assertEqual(code, 1, err)
        self.assertEqual(json.loads(out)["problems"], [shown.rstrip("\n")])
        self.assertIn(shown, blocks(EN_DOC.read_text(encoding="utf-8")))

    def test_the_readme_shows_the_commands_it_ran(self):
        for command in ("check conflict-register.json --texts-root .",
                        "list conflict-register.json --status open --markdown",
                        "collide --register conflict-register.json --texts-root . 标签 收藏",
                        "collide --register conflict-register.json --texts-root texts 标签"):
            self.assertIn(command, self.readme)


if __name__ == "__main__":
    unittest.main()
