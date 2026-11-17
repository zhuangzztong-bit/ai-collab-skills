# BJM 图工程原型 v0.1

用 BJM 的分工和验收思路跑一条可恢复的任务图。Python 标准库负责调度，SQLite 保存节点结果、审批状态和执行事件。每个数据库同一时间由一个本机进程调度，进程内可以并行跑分支。两章联审演示使用本地模拟调用，开箱即可复现分支失败和恢复。

## 快速运行

本模块单独解压时，从模块根目录运行。它随 BJM 迁移包分发时，下面的逐条命令从 `bjm-portable/graph-runtime/` 目录运行。需要 Python 3.10 或更新版本，本地验证环境为 Linux 与 Python 3.12。

```bash
python3 demo.py
```

演示脚本依次触发一章失败、从原数据库恢复、修改稿件、拒绝旧审批并接受新审批。下面也可以用 Bash 逐步复现。

```bash
bjm_demo_dir="$(mktemp -d)"
bjm_demo_db="$bjm_demo_dir/demo.sqlite3"

python3 workflow.py --db "$bjm_demo_db" --run-id demo init examples/two_chapters.json
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2 --fail-before review-b
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
python3 workflow.py --db "$bjm_demo_db" --run-id demo retry review-b
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2
python3 workflow.py --db "$bjm_demo_db" --run-id demo events
```

`--fail-before review-b` 在第二章审查的模拟调用开始前制造失败。第一次 `run` 后以 `status` 的节点状态判断结果，命令正常退出只表示返回了运行信息。随后几个命令启动新的进程，使用同一个 SQLite 文件继续工作。

## 验证审批绑定

上一步恢复后，先用 `status` 保存 `nodes.approve.token`，然后改第二章并恢复运行。

```bash
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
python3 workflow.py --db "$bjm_demo_db" --run-id demo edit draft-b '{"text":"第二章的新稿内容。"}'
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
```

先运行下面第一条来核对旧令牌会被拒绝，再把第二条的占位符替换为新令牌并批准。令牌前面的 `--` 告诉命令行后面不再是选项。

```bash
python3 workflow.py --db "$bjm_demo_db" --run-id demo approve approve -- '<编辑前的令牌>'
python3 workflow.py --db "$bjm_demo_db" --run-id demo approve approve -- '<编辑后的令牌>'
```

令牌由程序随机生成。v1.5.1 以前的版本生成的令牌约有 1/64 的机会以 `-` 开头，不加 `--` 时命令行会把它当成选项，报错退出（以 `-h` 开头时多半只打出帮助，退出码为 0），都不会批准。旧数据库里已经存下的这种令牌不会自动更换，照上面的写法加上 `--` 就能批准。

## 运行回归测试

```bash
python3 -B -m unittest discover -s tests -v
```

## 看懂两章联审

两章的初稿互相独立，各自交给对应的审查节点。审批等两份审查完成，再绑定当前候选和审查结果。执行记录可以用来定位节点开始、完成、失败、重新审查和等待审批的顺序。

| 场景 | 验收现象 |
|---|---|
| 其中一章审查失败 | 另一章已保存的结果继续有效。显式重试失败节点，再恢复整个运行 |
| 停止程序后重新启动 | 从 SQLite 重新读同一个运行。已保存且输入仍匹配的节点直接沿用 |
| 审批前修改其中一章 | 只重跑该章及受影响的下游。修改前发出的审批令牌失效 |
| 外部调用中途失联，无法判断是否送达 | 节点进入待核状态。等待提供方回执，取得已确认结果后用 `resolve` 写回。 |

## 接到实际任务时

- 每个任务节点声明输入和依赖。把提供方调用放在任务处理函数里，将实际稿件版本、请求 ID 和结果一并返回，便于恢复后对照。适配器应在正常返回前校验节点验收条件。审查失败或证据不足时应报告失败。
- 能确认重试安全的调用才标记为可安全重试。结果未知时等待提供方回执，已确认结果才用 `resolve <节点> '<实际结果 JSON>'` 记录。`retry` 适用于已失败且被声明为可安全重试的节点。已完成的外部动作如果未标记为可安全重试，关联的上游编辑会被拦住；另一次外部动作应由操作者重新授权并开启新的运行。
- 审批令牌标识当前审批版本。真实部署还需由接入系统校验操作者身份及审批权限。
- 每次运行使用创建时登记的图版本。改某一节点的输入用 `edit`；更换节点结构或状态格式时，新建运行并明确沿用的资料。原型独立运行，演示所用的生成和复核结果均来自本地模拟夹具。

## 设计参考

- Google ADK 的图工作流实战把流程分成明确节点，示范并行分支、汇总和人工审批。 [Graph Workflows in ADK](https://cloud.google.com/blog/topics/developers-practitioners/graph-workflows-in-adk-everything-you-need-to-know/)
- LangGraph 的中断与恢复提供了对照，特别是审批返回后节点可能重入，以及过期审批应被拒绝。 [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) · [LangGraph 发行记录](https://github.com/langchain-ai/langgraph/releases)
- Temporal 的持久执行和 Worker 版本固定用于参考进程恢复、外部调用和运行版本之间的边界。 [AI Framework Integrations](https://temporal.io/blog/ai-framework-integrations) · [Worker Versioning](https://docs.temporal.io/worker-versioning)
- OpenAI 的 Trace Grading 提供了依据执行过程定位问题的思路。本原型记录可供核查的事件，事件评分可由接入方另行实现。 [Trace Grading](https://developers.openai.com/api/docs/guides/trace-grading)
- EMNLP 2026 年 10 月综述区分了复用的图模板、某一次运行实际走过的图和执行轨迹，适合作为后续比较流程版本的参考。 [From Static Templates to Dynamic Runtime Graphs](https://aclanthology.org/2026.findings-emnlp.1393/)
