"""测试共用的东西：脚本的位置、运行脚本、一套测试用的小项目。

测试用的场景（一个小团队的季度数据报表）是专为测试写的，和 examples/ 里的例子不同。
所有文件按字节写出，换行固定为 LF，不受运行平台影响。
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "conflict_register.py"
TEMPLATE = REPO / "templates" / "conflict-register.json"
EXAMPLES = REPO / "examples"
MARKER = "<!-- 原文开始 -->"
MARKER_EN = "<!-- original text begins -->"
SCHEMA = "conflict-register/1"
WINDOWS = os.name == "nt"


def run(*args, env=None):
    """用当前的 Python 以 -I -B 运行脚本，返回 (退出码, 标准输出, 标准错误)。

    Windows 上，Python 往管道写标准输出和标准错误时会把 \\n 换成 \\r\\n（脚本没有改这一点）；
    这里换回 \\n，好和文档里贴的输出逐字比较。别的平台照原样返回。"""
    proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, env=env)
    out, err = proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8", "replace")
    if WINDOWS:
        out, err = out.replace("\r\n", "\n"), err.replace("\r\n", "\n")
    return proc.returncode, out, err


def write_text(path, text, encoding="utf-8"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode(encoding))
    return path


def write_json(path, value):
    return write_text(path, json.dumps(value, ensure_ascii=False, indent=1) + "\n")


def original_digest(text):
    """测试自己按文档写的规则算一遍哈希：第一处标记行（中文或英文写法）之后的文字（没有标记就是全文），UTF-8，LF。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if line.strip() in (MARKER, MARKER_EN):
            text = "\n".join(lines[number + 1:])
            break
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


METRICS_NOTE = "> AI 的加注：数据组给的口径说明，下面照录原文。\n\n"
METRICS_BODY = ("# 指标口径（第三版）\n\n"
                "一、“活跃用户”指最近 30 天内登录过的用户。\n\n"
                "二、金额一律保留两位小数。\n\n"
                "三、现状：第三季度报表已经按本版口径重算过。\n")
METRICS = METRICS_NOTE + MARKER + "\n" + METRICS_BODY
METRICS_V2 = "# 指标口径（第二版）\n\n一、“活跃用户”指最近 7 天内登录过的用户。\n"
LAYOUT = "# 报表排版规范\n\n一、金额保留整数，单位写“元”。\n\n二、表格第一列写指标名。\n"


def summary_text():
    lines = ["# 第三季度报表摘要"] + [""] * 29
    lines[2] = "本季度活跃用户 1,204 人（按 7 天内登录计）。"
    lines[4] = "本季度收入 85,320 元。"
    lines[8] = "表中“留存”指次月仍登录的比例。"
    return "\n".join(lines) + "\n"   # 30 行


CSV = "指标,数值\n活跃用户,1204\n收入,85320.00\n留存,0.41\n"


def good_register():
    return {
        "schema": SCHEMA,
        "project": "季度报表（测试）",
        "updated": "2026-11-01",
        "sources": [
            {"id": "metrics-v3", "label": "口径第三版", "title": "数据组的指标口径（第三版）", "file": "rules/metrics.md",
             "version": "第三版", "date": "2026-10-01", "status": "in_force",
             "sha256": original_digest(METRICS)},
            {"id": "metrics-v2", "title": "数据组的指标口径（第二版）", "file": "rules/old/metrics-v2.md",
             "version": "第二版", "date": "2026-07-01", "status": "superseded", "superseded_by": "metrics-v3"},
            {"id": "layout", "title": "报表排版规范", "file": "rules/layout.md", "version": "1", "date": "2026-09-01",
             "status": "in_force"},
            {"id": "finance", "title": "财务部的金额书写规定", "version": "2025", "date": "2025-01-01",
             "status": "in_force", "external": True},
        ],
        "texts": {"q3-summary": "reports/q3-summary.md", "q3-metrics": "reports/q3-metrics.csv"},
        "items": [
            {"id": "T-01", "kind": "conflict", "title": "金额保留几位",
             "sides": [{"source": "metrics-v3", "where": "第二条", "quote": "金额一律保留两位小数"},
                       {"source": "layout", "where": "第一条", "quote": "金额保留整数"}],
             "proposal": "两份同样具体、谁也不是谁的新版本，交委托人定。",
             "status": "open", "ask": "金额保留两位小数还是整数？",
             "meanwhile": "已采纳的报表不动；新表里的金额先照原始数据列出。", "since": "2026-10-20"},
            {"id": "T-02", "kind": "mismatch", "title": "口径说已经重算，摘要还按 7 天计",
             "sides": [{"source": "metrics-v3", "where": "第三条", "quote": "第三季度报表已经按本版口径重算过"},
                       {"text": "q3-summary", "line": 3, "quote": "按 7 天内登录计"}],
             "status": "decided", "resolution": "“已经重算过”是描述，和已采纳的摘要对不上；摘要不动，差异列给委托人。",
             "decided_by": {"who": "ai", "when": "2026-11-01", "rule_applied": 2}},
            {"id": "T-03", "kind": "exception", "title": "CSV 里的金额照原样保留两位",
             "sides": [{"text": "q3-metrics", "line": 3, "quote": "85320.00"}],
             "status": "decided", "resolution": "这一处不再报。",
             "decided_by": {"who": "principal", "when": "2026-11-01", "words": "CSV 是给系统导入的，照原样。",
                            "source": "委托人 2026-11-01 的邮件"}},
            {"id": "T-04", "kind": "conflict", "title": "旧口径和财务规定对活跃用户的说法不同",
             "sides": [{"source": "metrics-v2", "where": "第一条", "quote": "最近 7 天内登录过的用户"},
                       {"source": "finance", "where": "附录", "quote": "活跃用户按 30 天计"}],
             "status": "closed", "resolution": "第三版已经改成 30 天，这一条不再成立。"},
        ],
    }


def make_project(folder, register=None):
    """把测试项目的全部文件写到 folder 下，返回登记表的路径。"""
    folder = Path(folder)
    write_text(folder / "rules" / "metrics.md", METRICS)
    write_text(folder / "rules" / "old" / "metrics-v2.md", METRICS_V2)
    write_text(folder / "rules" / "layout.md", LAYOUT)
    write_text(folder / "reports" / "q3-summary.md", summary_text())
    write_text(folder / "reports" / "q3-metrics.csv", CSV)
    return write_json(folder / "register.json", good_register() if register is None else register)


def changed(change):
    """good_register() 的一份深拷贝，交给 change(register) 改。"""
    register = copy.deepcopy(good_register())
    change(register)
    return register


def gbk_console_env():
    env = dict(os.environ, PYTHONIOENCODING="gbk")
    return env
