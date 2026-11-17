# 领域方法

先按用户意图选主要做法。需要新增检查时，说明它服务的验收条件。各领域共用主文件的交付、返修和恢复规则。

| 领域 | 执行与核对 |
|---|---|
| 软件 `software` | 诊断时读现象、日志和调用路径，尽可能复现。修复或新建时确定可观察结果，完成最小可用改动，运行相关测试并记录实际执行项。 |
| 创作 `creative` | 找到最新有效稿和相邻上下文。排版核对字句、标点和顺序，改稿核对人物当时所知、时间线、视角及既定事实。给出具体位置与阅读效果，交由作者采纳。 |
| 研究 `research` | 把结论拆成可核验的说法，记录来源、日期、版本和定位。分别标注直接证据、推断、矛盾和未核实项。 |
| 文档 `documents` | 明确用途、读者和要保留的内容。完成后核对结构、事实、标题、引文和交付格式，涉及排版时检查最终呈现。 |
| 数据 `data` | 明确输入范围、字段、单位、缺失值处理和变换规则。抽查关键记录或计算，核对行数、汇总、单位和舍入。 |
| 运营 `operations` | 确认交付物、负责人或目标、时间、依赖和权限。执行后核对实际对象与结果，记录回执、失败项和恢复条件。 |
| 通用 `general` 或自定义领域 | 写清输入、目标、可动范围、必要证据和交付条件。先完成最小可验收成果。用该领域的有效来源、实际结果或合适的审查意见核对。 |

自定义领域沿用这几个字段。领域标识由小写英文字母、数字和连字符组成，例如 `education` 或 `legal-research`。

| 字段 | 写什么 |
|---|---|
| 成果 | 用户要收到的文件、解释、记录或其他结果 |
| 范围 | 可以修改、必须保留、由谁作决定 |
| 验收 | 什么可机械核对，什么需要实质判断 |
| 证据 | 能定位到输入和成果的实际检查结果 |
| 恢复 | 当前版本、待完成项、剩余预算和下一步 |

## 可选的 Agent Skills 工程方法索引

本包内置 [Agent Skills 0.6.16](https://github.com/addyosmani/agent-skills/releases/tag/0.6.16)。按下表只打开本轮需要的模块，模块的共享资料、模板和脚本沿用原目录结构。把模块中的技术方法用到本轮任务，验收、权限和返修仍按 BJM 执行。需要调用脚本时，先按目标环境的授权和依赖核对。

| 需要补充的方法 | 模块名 |
|---|---|
| 探索问题、澄清需求或审视判断 | [idea-refine](../vendor/agent-skills-0.6.16/skills/idea-refine/SKILL.md)、[interview-me](../vendor/agent-skills-0.6.16/skills/interview-me/SKILL.md)、[doubt-driven-development](../vendor/agent-skills-0.6.16/skills/doubt-driven-development/SKILL.md) |
| 选择方法或管理上下文 | [using-agent-skills](../vendor/agent-skills-0.6.16/skills/using-agent-skills/SKILL.md)、[context-engineering](../vendor/agent-skills-0.6.16/skills/context-engineering/SKILL.md) |
| 定义需求、约束和任务拆分 | [spec-driven-development](../vendor/agent-skills-0.6.16/skills/spec-driven-development/SKILL.md)、[constraint-driven-development](../vendor/agent-skills-0.6.16/skills/constraint-driven-development/SKILL.md)、[planning-and-task-breakdown](../vendor/agent-skills-0.6.16/skills/planning-and-task-breakdown/SKILL.md) |
| 实现、测试或排查故障 | [incremental-implementation](../vendor/agent-skills-0.6.16/skills/incremental-implementation/SKILL.md)、[test-driven-development](../vendor/agent-skills-0.6.16/skills/test-driven-development/SKILL.md)、[debugging-and-error-recovery](../vendor/agent-skills-0.6.16/skills/debugging-and-error-recovery/SKILL.md) |
| 审查质量、安全、复杂度或性能 | [code-review-and-quality](../vendor/agent-skills-0.6.16/skills/code-review-and-quality/SKILL.md)、[security-and-hardening](../vendor/agent-skills-0.6.16/skills/security-and-hardening/SKILL.md)、[code-simplification](../vendor/agent-skills-0.6.16/skills/code-simplification/SKILL.md)、[performance-optimization](../vendor/agent-skills-0.6.16/skills/performance-optimization/SKILL.md) |
| 设计、实现或检查界面 | [api-and-interface-design](../vendor/agent-skills-0.6.16/skills/api-and-interface-design/SKILL.md)、[frontend-ui-engineering](../vendor/agent-skills-0.6.16/skills/frontend-ui-engineering/SKILL.md)、[browser-testing-with-devtools](../vendor/agent-skills-0.6.16/skills/browser-testing-with-devtools/SKILL.md) |
| 核对版本化来源或筹划迁移 | [source-driven-development](../vendor/agent-skills-0.6.16/skills/source-driven-development/SKILL.md)、[deprecation-and-migration](../vendor/agent-skills-0.6.16/skills/deprecation-and-migration/SKILL.md) |
| 记录决策或管理版本 | [documentation-and-adrs](../vendor/agent-skills-0.6.16/skills/documentation-and-adrs/SKILL.md)、[git-workflow-and-versioning](../vendor/agent-skills-0.6.16/skills/git-workflow-and-versioning/SKILL.md) |
| 观察、自动化或发布系统 | [observability-and-instrumentation](../vendor/agent-skills-0.6.16/skills/observability-and-instrumentation/SKILL.md)、[ci-cd-and-automation](../vendor/agent-skills-0.6.16/skills/ci-cd-and-automation/SKILL.md)、[shipping-and-launch](../vendor/agent-skills-0.6.16/skills/shipping-and-launch/SKILL.md) |

Agent Skills 由 Addy Osmani 发布，采用 MIT 许可。
