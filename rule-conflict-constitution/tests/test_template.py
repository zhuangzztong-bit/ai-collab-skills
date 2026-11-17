"""templates/conflict-register.json：格式对，配上它点名的文件能通过 check。"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import run  # noqa: E402


def files_from_register(folder, register):
    """照登记表自己引的原句，造出它点名的文件：来源文件里有每句原句，成果文件的那一行有那句原话。"""
    folder = Path(folder)
    quotes, lines = {}, {}
    for item in register["items"]:
        for side in item["sides"]:
            if "source" in side and side.get("quote"):
                quotes.setdefault(side["source"], []).append(side["quote"])
            elif "text" in side:
                lines.setdefault(side["text"], {})[side["line"]] = side["quote"]
    for source in register["sources"]:
        if source.get("file") and source.get("external") is not True:
            support.write_text(folder / source["file"], "\n\n".join(quotes.get(source["id"], ["（空）"])) + "\n")
    for tid, rel in register["texts"].items():
        wanted = lines.get(tid, {})
        body = [wanted.get(n, "") for n in range(1, max(wanted, default=1) + 1)]
        support.write_text(folder / rel, "\n".join(body) + "\n")


class Template(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.register = json.loads(support.TEMPLATE.read_text(encoding="utf-8"))

    def test_shape(self):
        self.assertEqual(self.register["schema"], "conflict-register/1")
        self.assertTrue(self.register["note"].strip())
        self.assertIn("conflict-register/1", self.register["note"])
        for marker in (support.MARKER, support.MARKER_EN):
            self.assertIn(marker, self.register["note"])
        statuses = {item["status"] for item in self.register["items"]}
        self.assertIn("open", statuses)
        self.assertIn("decided", statuses)
        who = {item["decided_by"]["who"] for item in self.register["items"] if item["status"] == "decided"}
        self.assertEqual(who, {"principal", "ai"})

    def test_it_shows_where_to_write_how_strong_a_rule_is(self):
        sides = [side for item in self.register["items"] for side in item["sides"] if "strength" in side]
        self.assertTrue(sides)
        for side in sides:
            self.assertIn(side["strength"], ("must", "should"))
            self.assertIn("source", side)   # 只写在规则一边
        for word in ("strength", "must", "should"):
            self.assertIn(word, self.register["note"])

    def test_it_passes_check_once_the_files_it_names_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "conflict-register.json"
            path.write_bytes(support.TEMPLATE.read_bytes())
            files_from_register(tmp, self.register)
            code, out, err = run("check", path, "--texts-root", tmp)
            result = json.loads(out)
            self.assertEqual((code, result["status"]), (0, "OK"), result["problems"])
            # 只建了文件、不改模板：模板里没有钉死的 sha256，否则这一步过不了。
            self.assertTrue(result["texts_checked"])


if __name__ == "__main__":
    unittest.main()
