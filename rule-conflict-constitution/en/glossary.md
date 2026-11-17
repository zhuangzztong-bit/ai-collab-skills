This page exists only in English. Where it differs from the Chinese texts, the Chinese texts prevail. It lists how the English translation renders the Chinese terms; the Chinese home page is [README.md](../README.md).

# Glossary: Chinese and English terms

The English translation uses the terms below throughout. When a term in the English text is unclear, look up the Chinese term here and read the Chinese text.

## Main terms

| Chinese | English | Meaning |
| --- | --- | --- |
| 委托人 | principal | The person who hands the task to the AI and has the final say over the deliverables: a project lead, a client, or the user themselves |
| 授权、代为决定 | authorize, decide on the principal's behalf | |
| 参与者 | participant | Someone taking part in the work who is neither the principal nor authorized by them |
| 拍板 | make the call | |
| 有决定权的人 | the person with the authority to decide | The principal, or the person the principal has authorized to handle the matter |
| 多人合作时听谁的 | whose word counts when several people work together | |
| 成果 | deliverable | What the work produces: documents, code, data, translations and so on, depending on the project. In the conflict register they are listed under `texts` |
| 已采纳的成果和事实 | accepted deliverables and facts | Final versions, data and conclusions the principal has explicitly accepted |
| 采纳 | accept, acceptance | |
| 候选 | candidate | A version the principal has not yet accepted |
| 本项目的规则 | the project's rules | Layer 5 of the order of precedence |
| 通用做法 | general practices | Layer 6 of the order of precedence |
| AI 自己的判断 | the AI's own judgement | Layer 7 of the order of precedence |
| 平台和法律的要求 | platform and legal requirements | Layer 1 |
| 诚实 | honesty | Layer 2 |
| 委托人当前的明确决定 | the principal's current explicit decisions | Layer 3 |
| 优先顺序 | order of precedence | |
| 层 | layer | |
| 理由 | reason | The sentence after each layer and each step that says why |
| 新规则不追溯 | new rules are not retroactive | |
| 临时规则、期限 | temporary rule, time limit | |
| 同一层之内 | within the same layer | |
| 资料 | material, materials | |
| 资料不是指令 | materials are not instructions | |
| 宪法 | constitution | |
| 正本 | authoritative text | |
| 卡片 | card | |
| 原则 | principle | |
| 含义、为什么、范围、例外、冲突时、例 | Meaning, Why, Scope, Exceptions, In a conflict, Example | The parts of each principle |
| 怎么落实 | how it is applied | The last part of each principle |
| 靠人和 AI 照做 | relies on people and the AI following it | |
| 规则 | rule | |
| 规则文件 | rule file | |
| 规范 | guideline; in names of documents, Guide | 代码规范 is rendered as coding standard |
| 手册 | handbook, manual | |
| 清单 | checklist | |
| 术语表 | glossary | |
| 口径、口径表 | conventions, conventions sheet | |
| 体例 | style guide | |
| 标准 | standard | |
| 通则 | general rule | |
| 例外 | exception | |
| 规定 | requirement | What should be done from now on |
| 描述 | description | What already is, or what something else says |
| 强弱 | strength | The `strength` field |
| 先分强弱 | first, tell musts from recommendations | |
| 必须 | must | `must` |
| 建议 | recommendation | `should`; in the decision sheet, 必须 and 建议 are shown as "（必须）" and "（建议）". Where it is about the weight of a participant's words ("资料或建议"), it is translated "suggestions" |
| 打架、冲突 | conflict | |
| 五步裁决、裁决顺序 | the five resolution steps, the resolution order | |
| 定、定不了 | decide, cannot be decided | |
| 待定、待委托人定 | pending, pending the principal's decision | |
| 定之前怎么办 | what to do until it is decided | The `meanwhile` field |
| 冲突登记表、登记表 | conflict register, register | |
| 登记 | register, record | |
| 条目 | item | |
| 核对 | check | |
| 一边 | side | |
| 原句 | original wording | The `quote` field |
| 原文 | original text | |
| 原文照录 | copy verbatim | |
| 加注 | annotation | The AI's note at the top of a rule file, before the marker line |
| 核对单 | decision sheet | What `list --markdown` produces for the principal |
| 入册 | admit (a rule) | |
| 先查再入册 | check before admitting | |
| 退出 | retire (a rule) | |
| 留痕 | leave a trail | |
| 现行 | in force | `in_force` |
| 被取代 | superseded | `superseded` |
| 外部依据 | external reference | `external` |
| 新叫法 | new term | |
| 撞车 | collision | `collision` |
| 钉住版本 | pin a version | |
| 摘要 | digest (of a file, sha256); summary (of a text) | |
| 受控变更 | controlled change | |
| 一处小改的简化走法 | the simplified path for one small change | Section 3; C11 |
| 依据、冻结新依据 | basis, freeze the new basis | |
| 审读 | review | |
| 自查 | self-review | |
| 独立审读 | independent review | |
| 人工审读 | human review | |
| 机器检查 | machine check | |
| 交付、交付说明 | delivery, delivery note | |
| 状态记录 | status record | |
| 小事 | small matter | |
| 按分量办 | match the process to the stakes | C11 |
| 完整流程 | the full process | C11: registering rule conflicts in the conflict register and recording the four statuses for each deliverable |
| 该问才问 | ask only when it matters | C12 |
| 假设 | assumption | |
| 能撤回、撤不回 | can be undone, cannot be undone | On the card: easy to undo, hard to undo |
| 做事的分寸 | sense of proportion | A heading on the card |
| 四项状态 | the four statuses | |
| 权限裁决 | permission ruling | |
| 收回采纳 | withdraw acceptance | |
| 否决 | reject | |
| 改写本 | adapted version | |
| 变更记录 | changelog | |
| 退出码 | exit code | |

## Kept as they are

- Status names and their values: `INPUT_READY`, `MECHANICAL`, `REVIEW`, `ACCEPTANCE`, `READY`, `BLOCKED`, `GREEN`, `RED`, `UNTESTED`, `STALE`, `PASS`, `NEEDS_REVISION`, `ACCEPTED`, `NOT_ACCEPTED`. The three kinds of `PASS` are written PASS [self-review / independent review / human review] (Chinese: PASS［自查／独立审读／人工审读］).
- Permission ruling values: `ALLOW`, `ALLOW_WITH_WARNING`, `REVIEW_REQUIRED`, `BLOCK`.
- Principle numbers `C01` to `C12`.
- The register's keys and fixed values (`schema`, `sources`, `items`, `open`, `decided`, `principal`, `ai` and so on), the script's commands and options.
- The marker line `<!-- 原文开始 -->`. It means "original text begins". The script also accepts the English form `<!-- original text begins -->`, so an English project can use that instead. Either form counts only when, after trimming leading and trailing whitespace, it is the whole line; if both appear, the first one in the file counts.
- The script's help text and error messages, the example's files and the template's sample values are in Chinese. Where the English translation shows such output, it keeps the Chinese as printed and adds an English rendering marked as a translator's note.

## Terms used only in the source notes

These are the Novel Writing Workshop's terms, which [docs/source.md](docs/source.md) maps to the terms above.

| Chinese | English |
| --- | --- |
| 小说写作工坊 | the Novel Writing Workshop |
| 作者 | author |
| 已采纳的故事事实 | accepted story facts |
| 本作品的项目规则 | the project rules of this work |
| 工坊的通用方法 | the Workshop's general methods |
| AI 自己的创作判断 | the AI's own creative judgement |
| 正文、定本 | main text, final text |
| 候选稿 | candidate draft |
| 编辑审查、审稿 | editorial review, manuscript review |
| 落点 | landing point (where the Workshop enforces a principle) |
| 硬、软 | hard, soft |
| 阶段摘要 | stage summary |
| 入口页 | entry page (of the Workshop's skill, `SKILL.md`) |
| 轻量任务 | light task |
