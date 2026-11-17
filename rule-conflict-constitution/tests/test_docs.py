"""文档、模板和脚本里的几处说法前后一致：登记表的 schema 名、原文标记的两种写法。

只读几处固定位置上跟着发布附件走的文件（.github/、docs/releases/ 这类不进附件的不读），解压出来的附件里也能跑。
工作树里另外放的目录（比如照例子说明复制出来的一份例子，或者自己项目的文件）不读。
"""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402

EXAMPLE_DATA = support.EXAMPLES / "help-center"
SOURCE_NOTES = {support.REPO / "docs" / "source.md", support.REPO / "en" / "docs" / "source.md"}
# 给人看的文件（文档、模板、脚本）放在这几处。docs/releases/ 不在 docs/*.md 里：发布说明只在仓库里，不进附件。
# examples/ 下只看 examples/README.md：例子的规则文件本身带着标记行，那是数据，不是讲标记的文字。
SHIPPED = ("README.md", "README.en.md", "CHANGELOG.md", "CONSTITUTION.md", "CARD.md", "docs/*.md", "en/**/*.md",
           "templates/*.json", "scripts/*.py", "examples/README.md")


def shipped_files(*suffixes, root=support.REPO):
    """root 下 SHIPPED 列的文件里，后缀是 suffixes 之一的，按路径排好。"""
    found = set()
    for pattern in SHIPPED:
        found.update(path for path in root.glob(pattern) if path.is_file() and path.suffix in suffixes)
    return sorted(found)


class Wording(unittest.TestCase):
    def test_the_old_schema_name_is_only_in_the_source_notes(self):
        # 工坊的登记表叫 rule-conflicts/1；这里格式不同，另起名 conflict-register/1。旧名只在来源说明里提一次。
        files = shipped_files(".md", ".json", ".py")
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(support.REPO))):
                if path in SOURCE_NOTES:
                    self.assertIn("rule-conflicts/1", text)
                    self.assertIn("conflict-register/1", text)
                else:
                    self.assertNotIn("rule-conflicts/1", text)
        register = (EXAMPLE_DATA / "conflict-register.json").read_text(encoding="utf-8")
        self.assertIn('"schema": "conflict-register/1"', register)

    def test_every_page_that_names_the_marker_names_both_spellings(self):
        named = 0
        for path in shipped_files(".md", ".json", ".py"):
            text = path.read_text(encoding="utf-8")
            if support.MARKER in text or support.MARKER_EN in text:
                named += 1
                with self.subTest(path=str(path.relative_to(support.REPO))):
                    self.assertIn(support.MARKER, text)
                    self.assertIn(support.MARKER_EN, text)
        self.assertGreaterEqual(named, 8)

    def test_other_folders_in_the_working_tree_are_not_read(self):
        # 照 examples/README.md 复制一份例子放在 examples/ 下，或者把自己项目的文件放进仓库目录，
        # 这些文件里的标记行是数据，只写了中文写法也不能让这里的测试失败。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("docs/usage.md", "examples/README.md", "examples/hc5/rules/writing-guide.md",
                         "my-project/rules/guide.md", "docs/releases/v9.md", "tests/notes.md"):
                support.write_text(root / name, support.MARKER + "\n")
            found = [path.relative_to(root).as_posix() for path in shipped_files(".md", root=root)]
        self.assertEqual(found, ["docs/usage.md", "examples/README.md"])

    def test_the_docs_say_the_first_marker_counts(self):
        for name, needle in (("docs/conflict-resolution.md", "以文件里第一处出现的那一行为准"),
                             ("en/docs/conflict-resolution.md", "the first one in the file counts")):
            with self.subTest(name=name):
                self.assertIn(needle, (support.REPO / name).read_text(encoding="utf-8"))

    def test_the_field_table_explains_strength(self):
        doc = (support.REPO / "docs" / "conflict-resolution.md").read_text(encoding="utf-8")
        for needle in ("| 规则 | `strength` |", "`must`", "`should`"):
            self.assertIn(needle, doc)


class CardAndSteps(unittest.TestCase):
    def test_the_card_is_under_5000_bytes(self):
        # 中英文的首页和“怎么用”都说卡片不到 5000 字节，可以整页贴进 AI 的项目指令。
        # 按 LF 换行量：Windows 上检出成 CRLF 时每行多一个字节，贴进 AI 的内容并没有变多
        # （2026-11-15 第一次在 GitHub 的 Windows 上跑 CI 时，就是这样多出了 47、49 个字节）。
        for name in ("CARD.md", "en/CARD.md"):
            with self.subTest(name=name):
                data = (support.REPO / name).read_bytes().replace(b"\r\n", b"\n")
                self.assertLess(len(data), 5000)

    def test_the_five_steps_keep_their_numbers(self):
        # 登记表里 AI 定的条目写 rule_applied 1 至 4，第 5 步只能由委托人定；脚本认的是这个编号。
        steps = ("委托人最新的明确决定", "核实过的规定胜过没核实的描述", "专门的胜过通用的", "同样具体的，日期新的胜过旧的",
                 "还定不了的，两条都不执行")
        for name in ("CONSTITUTION.md", "CARD.md"):
            text = (support.REPO / name).read_text(encoding="utf-8")
            section = text.split("同一层之内", 1)[1]
            with self.subTest(name=name):
                for number, step in enumerate(steps, 1):
                    self.assertIn("\n%d. **%s" % (number, step), section)


if __name__ == "__main__":
    unittest.main()
