# AI 协作技能

此仓库收录两套开源协作工具。两套上游内容按发布包保留，AI 协作宪法另加一个供 Agent 按需调用的技能入口。

| 内容 | 版本 | 来源 |
| --- | --- | --- |
| [BJM 通用迁移包](bjm-portable/) | v1.5.1（协议 v3.2） | [上游 release](https://github.com/rumpelpalmour757-lgtm/bjm-portable/releases/tag/v1.5.1) |
| [AI 协作宪法](rule-conflict-constitution/) | v1.0 | [上游 release](https://github.com/rumpelpalmour757-lgtm/rule-conflict-constitution/releases/tag/v1.0) |

将对应技能目录放进宿主的用户级 skills 目录，再在新会话中检查技能列表。BJM 的工程模块位于 `vendor/`；如果宿主已有 BJM，请沿用现有入口路径，避免重复注册。宪法可通过 `rule-conflict-constitution` 按需调用，也可以单独阅读[速查卡](rule-conflict-constitution/CARD.md)。

在 Windows / Python 3.13 上对发布包自查：BJM 核心 47 项通过、1 项跳过，图执行器 8 项通过；宪法 101 项通过、1 项跳过。两个跳过项依赖 Windows 不提供的设备或命令行字节输入。单元测试不代表各 Agent 已实际调用技能。

上游许可随包保留：[BJM](bjm-portable/LICENSE)、[AI 协作宪法](rule-conflict-constitution/LICENSE)，以及 [BJM 的第三方声明](bjm-portable/THIRD-PARTY-NOTICES.md)。
