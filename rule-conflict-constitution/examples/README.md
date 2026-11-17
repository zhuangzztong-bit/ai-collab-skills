# 例子：一个帮助中心的冲突登记表

一个小团队给自家的待办应用写帮助中心。内容组、客服组、产品组各有一份规范，委托人是帮助中心的负责人，他把这三份规范，连同设计组的一份界面文案规范，都定为本项目的规则。帮助中心已经有几篇委托人采纳过的文章和一份界面文字。几份规范互相打架，规范和已采纳的成果也有对不上的地方，于是建了一张冲突登记表。团队、委托人、产品、规范和成果都是为这个例子编的。

## 文件

```text
help-center/
  conflict-register.json            填好的冲突登记表
  rules/                            规则文件（sources）
    writing-guide.md                内容组的写作规范第二版（现行；“<!-- 原文开始 -->”前面是 AI 的加注）
    archive/writing-guide-v1.md     写作规范第一版（被第二版取代，存档）
    support-replies.md              客服组的客服回复规范（现行）
    glossary.md                     产品组的术语表（现行）
  texts/                            已采纳的成果（texts）
    faq-account.md                  常见问题：账户
    refund.md                       申请退款
    settings-notifications.md       管理通知
    terms-excerpt.md                服务条款摘录
    ui-strings.json                 界面文字（数据文件）
```

`writing-guide.md` 用的是中文的标记行 `<!-- 原文开始 -->`，这一行之前是加注，之后是原文。标记行也可以写成英文的 `<!-- original text begins -->`，脚本一样认，见[规则打架时怎么定](../docs/conflict-resolution.md)里的“先查再入册”。

登记表里还有两份没有本地文件的来源：设计组的界面文案规范（`"external": true`，外部依据，不在这里留副本）和产品组的术语表修订草案（`pending`，委托人还没定）。

## 登记表里的六条

| 条目 | kind | 状态 | 说的是什么 |
|---|---|---|---|
| HC-01 | conflict | open | 写作规范说退款类文章用“你”，客服回复规范说用“您”。两条都是必须，不是建议（登记表里两边的 `strength` 都写 `must`，核对单里标成“（必须）”），所以要走五步。两份同一天发，管的范围一样，谁也不是谁的新版本，定不了，交委托人定；写明了定下之前怎么办。 |
| HC-02 | mismatch | decided（AI，第 2 步） | 写作规范说账户类问题“已经全部改成用‘你’”，已采纳的问答第 7 行还是“您”。这是描述，和成果对不上，不当成事实用。 |
| HC-03 | collision | decided（委托人） | 术语表让“标签”专指彩色标记，已采纳的成果里“标签页”指界面上的分页。委托人定了：“标签页”照旧。 |
| HC-04 | stale | decided（AI，第 1 步） | 写作规范第二版开头说“全部执行”，第四节还标着“待定”。和第一版逐字比过，按第二版新改的那句读。 |
| HC-05 | exception | decided（委托人） | 服务条款摘录照法务原文用“您”，登记一次，以后不再报。 |
| HC-06 | conflict | closed | 第一版说按钮名加粗，设计组说外加「」；第二版已经改成外加「」，这一条不再成立。 |

“第 1 步”“第 2 步”指裁决顺序的步数（登记表里的 `rule_applied`）。AI 只能按第 1 至 4 步定；第 5 步（还定不了）只能交委托人。

## 怎么跑

要 Python 3.9 或更新的版本，只用标准库，不用装别的。在 `examples/help-center/` 目录里运行下面的命令。下面贴的输出都是实际运行的结果（在 Linux 上用 Python 3.13 和 3.9 跑过，输出一样；Windows 上没有试过）。

### 1. 核对登记表

```text
python3 -I -B ../../scripts/conflict_register.py check conflict-register.json --texts-root .
```

退出码 0，输出：

```json
{
 "status": "OK",
 "problems": [],
 "warnings": [
  "来源 design-copy 是外部依据（external），没有本地文件，引它的 1 处原句没有核"
 ],
 "counts": {
  "open": 1,
  "decided": 4,
  "closed": 1
 },
 "kinds": {
  "conflict": 2,
  "mismatch": 1,
  "collision": 1,
  "stale": 1,
  "exception": 1
 },
 "sources": {
  "in_force": 4,
  "superseded": 1,
  "pending": 1,
  "stale": [],
  "digests": {
   "writing-guide-v2": "08e4f08ebbdc326d64f07406cb9be8b1d941eab6bf45a271de066e023008407a",
   "writing-guide-v1": "a472d1f0c8d59d2056702fb6454e8057f9d360200c4d4cdf137171bdcf47663d",
   "support-replies": "568be5f70eb504f3d9f899e0767b076cc1fa3cd929e40cc65aef0c526e63c0df",
   "glossary": "9f1d2f044009ca929faa2649390fe68944f2f9c465f21d75c885ff2dbdbbf3ba"
  }
 },
 "texts_checked": true
}
```

- `status` 是 `OK`，`problems` 是空的：结构、来源版本、原句和行号都对得上。
- `warnings` 说出了没核的东西：设计组的规范没有本地文件，HC-06 引它的那句原句没有核。
- `sources.digests` 是每份读到的本地来源现在的摘要。四份本地来源在登记表里都钉了 `sha256`，和这里的值一样，所以没有报“改过”；新登记一份来源时，核过原文后照抄这里的值。哪份本地来源没记 `sha256`，`warnings` 里会提醒一句。
- 不给 `--texts-root` 也能跑，但成果一边的行号和原句就不核了，`texts_checked` 是 `false`，`warnings` 里会多一句提醒。

### 2. 列出还没定的条目，给委托人一张核对单

```text
python3 -I -B ../../scripts/conflict_register.py list conflict-register.json --status open --markdown
```

退出码 0，输出：

```markdown
## 帮助中心改版（示例）：还没定的条目（共 1 条）

- **HC-01**（规则打架，还没定，自 2026-11-05 起）写作规范和客服回复规范对退款类文章的称呼说法不同：退款类文章称呼用户用“你”还是“您”？
  - 定下之前：已采纳的退款说明照原样，不按任何一条改；新写的退款类文字尽量不直接称呼用户（比如写成“申请提交后，款项会在 7 个工作日内原路退回”），避不开的地方标出来交委托人定。
  - 写作规范第二版，第一节第 2 条（必须）：退款类文章也用“你”
  - 客服回复规范，第二节第 1 条（必须）：退款类文章称呼用户用“您”
  - refund（texts/refund.md）第 3 行：您的退款申请提交后
  - AI 的建议：两条都是必须，不是建议；两份规范同一天发，管的都是退款类文章，谁也不是谁的新版本，按裁决顺序定不了。请委托人选一个；选定后，由内容组或客服组把自己那一份改成一致的说法。
```

不加 `--markdown` 输出 JSON（条目原样列出）；`--status` 可以是 `open`（默认）、`decided`、`closed` 或 `all`。

### 3. 查新叫法在已采纳的成果里有没有用过

术语表要让“标签”专指任务上的彩色标记。先查“标签”在成果里已经怎么用，顺便查一个还没用过的词“收藏”：

```text
python3 -I -B ../../scripts/conflict_register.py collide --register conflict-register.json --texts-root . 标签 收藏
```

退出码 0，输出：

```json
{
 "complete": true,
 "words": {
  "标签": [
   {
    "text": "settings-notifications",
    "line": 3,
    "snippet": "打开「设置」，切到「通知」标签页，关掉“邮件提醒”。"
   },
   {
    "text": "ui-strings",
    "line": 3,
    "snippet": "\"settings.tabs.hint\": \"在上方的标签页之间切换\","
   },
   {
    "text": "ui-strings",
    "line": 5,
    "snippet": "\"task.tag.add\": \"添加标签\","
   }
  ],
  "收藏": []
 },
 "texts": [
  "faq-account",
  "refund",
  "settings-notifications",
  "terms-excerpt",
  "ui-strings"
 ],
 "checked": [
  "faq-account",
  "refund",
  "settings-notifications",
  "terms-excerpt",
  "ui-strings"
 ],
 "missing_texts": [],
 "unreadable_texts": []
}
```

“标签”在 `settings-notifications` 第 3 行和 `ui-strings` 第 3 行指的是界面上的分页，这就是 HC-03 的来由；`ui-strings` 第 5 行的“添加标签”正是新叫法要指的东西。“收藏”一处也没有。`complete` 是 `true`，说明登记的五份成果都读到了，“一处也没有”才算数。程序只按字面找：它不知道哪一处是同一个意思、哪一处不是，这要人看。

### 4. 没读全的时候

`--texts-root` 指错了目录（这里指成了 `texts`，路径就成了 `texts/texts/…`）：

```text
python3 -I -B ../../scripts/conflict_register.py collide --register conflict-register.json --texts-root texts 标签
```

退出码 1，输出：

```json
{
 "complete": false,
 "words": {
  "标签": []
 },
 "texts": [
  "faq-account",
  "refund",
  "settings-notifications",
  "terms-excerpt",
  "ui-strings"
 ],
 "checked": [],
 "missing_texts": [
  {
   "text": "faq-account",
   "path": "texts/faq-account.md"
  },
  {
   "text": "refund",
   "path": "texts/refund.md"
  },
  {
   "text": "settings-notifications",
   "path": "texts/settings-notifications.md"
  },
  {
   "text": "terms-excerpt",
   "path": "texts/terms-excerpt.md"
  },
  {
   "text": "ui-strings",
   "path": "texts/ui-strings.json"
  }
 ],
 "unreadable_texts": []
}
```

一份也没读到，所以 `complete` 是 `false`，退出码是 1。没读到不会看起来像“读了，没撞上”。

### 5. 证据对不上的时候

把整个 `help-center` 目录复制一份，在副本里把 `conflict-register.json` 中 HC-02 里 `faq-account` 的行号从 7 改成 8（第 8 行是空行），在副本目录里再核：

```text
python3 -I -B ../../scripts/conflict_register.py check conflict-register.json --texts-root .
```

退出码 1，输出：

```json
{
 "status": "FAIL",
 "problems": [
  "条目 HC-02 第 2 项 sides：原句不在 faq-account 第 8 行"
 ],
 "warnings": [
  "来源 design-copy 是外部依据（external），没有本地文件，引它的 1 处原句没有核"
 ],
 "counts": {
  "open": 1,
  "decided": 4,
  "closed": 1
 },
 "kinds": {
  "conflict": 2,
  "mismatch": 1,
  "collision": 1,
  "stale": 1,
  "exception": 1
 },
 "sources": {
  "in_force": 4,
  "superseded": 1,
  "pending": 1,
  "stale": [],
  "digests": {
   "writing-guide-v2": "08e4f08ebbdc326d64f07406cb9be8b1d941eab6bf45a271de066e023008407a",
   "writing-guide-v1": "a472d1f0c8d59d2056702fb6454e8057f9d360200c4d4cdf137171bdcf47663d",
   "support-replies": "568be5f70eb504f3d9f899e0767b076cc1fa3cd929e40cc65aef0c526e63c0df",
   "glossary": "9f1d2f044009ca929faa2649390fe68944f2f9c465f21d75c885ff2dbdbbf3ba"
  }
 },
 "texts_checked": true
}
```

## 这个例子说明不了什么

- 程序没有替谁定 HC-01。“你”还是“您”，要委托人定；程序只核登记表写的原句、行号、状态和必填的说明是不是齐、是不是对得上。
- 程序不判断哪条规范写得好、该不该留，也不判断成果写得对不对。HC-02 的“描述和成果对不上”是人发现、人登记的，程序只核登记的原句确实在那两处。
- 外部依据（`external`）没有本地文件，引它的原句核不了，只在 `warnings` 里说一声。
- 这个例子能跑通，只说明登记表的格式和程序对得上，不说明这套办法一定能让工作做得更好。
