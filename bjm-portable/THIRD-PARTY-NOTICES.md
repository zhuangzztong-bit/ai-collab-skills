# 第三方组件与许可范围

本仓库按 MIT 许可发布，全文见 [LICENSE](LICENSE)，版权人 Celeste。这份文件说明哪些东西是别人的，继续按它们自己的许可。

## 许可范围

- 根目录的 `LICENSE` 适用于本仓库里版权人自己的内容：`SKILL.md`、`README.md`、`CHANGELOG.md`、`references/`、`scripts/`、`tests/`、`examples/`、`graph-runtime/` 和 `docs/images/`（README 用的图标和题图）。
- 下面列出的第三方组件不算进版权人的版权声明，各按自己的许可，版权归各自的权利人。

## 包里带的第三方组件

| 组件 | 版权行 | 包里的哪些文件 | 许可文件 |
|:-----|:-------|:---------------|:---------|
| [Agent Skills](https://github.com/addyosmani/agent-skills) 0.6.16 | Copyright (c) 2025 Addy Osmani | `vendor/agent-skills-0.6.16/`（展开目录）和 `vendor/agent-skills-0.6.16.zip`（标签源码 ZIP，原样保留） | `vendor/agent-skills-0.6.16/LICENSE`，ZIP 里也有同一份 |

- 标签源码 ZIP 的 SHA-256：`6f0304fe35188526f27541e913b9aeff60663ae076c04c65090df12875aeec48`；ZIP 注释里记的提交是 `39b723ceebf81474d0557c1fecd01eddab585563`。
- 展开目录和 ZIP 的差别：原包里的符号链接 `.opencode/skills -> ../skills/` 只在 ZIP 里，展开目录没有 `.opencode/`。其余文件逐字节相同；`hooks/` 下 7 个和 `skills/idea-refine/scripts/` 下 1 个 shell 脚本照 ZIP 保留可执行位。
- `references/bjm-v3.2.md` 参考 Agent Skills 改写，出处见那一页“改编依据”一节。那一节写的是当时依据的 `agent-skills-main.zip` 快照（0.6.15 前后的 main 分支）；本仓库带的是 0.6.16 标签版。
- 再分发 `vendor/` 下的文件时，请把 Agent Skills 的版权行和许可声明一起带上。

Agent Skills 的许可声明原文如下，配上表里的版权行：

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 只作参考、没有带进来的

- `graph-runtime/README.md`“设计参考”一节列的 LangGraph、Temporal 和论文只是链接，仓库里没有它们的代码。
- `references/bjm-v3.2.md` 开头的“方法来源”是一条公开讨论的链接。
- `references/blind-review.md` 末尾链接了达尔文（[alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill)）v3.0.0 和 v3.0.1 的发布页。`scripts/blind_review.py` 参考了它成对盲评的做法和它发现的路径泄露问题，是另外写的，仓库里没有达尔文的代码或文本。
