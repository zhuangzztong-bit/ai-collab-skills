#!/usr/bin/env python3
"""冲突登记表（conflict-register/1）的核对工具。只用 Python 标准库，Python 3.9 起能跑。

登记表是一个 JSON 文件，记三样东西：
  sources  规则文件：现行的（in_force）、被取代的（superseded）、委托人还没定的（pending）；
  texts    已采纳的成果：委托人采纳过的文档、代码、数据等文件，成果 id 对相对路径；
  items    每条一个冲突，列出两边的原句和位置，写明状态（open、decided、closed）。

命令：
  check   REGISTER [--texts-root DIR]
          核对登记表的结构；来源文件的版本（登记了 sha256 的，核文件现在的摘要）；
          来源一边的原句在不在那份文件里；规则一边写了 strength 的，只能是 must（必须）或 should（建议）。
          给了 --texts-root，再核成果一边的行号和原句。
          warnings 里提醒没有核的地方和可能写错的地方（不认识的键、没记 sha256 的本地来源）。
  list    REGISTER [--status open|decided|closed|all] [--markdown]
          列出条目，默认列还没定的（open）。--markdown 出一张给委托人看的核对单，
          规则一边写了 strength 的标出“（必须）”“（建议）”（写的不是 must、should 的，照 JSON 的写法标出来，
          提醒先跑 check），值里的换行在核对单里换成“／”。
  collide --register REGISTER --texts-root DIR [--ignore-case] WORD [WORD ...]
          列出每个词在已采纳的成果里出现的行，看新叫法是不是已经指着别的东西。
          按字面找，区分大小写（--ignore-case 不区分），不认词形变化和近义词。

路径：来源的 file 相对登记表所在的目录；texts 的路径相对 --texts-root。
路径不限在这两个目录之内：写成绝对路径、../ 开头都照读。拿别人给的登记表来跑之前，
先看一眼它点名了哪些文件：collide 会把命中的整行写进输出，check 会给出文件的摘要。
文本按 UTF-8 读：开头的 BOM 不算，CRLF 和单独的 CR 都当一个换行；行号从 1 数起，
换页符、U+2028 这类字符不算换行。来源文件里有一行去掉首尾空白后正好是“<!-- 原文开始 -->”
或英文写法“<!-- original text begins -->”时，这一行之后才是原文：sha256 只算原文，原句也只在原文里找。
两种写法都出现时，以文件里第一处出现的那一行为准，后面那一行算原文的一部分。

退出码：
  0  check 没发现问题（warnings 只是提醒，不影响退出码）；list 列出来了；
     collide 每份登记的成果都读到了（有没有命中都是 0）。
  1  check 发现了问题；登记表找不到、不是 UTF-8、不是标准的 JSON 或格式不对；
     collide 有成果找不到、读不了，或登记表没列成果（结果里 complete 是 false）。
  2  命令用法不对。

它只核对登记表自己写的话和它点名的文件对不对得上。规则写得好不好、该不该留、
两条规则哪条更对、委托人该怎么定，它判断不了；成果本身写得对不对，它也不判。
"""

import argparse
import codecs
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import sys

SCHEMA = "conflict-register/1"
MARKERS = ("<!-- 原文开始 -->", "<!-- original text begins -->")   # 原文标记的中文、英文写法
SOURCE_STATUS = ("in_force", "superseded", "pending")
KINDS = ("conflict", "mismatch", "collision", "stale", "exception")
ITEM_STATUS = ("open", "decided", "closed")
DECIDERS = ("principal", "ai")
STRENGTHS = ("must", "should")   # 规则一边的强弱：must 是必须，should 是建议（“尽量”“一般”这类也算）
AI_STEPS = (1, 2, 3, 4)  # 裁决顺序的第 1 至 4 步 AI 可以自己用；第 5 步（还定不了）只能交委托人定
HEX64 = re.compile(r"[0-9a-fA-F]{64}")

# 各个对象里认得的键。别的键程序不读，check 在 warnings 里提醒（多半是拼错了）。note 在哪里都可以写。
TOP_KEYS = ("schema", "project", "updated", "note", "sources", "texts", "items")
SOURCE_KEYS = ("id", "title", "version", "date", "status", "label", "file", "sha256", "superseded_by", "external",
               "note")
ITEM_KEYS = ("id", "title", "kind", "sides", "status", "ask", "meanwhile", "since", "proposal", "resolution",
             "decided_by", "note")
SIDE_KEYS = ("source", "where", "quote", "strength", "text", "line", "note")
DECIDED_KEYS = ("who", "when", "words", "source", "rule_applied", "note")

KIND_LABEL = {"conflict": "规则打架", "mismatch": "描述和成果对不上", "collision": "新叫法撞上已有用法",
              "stale": "同一份文件前后不一致", "exception": "登记过的例外"}
STATUS_LABEL = {"open": "还没定", "decided": "已定", "closed": "已关闭"}
HEADING = {"open": "还没定的条目", "decided": "已定的条目", "closed": "已关闭的条目", "all": "全部条目"}
STRENGTH_LABEL = {"must": "必须", "should": "建议"}
SHAPE_ERRORS = (TypeError, AttributeError, KeyError, ValueError, IndexError, OSError, RecursionError)


class Unreadable(Exception):
    """文件或登记表读不了；str(error) 是给人看的原因。"""


def text_of(value):
    return isinstance(value, str) and bool(value.strip())


def shown(value):
    """放进出错信息里的值：字符串原样，别的按 JSON 写。"""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def as_text(value):
    return "" if value is None else shown(value)


def encodable(value):
    """字符串能不能按 UTF-8 写出来（不成对的代理项，比如 \\ud800 或命令行里解不了的字节，写不出来）。"""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


# --- 读文件 -----------------------------------------------------------------------------------------------------

def decode(data):
    """字节按 UTF-8 解成文本：开头的 BOM 去掉，CRLF 和单独的 CR 都换成 LF。不是 UTF-8 的抛 Unreadable。"""
    skip = len(codecs.BOM_UTF8) if data.startswith(codecs.BOM_UTF8) else 0
    try:
        text = data[skip:].decode("utf-8")
    except UnicodeDecodeError as error:
        offset = skip + error.start
        before = data[skip:offset].replace(b"\r\n", b"\n").replace(b"\r", b"\n")   # 和读文本时一样数行
        raise Unreadable("不是 UTF-8 文本（第 %d 行有不能按 UTF-8 读的字节，从文件的第 %d 个字节起）"
                         % (before.count(b"\n") + 1, offset + 1))
    return text.replace("\r\n", "\n").replace("\r", "\n")


def path_kind(path):
    """路径指着什么：返回 (种类, 原因)，种类是 file、dir、other（设备、管道这类）、missing 或 error。
    stat 出错（文件名太长、没有权限这类）不抛异常，原因放在第二项。"""
    try:
        mode = Path(path).stat().st_mode
    except (FileNotFoundError, NotADirectoryError):
        return "missing", ""
    except OSError as error:
        return "error", error.strerror or str(error)
    except ValueError as error:   # 路径里有 NUL 这类字符
        return "error", str(error)
    if stat.S_ISREG(mode):
        return "file", ""
    if stat.S_ISDIR(mode):
        return "dir", ""
    return "other", ""


def read_text(path):
    try:
        data = Path(path).read_bytes()
    except OSError as error:
        raise Unreadable("读不出来（%s）" % (error.strerror or error))
    return decode(data)


def split_lines(text):
    """按 LF 分行（decode 已经把 CRLF、CR 换成 LF）；末尾的换行不多算一行。"""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def original_part(text):
    """有标记行（MARKERS 里的任一种写法，去掉首尾空白后整行正好是它）时，取第一处标记行之后的文字；没有就是全文。"""
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if line.strip() in MARKERS:
            return "\n".join(lines[number + 1:])
    return text


def original_sha256(original):
    """原文（original_part 取出的文字）的 SHA-256，按 UTF-8 编码后算。

    文字是 decode 读出来的，所以 Windows 上另存的一份（CRLF、带 BOM）和原来是同一个摘要；
    标记之前的加注改了，摘要也不变。对一个 UTF-8、LF、没有 BOM、没有标记的文件，
    这就是文件字节的 SHA-256（和 sha256sum 算的一样）。"""
    return hashlib.sha256(original.encode("utf-8")).hexdigest()


def not_standard(value):
    """登记表读出来以后再查一遍：不成对的代理项、溢出成无穷大的数。有就返回说明，没有返回 None。
    用一个栈逐层查，不用递归，嵌套得再深也不会出错。"""
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if not encodable(current):
                return "有不成对的 \\uD800 这类转义，不是有效的 Unicode 文本"
        elif isinstance(current, float) and not math.isfinite(current):
            return "有超出范围的数（比如 1e400），标准 JSON 读不出这样的数"
    return None


def load_register(path):
    """读登记表，返回 (登记表, 重复出现的键)。读不了抛 Unreadable，原因是整句。"""
    path = Path(path)
    kind, reason = path_kind(path)
    if kind == "dir":
        raise Unreadable("给的是目录，不是登记表文件：%s" % path)
    if kind == "missing":
        raise Unreadable("找不到登记表：%s" % path)
    if kind == "other":
        raise Unreadable("登记表不是普通文件：%s" % path)
    if kind == "error":
        raise Unreadable("读不了登记表（%s）：%s" % (reason, path))
    try:
        text = read_text(path)
    except Unreadable as error:
        raise Unreadable("登记表%s：%s；另存为 UTF-8 再试" % (error, path))
    duplicates = []

    def pairs(items):
        value, repeated = {}, []
        for key, item in items:
            if key in value and key not in repeated:
                repeated.append(key)
            value[key] = item
        owner = value.get("id")
        for key in repeated:
            where = "id 为 %s 的对象" % owner if isinstance(owner, str) else "同一个对象"
            duplicates.append("%s里键 %s 出现了两次（JSON 只留最后一个）" % (where, key))
        return value

    def constant(name):
        raise Unreadable("登记表里有 %s，标准 JSON 没有这样的值：%s" % (name, path))

    try:
        register = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError as error:
        raise Unreadable("登记表不是合法的 JSON（第 %d 行第 %d 列：%s）：%s" % (error.lineno, error.colno, error.msg, path))
    except RecursionError:
        raise Unreadable("登记表嵌套得太深，读不了：%s" % path)
    why = not_standard(register)
    if why:
        raise Unreadable("登记表里%s：%s" % (why, path))
    return register, duplicates


def load_for_reading(path):
    """list 和 collide 用：读登记表，核最外层和 schema。不对就抛 Unreadable。"""
    register, _ = load_register(path)
    if not isinstance(register, dict):
        raise Unreadable("登记表最外层必须是一个 JSON 对象：%s" % path)
    if register.get("schema") != SCHEMA:
        raise Unreadable("schema 必须是 %s（现在是 %s）：%s" % (SCHEMA, shown(register.get("schema")), path))
    return register


# --- check ------------------------------------------------------------------------------------------------------

def empty_result(problems):
    return {"status": "FAIL", "problems": problems, "warnings": [], "counts": {}, "kinds": {}, "sources": {},
            "texts_checked": False}


def check(register_path, texts_root=None):
    """核对登记表，返回 {"status": "OK" 或 "FAIL", "problems", "warnings", "counts", "kinds", "sources",
    "texts_checked"}。登记表的形状再怪也只给出信息，不抛异常。"""
    try:
        return _check(Path(register_path), texts_root)
    except Unreadable as error:
        return empty_result([str(error)])
    except SHAPE_ERRORS as error:
        return empty_result(["登记表的格式不对，核到一半停了（%s: %s）" % (type(error).__name__, error)])


def unknown_keys(entry, known, label):
    """entry 里程序不认识的键，各写一句提醒；大小写不同或拼得很像的，点出可能是哪个键。"""
    notes = []
    for key in entry:
        if key in known:
            continue
        guess = [name for name in known if isinstance(key, str) and name.casefold() == key.casefold()]
        guess = guess or difflib.get_close_matches(key, known, n=1, cutoff=0.75)
        hint = "（是不是 %s？）" % guess[0] if guess else ""
        notes.append("%s里有不认识的键 %s，程序不读它%s" % (label, key, hint))
    return notes


def missing_file(label, kind, reason, name, relative_to):
    """文件不在、不是普通文件或读不了时的一句话。绝对路径不加“路径相对……”的说明。"""
    where = "" if Path(name).is_absolute() else "（路径相对%s）" % relative_to
    if kind == "missing":
        return "%s：找不到文件 %s%s" % (label, name, where)
    if kind == "error":
        return "%s：读不了 %s（%s）" % (label, name, reason)
    return "%s：%s 不是普通文件（是目录、设备或管道这类）" % (label, name)


def _check(register_path, texts_root):
    problems, warnings = [], []

    def need(condition, message):
        if not condition:
            problems.append(message)
        return condition

    register, duplicates = load_register(register_path)
    problems.extend(duplicates)
    if not isinstance(register, dict):
        return empty_result(problems + ["登记表最外层必须是一个 JSON 对象"])
    if not need(register.get("schema") == SCHEMA,
                "schema 必须是 %s（现在是 %s）" % (SCHEMA, shown(register.get("schema")))):
        return empty_result(problems)
    warnings.extend(unknown_keys(register, TOP_KEYS, "最外层"))
    need(text_of(register.get("project")), "project 要写项目名称")
    need(text_of(register.get("updated")), "updated 要写最近一次核对的日期")

    # --- sources：规则文件
    sources = register.get("sources")
    need(isinstance(sources, list) and sources, "sources 必须是非空列表：每份规则文件一项")
    by_id, source_text, no_file, stale, digests = {}, {}, {}, [], {}
    for entry in sources if isinstance(sources, list) else []:
        if not need(isinstance(entry, dict) and text_of(entry.get("id")), "每个来源都要有 id（非空字符串）"):
            continue
        sid = entry["id"]
        if not need(sid not in by_id, "来源 id %s 出现了两次" % sid):
            continue
        by_id[sid] = entry
        warnings.extend(unknown_keys(entry, SOURCE_KEYS, "来源 %s " % sid))
        for key in ("title", "version", "date"):
            need(text_of(entry.get(key)), "来源 %s 缺 %s" % (sid, key))
        for key in ("file", "sha256", "superseded_by", "label"):
            need(entry.get(key) is None or isinstance(entry[key], str),
                 "来源 %s：%s 必须是字符串（或不写）" % (sid, key))
        # external 会关掉文件、哈希和原句的核对，所以只认 JSON 的 true；写错了的照本地文件核。
        external = entry.get("external")
        need(external is None or isinstance(external, bool),
             "来源 %s：external 只能是 JSON 的 true 或 false（写 null 或不写算 false），现在是 %s"
             % (sid, json.dumps(external, ensure_ascii=False)))
        status = entry.get("status")
        need(isinstance(status, str) and status in SOURCE_STATUS,
             "来源 %s：status 必须是 %s 之一" % (sid, "、".join(SOURCE_STATUS)))
        if status == "superseded":
            need(text_of(entry.get("superseded_by")), "来源 %s 是 superseded，但没写 superseded_by（被哪一份取代）" % sid)
        else:
            need(not entry.get("superseded_by"), "来源 %s 是 %s，却写了 superseded_by" % (sid, shown(status)))
        registered = entry.get("sha256")
        pinned = isinstance(registered, str) and bool(HEX64.fullmatch(registered))
        file_name = entry.get("file")
        if external is True or not text_of(file_name):
            no_file[sid] = "external" if external is True else "no_file"
            if isinstance(registered, str):
                if not pinned:
                    problems.append("来源 %s：sha256 必须是 64 位十六进制字符" % sid)
                why = "是外部依据（external）" if external is True else "没写 file"
                warnings.append("来源 %s 写了 sha256，但%s，没有本地文件可核，sha256 没有核" % (sid, why))
            if status == "in_force" and external is not True:
                need(False, "来源 %s 是 in_force 且不是 external，要写 file（相对登记表所在目录的路径）" % sid)
            continue
        location = register_path.parent / file_name
        kind, reason = path_kind(location)
        if not need(kind == "file", missing_file("来源 %s" % sid, kind, reason, file_name, "登记表所在的目录")):
            continue
        try:
            text = read_text(location)
        except Unreadable as error:
            problems.append("来源 %s：%s %s；另存为 UTF-8 再核" % (sid, file_name, error))
            continue
        source_text[sid] = original_part(text)
        actual = original_sha256(source_text[sid])
        digests[sid] = actual
        if isinstance(registered, str):
            if not pinned:
                problems.append("来源 %s：sha256 必须是 64 位十六进制字符（%s 现在的摘要是 %s，核过原文后可以照抄）"
                                % (sid, file_name, actual))
            elif registered.lower() != actual:
                problems.append("来源 %s：%s 在登记之后改过（登记的 sha256 是 %s，现在是 %s）；"
                                "先重核引用它的条目，再更新 sha256" % (sid, file_name, registered.lower(), actual))
                stale.append(sid)
        elif registered is None:
            warnings.append("来源 %s 没有记 sha256：%s 的原文改了，check 报不出来；核过原文后可以从 "
                            "sources.digests 照抄" % (sid, file_name))
    for sid, entry in by_id.items():
        target = entry.get("superseded_by")
        if entry.get("status") != "superseded" or not text_of(target):
            continue   # 没写 superseded_by 的，上面已经报过
        if not need(target in by_id, "来源 %s：superseded_by 写的 %s 不在 sources 里" % (sid, target)):
            continue
        seen, current = {sid}, target
        while isinstance(current, str) and current in by_id and current not in seen \
                and by_id[current].get("status") == "superseded":
            seen.add(current)
            current = by_id[current].get("superseded_by")
        need(isinstance(current, str) and current in by_id and current not in seen
             and by_id[current].get("status") != "superseded",
             "来源 %s：superseded_by 顺着找下去，必须落到一个 in_force 或 pending 的来源" % sid)

    # --- texts：已采纳的成果（不写、写 null 都算空）
    texts = register.get("texts")
    if texts is None:
        texts = {}
    if not need(isinstance(texts, dict), "texts 必须是对象：成果 id 对相对路径"):
        texts = {}
    known_texts = {}
    for tid, rel in texts.items():
        if need(text_of(tid) and text_of(rel), "texts 里的 %s：要有 id，路径必须是非空字符串" % shown(tid)):
            known_texts[tid] = rel
    lines_of, texts_checked = {}, False
    if texts_root is None:
        if known_texts:
            warnings.append("没有给 --texts-root，成果一边的行号和原句没有核；要核就加上 --texts-root（成果路径的起点目录）")
    elif need(path_kind(texts_root)[0] == "dir", "--texts-root 不是目录：%s" % texts_root):
        texts_checked = True
        for tid, rel in known_texts.items():
            location = Path(texts_root) / rel
            kind, reason = path_kind(location)
            if kind == "missing":
                where = "找不到" if Path(rel).is_absolute() else "在 --texts-root 下找不到"
                problems.append("成果 %s：%s %s" % (tid, where, rel))
                continue
            if not need(kind == "file", missing_file("成果 %s" % tid, kind, reason, rel, " --texts-root")):
                continue
            try:
                lines_of[tid] = split_lines(read_text(location))
            except Unreadable as error:
                problems.append("成果 %s：%s %s；另存为 UTF-8 再核" % (tid, rel, error))

    # --- items：每条一个冲突
    items = register.get("items")
    need(isinstance(items, list), "items 必须是列表")
    counts = {status: 0 for status in ITEM_STATUS}
    kinds = {kind: 0 for kind in KINDS}
    item_ids, unchecked = set(), {}
    for item in items if isinstance(items, list) else []:
        if not need(isinstance(item, dict) and text_of(item.get("id")), "每个条目都要有 id（非空字符串）"):
            continue
        iid = item["id"]
        need(iid not in item_ids, "条目 id %s 出现了两次" % iid)
        item_ids.add(iid)
        warnings.extend(unknown_keys(item, ITEM_KEYS, "条目 %s " % iid))
        need(text_of(item.get("title")), "条目 %s 缺 title" % iid)
        kind = item.get("kind")
        if need(isinstance(kind, str) and kind in KINDS, "条目 %s：kind 必须是 %s 之一" % (iid, "、".join(KINDS))):
            kinds[kind] += 1
        sides = item.get("sides")
        minimum = 1 if kind == "exception" else 2
        need(isinstance(sides, list) and len(sides) >= minimum,
             "条目 %s：sides 至少要有 %d 项（必须是列表；exception 至少 1 项，别的至少 2 项）" % (iid, minimum))
        cites_live = cites_known = False
        for number, side in enumerate(sides if isinstance(sides, list) else [], 1):
            label = "条目 %s 第 %d 项 sides" % (iid, number)
            if not need(isinstance(side, dict), label + " 必须是对象"):
                continue
            warnings.extend(unknown_keys(side, SIDE_KEYS, label + " "))
            if "source" in side and "text" in side:
                problems.append(label + " 只能引一个来源（source）或一份成果（text），不能两个都写")
            elif "source" in side:
                sid = side["source"]
                known = isinstance(sid, str) and sid in by_id
                if need(known, label + " 引了不存在的来源 %s" % shown(sid)):
                    cites_known = True
                    cites_live = cites_live or by_id[sid].get("status") != "superseded"
                need(text_of(side.get("where")), label + " 要写 where（来源里的哪一节、哪一条）")
                strength = side.get("strength")
                need(strength is None or (isinstance(strength, str) and strength in STRENGTHS),
                     label + "：strength 只能是 must（必须）或 should（建议），现在是 %s"
                     % json.dumps(strength, ensure_ascii=False))
                quote = side.get("quote")
                if need(quote is None or isinstance(quote, str), label + "：quote 必须是字符串") \
                        and known and text_of(quote):
                    if sid in source_text:
                        need(quote in source_text[sid], label + "：原句在 %s 里找不到" % by_id[sid].get("file"))
                    elif sid in no_file:
                        unchecked[sid] = unchecked.get(sid, 0) + 1
            elif "text" in side:
                tid = side["text"]
                known = isinstance(tid, str) and tid in known_texts
                need(known, label + " 引了不存在的成果 %s" % shown(tid))
                need(side.get("strength") is None, label + "：strength 只写在规则一边（source），成果一边（text）不写")
                line = side.get("line")
                line_ok = need(type(line) is int and line >= 1, label + "：line 必须是正整数（从 1 数起）")
                quote = side.get("quote")
                quote_ok = need(text_of(quote), label + " 要写 quote（那一行里的原话）")
                if known and line_ok and quote_ok and tid in lines_of:
                    lines = lines_of[tid]
                    if need(line <= len(lines), label + "：%s 只有 %d 行，没有第 %d 行" % (tid, len(lines), line)):
                        need(quote in lines[line - 1], label + "：原句不在 %s 第 %d 行" % (tid, line))
            else:
                problems.append(label + " 必须引一个来源（source）或一份成果（text）")
        status = item.get("status")
        if need(isinstance(status, str) and status in ITEM_STATUS,
                "条目 %s：status 必须是 %s 之一" % (iid, "、".join(ITEM_STATUS))):
            counts[status] += 1
        decided = item.get("decided_by")
        if status == "open":
            need(text_of(item.get("ask")), "条目 %s 是 open，要写 ask：委托人要定什么" % iid)
            need(text_of(item.get("meanwhile")), "条目 %s 是 open，要写 meanwhile：定下之前怎么办" % iid)
            need(not item.get("resolution") and not decided,
                 "条目 %s 是 open，却写了 resolution 或 decided_by" % iid)
            need(cites_live or not cites_known, "条目 %s 是 open，但只引了被取代的来源；先按现行的版本重核" % iid)
        elif status == "decided":
            need(text_of(item.get("resolution")), "条目 %s 是 decided，要写 resolution：怎么定的" % iid)
            check_decided_by(iid, decided, kind, need, warnings)
        elif status == "closed":
            need(text_of(item.get("resolution")), "条目 %s 是 closed，要写 resolution：为什么关掉" % iid)
            if decided is not None:   # closed 可以不写谁定的；写了就照 decided 的规矩核
                check_decided_by(iid, decided, kind, need, warnings)
    for sid, number in unchecked.items():
        why = "是外部依据（external），没有本地文件" if no_file[sid] == "external" else "没写 file"
        warnings.append("来源 %s %s，引它的 %d 处原句没有核" % (sid, why, number))
    return {"status": "FAIL" if problems else "OK", "problems": problems, "warnings": warnings,
            "counts": counts, "kinds": kinds,
            "sources": {"in_force": sum(1 for s in by_id.values() if s.get("status") == "in_force"),
                        "superseded": sum(1 for s in by_id.values() if s.get("status") == "superseded"),
                        "pending": sum(1 for s in by_id.values() if s.get("status") == "pending"),
                        "stale": stale, "digests": digests},
            "texts_checked": texts_checked}


def check_decided_by(iid, decided, kind, need, warnings):
    """decided_by：谁定的、哪天定的、依据什么。exception 是委托人明示有意为之的做法，只能由委托人定。"""
    who = decided.get("who") if isinstance(decided, dict) else None
    if not need(isinstance(who, str) and who in DECIDERS,
                "条目 %s：decided_by.who 必须是 principal 或 ai（principal 是委托人定的，ai 是 AI 按裁决顺序定的）" % iid):
        return
    warnings.extend(unknown_keys(decided, DECIDED_KEYS, "条目 %s 的 decided_by " % iid))
    need(text_of(decided.get("when")), "条目 %s：decided_by.when 没写（哪天定的）" % iid)
    if who == "principal":
        need(text_of(decided.get("words")), "条目 %s：委托人定的，要写委托人或他授权的人的原话（words）" % iid)
        need(text_of(decided.get("source")), "条目 %s：委托人定的，要写原话的出处（source）" % iid)
        return
    need(kind != "exception",
         "条目 %s 是 exception（委托人明示有意为之的做法），decided_by.who 必须是 principal" % iid)
    step = decided.get("rule_applied")
    need(type(step) is int and step in AI_STEPS,
         "条目 %s：AI 定的，要写 rule_applied：按裁决顺序第 1 至 4 步的哪一步（整数）；"
         "第 5 步只能由委托人定" % iid)


# --- list -------------------------------------------------------------------------------------------------------

def one_line(value):
    """放进核对单的值：换行换成“／”，免得续行跑出列表项、凭空造出标题。"""
    parts = [part.strip() for part in re.split(r"\r\n|\r|\n", as_text(value))]
    return "／".join(part for part in parts if part)


def listing(register_path, status="open", markdown=False):
    """status 为 all 时列全部。返回条目列表，或 --markdown 的核对单文字。读不了、格式不对抛 Unreadable。"""
    register = load_for_reading(register_path)
    items = register.get("items")
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise Unreadable("items 必须是由对象组成的列表；先运行 check 看具体问题")
    wanted = [item for item in items if status == "all" or item.get("status") == status]
    if not markdown:
        return wanted
    sources = register.get("sources") if isinstance(register.get("sources"), list) else []
    names = {}
    for source in sources:
        if isinstance(source, dict) and isinstance(source.get("id"), str):
            names[source["id"]] = next((source[k] for k in ("label", "title") if text_of(source.get(k))), source["id"])
    paths = register.get("texts") if isinstance(register.get("texts"), dict) else {}
    lines = ["## %s：%s（共 %d 条）" % (one_line(register.get("project")) or "（没写项目名）", HEADING[status], len(wanted)),
             ""]
    if not wanted:
        lines.append("没有。")
    for item in wanted:
        state, kind = item.get("status"), item.get("kind")
        tags = [KIND_LABEL.get(kind, one_line(kind)) if isinstance(kind, str) else one_line(kind),
                STATUS_LABEL.get(state, one_line(state)) if isinstance(state, str) else one_line(state)]
        if state == "open" and text_of(item.get("since")):
            tags.append("自 %s 起" % one_line(item["since"]))
        head = "- **%s**（%s）%s" % (one_line(item.get("id")), "，".join(t for t in tags if t), one_line(item.get("title")))
        tail = item.get("ask") if state == "open" else item.get("resolution")
        if text_of(tail):
            head += "：" + one_line(tail)
        lines.append(head)
        if state == "open" and text_of(item.get("meanwhile")):
            lines.append("  - 定下之前：" + one_line(item["meanwhile"]))
        for side in item.get("sides") if isinstance(item.get("sides"), list) else []:
            if not isinstance(side, dict):
                continue
            if "source" in side:
                sid = side["source"]
                entry = "  - %s，%s" % (one_line(names.get(sid, sid) if isinstance(sid, str) else sid),
                                        one_line(side.get("where")))
                strength = side.get("strength")   # list 不核它的值（由 check 核），写错了的照 JSON 的写法标出来
                if isinstance(strength, str) and strength in STRENGTH_LABEL:
                    entry += "（%s）" % STRENGTH_LABEL[strength]
                elif strength is not None:
                    entry += "（strength 写的是 %s，先跑 check）" % json.dumps(strength, ensure_ascii=False)
                if text_of(side.get("quote")):
                    entry += "：" + one_line(side["quote"])
            elif "text" in side:
                tid = side["text"]
                path = paths.get(tid) if isinstance(tid, str) else None
                where = "%s（%s）" % (one_line(tid), one_line(path)) if text_of(path) else one_line(tid) + " "
                entry = "  - %s第 %s 行：%s" % (where, one_line(side.get("line")), one_line(side.get("quote")))
            else:
                continue
            lines.append(entry)
        if text_of(item.get("proposal")):
            lines.append("  - AI 的建议：" + one_line(item["proposal"]))
        decided = item.get("decided_by")
        if state == "decided" and isinstance(decided, dict):
            when = one_line(decided.get("when"))
            if decided.get("who") == "principal":
                lines.append("  - 定的人：委托人，%s，原话：“%s”（%s）"
                             % (when, one_line(decided.get("words")), one_line(decided.get("source"))))
            elif decided.get("who") == "ai":
                lines.append("  - 定的人：AI，%s，按裁决顺序第 %s 步" % (when, one_line(decided.get("rule_applied"))))
    return "\n".join(lines) + "\n"


# --- collide ----------------------------------------------------------------------------------------------------

def snippet(line, at, width, room=40):
    """命中的那一行；行太长时只取词前后各 room 个字，截掉的地方用“…”标出。"""
    if len(line.strip()) <= 2 * room + width:
        return line.strip()
    start, end = max(0, at - room), min(len(line), at + width + room)
    return ("…" if line[:start].strip() else "") + line[start:end].strip() + ("…" if line[end:].strip() else "")


def original_index(line, folded_at):
    """casefold 改变了长度（比如 ß 变成 ss）时，把折叠后文字里的位置换回原行里的位置。"""
    total = 0
    for index, char in enumerate(line):
        total += len(char.casefold())
        if total > folded_at:
            return index
    return len(line)


def collide(register_path, texts_root, words, ignore_case=False):
    """每份登记的成果里含这些词的每一行。complete 只在每份登记的成果都读到时为 true：
    找不到的列在 missing_texts，读不了的（比如不是 UTF-8）列在 unreadable_texts，
    所以“没读到”不会看起来像“读了，没撞上”。"""
    words = list(dict.fromkeys(words))
    hits = {word: [] for word in words}
    result = {"complete": False, "words": hits, "texts": [], "checked": [], "missing_texts": [],
              "unreadable_texts": []}
    try:
        register = load_for_reading(register_path)
    except Unreadable as error:
        result["error"] = str(error)
        return result
    texts = register.get("texts")
    if texts is None:
        texts = {}   # 不写、写 null 都算空，和 check 一样
    if not isinstance(texts, dict):
        result["error"] = "texts 必须是对象：成果 id 对相对路径；先运行 check 看具体问题"
        return result
    if not texts:
        result["error"] = "登记表的 texts 是空的：没有列已采纳的成果，没有文件可查"
        return result
    result["texts"] = list(texts)
    root = Path(texts_root)
    if path_kind(root)[0] != "dir":
        result["error"] = "--texts-root 不是目录：%s" % texts_root
        result["missing_texts"] = [{"text": tid, "path": rel} for tid, rel in texts.items()]
        return result

    def fold(value):
        return value.casefold() if ignore_case else value

    needles = [(word, fold(word)) for word in words]
    for tid, rel in texts.items():
        kind, reason = path_kind(root / rel) if text_of(rel) else ("missing", "")
        if kind == "missing":
            result["missing_texts"].append({"text": tid, "path": rel})
            continue
        if kind != "file":
            why = "读不了（%s）" % reason if kind == "error" else "不是普通文件（是目录、设备或管道这类）"
            result["unreadable_texts"].append({"text": tid, "path": rel, "reason": why})
            continue
        try:
            lines = split_lines(read_text(root / rel))
        except Unreadable as error:
            result["unreadable_texts"].append({"text": tid, "path": rel, "reason": str(error)})
            continue
        result["checked"].append(tid)
        for number, line in enumerate(lines, 1):
            folded = fold(line)
            for word, needle in needles:
                at = folded.find(needle)
                if at >= 0:
                    if len(folded) != len(line):
                        at = original_index(line, at)
                    hits[word].append({"text": tid, "line": number, "snippet": snippet(line, at, len(word))})
    result["complete"] = not result["missing_texts"] and not result["unreadable_texts"]
    return result


# --- 命令行 -----------------------------------------------------------------------------------------------------

def utf8_stdio():
    """输出一律 UTF-8；不然 Windows 的管道会用本地代码页（比如 GBK），有的字写不出来。
    写不出来的（比如命令行里解不了的字节）写成 \\udcff 这样的转义，不让输出半路断掉。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def dump(value):
    print(json.dumps(value, ensure_ascii=False, indent=1))


def main(argv=None):
    utf8_stdio()
    parser = argparse.ArgumentParser(prog="conflict_register.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, metavar="{check,list,collide}")
    p_check = commands.add_parser("check", help="核对登记表的结构、来源版本和哈希、证据的原句和行号")
    p_check.add_argument("register", help="登记表（JSON 文件）")
    p_check.add_argument("--texts-root", help="成果路径的起点目录；不给就不核成果一边的行号和原句")
    p_list = commands.add_parser("list", help="列出条目，默认列还没定的；--markdown 出给委托人的核对单")
    p_list.add_argument("register", help="登记表（JSON 文件）")
    p_list.add_argument("--status", default="open", choices=ITEM_STATUS + ("all",),
                        help="列哪一种状态的条目，all 是全部；默认 open")
    p_list.add_argument("--markdown", action="store_true", help="输出 Markdown 核对单，不输出 JSON")
    p_collide = commands.add_parser("collide", help="列出每个词在已采纳的成果里出现的行")
    p_collide.add_argument("--register", required=True, help="登记表（JSON 文件）")
    p_collide.add_argument("--texts-root", required=True, help="成果路径的起点目录")
    p_collide.add_argument("--ignore-case", action="store_true", help="不区分大小写")
    p_collide.add_argument("words", nargs="+", metavar="WORD", help="要查的词，按字面找")
    args = parser.parse_args(argv)

    if args.command in ("check", "collide") and args.texts_root is not None and not args.texts_root.strip():
        (p_check if args.command == "check" else p_collide).error("--texts-root 不能是空的")
    if args.command == "check":
        result = check(args.register, args.texts_root)
        dump(result)
        return 0 if result["status"] == "OK" else 1
    if args.command == "list":
        try:
            result = listing(args.register, args.status, args.markdown)
        except Unreadable as error:
            dump({"status": "FAIL", "problems": [str(error)]})
            return 1
        except SHAPE_ERRORS as error:
            dump({"status": "FAIL", "problems": ["登记表的格式不对（%s: %s）；先运行 check 看具体问题"
                                                 % (type(error).__name__, error)]})
            return 1
        if args.markdown:
            sys.stdout.write(result)
        else:
            dump(result)
        return 0
    if any(not word.strip() for word in args.words):
        p_collide.error("要查的词不能是空的")
    if not all(encodable(word) for word in args.words):
        p_collide.error("要查的词里有不能按 UTF-8 解的字节；把终端或脚本的编码改成 UTF-8 再查")
    try:
        result = collide(args.register, args.texts_root, args.words, args.ignore_case)
    except SHAPE_ERRORS as error:
        result = {"complete": False, "error": "登记表的格式不对（%s: %s）；先运行 check 看具体问题"
                                              % (type(error).__name__, error)}
    dump(result)
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
