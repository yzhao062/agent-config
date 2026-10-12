# Mac 持久存储审计与复查记录

2026-10-12 合并 Codex 的只读扫描与用户提供的 Claude 独立扫描，关注 `~/PycharmProjects/` 外的持久实验产物、agent 工作区、历史记录和缓存。确实存在重启不会清除的项目外数据，其中 Agy 的持久 scratch 最符合长期遗留的担心。当前决定：保留全部内容，之后复查，再决定是否迁移或清理。

本记录与 [Mac 设置与重装恢复指南](mac-mouse-preferences.md) 一起维护，只保存在 agent-config。此次仅新增审计文档和入口链接，没有删除或迁移审计对象，没有修改工具配置。

## 测量基线

容量基线复测于 **2026-10-12 00:55 PDT，America/Los_Angeles**。目录通过 `du -sk` 测量，统一换算为十进制 GB（1 GB = 1,000,000,000 bytes）。这是文件系统报告的分配量，不能据此预测删除后的精确可回收空间；APFS 克隆、硬链接和稀疏文件会影响解释。

原扫描中的部分数值使用 GiB，却标成 GB。例如 QEM 三个目录约 25.6 GiB，对应约 27.5 GB；Agy 总目录 9.6 GiB，对应 10.308 GB。下面以统一单位后的复测值为准。扫描期间有其他活跃 session，数值不是全盘同时冻结的快照。

`df -k /System/Volumes/Data` 在本轮显示已用约 **468.1 GiB**、可用约 **432.7 GiB**。`tmutil listlocalsnapshots /` 未列出 Time Machine 本地快照，该结果不等于检查了所有类型的 APFS 快照。

## 项目目录外的实验数据

| 路径 | 2026-10-12 大小 GB | 内容及复查判断 |
| --- | ---: | --- |
| `~/qemscore-r8/` | 9.901 | QEM 实验数据、代码和 release 副本。仍有脚本引用，先核对复现依赖 |
| `~/qemscore-r9/` | 12.695 | 上游仓库、数据、打包产物和实验输出；其中 `upstream` 约 11.358 GB |
| `~/qemscore-r10/` | 4.916 | `fresh-v1` 实验数据，仍被 round 10 脚本引用 |
| `~/Documents/QEMScore-release-assets/` | 0.836 | Claude 扫描补充发现的 QEM 发布资料 |
| `~/Documents/ab-directions-scratch-2026-10-11/` | 0.739 | Claude 扫描补充发现的 A/B 方向探索目录；普通 Documents 目录不会因重启清空 |
| `~/data/` | 0.048 | 当前包含 `inj_actor` 和 `SKAB` 数据集，属于项目外持久下载位置 |

QEM 三个主目录合计 **27.512 GB**。两处 Documents 目录合计 **1.575 GB**。这些是散落在项目目录外的资料，是否已经失去用途需要分别确认，不能按目录年龄直接删除。

来源证据：[qem-bench 默认数据路径](../../qem-bench/tools/pooled_absolute.py) 指向 `~/qemscore-r8/`；[round 10 运行脚本](../../internal-writing/docs/qemscore-mlst/round10-2026-10-07/scripts/run_round10.sh) 引用了 r8、r9 和 r10。[pyod3 图实验脚本](../../pyod3-experiments/scripts/phase_b_graph_fit.py) 把部分数据集下载目录设为 `~/data/<name>`。

## Agent 持久工作区与记录

下表同时列出总目录和重点子目录。**子目录已经包含在总目录容量中，不要把整张表相加。**

| 路径 | 2026-10-12 大小 GB | 内容及复查判断 |
| --- | ---: | --- |
| `~/.gemini/antigravity-cli/` | 10.308 | Agy 总目录，包含下列 brain 和 conversations |
| `~/.gemini/antigravity-cli/brain/` | 7.460 | 约 500 个任务目录，含实验 scratch、代码克隆、数据和虚拟环境；重点复查 |
| `~/.gemini/antigravity-cli/conversations/` | 2.709 | 会话数据库及 SQLite WAL 文件 |
| `~/.codex/` | 19.044 | Codex 总目录，包含下面的会话、包、工作树、scratch 和数据库 |
| `~/.codex/sessions/` | 9.749 | 会话 JSONL；扫描中单个文件最大约 605 MB（577 MiB） |
| `~/.codex/thread_history_1.sqlite` | 2.852 | 单个持久历史数据库，同轮定向检查所得；已包含在 `.codex` 总量中 |
| `~/.codex/worktrees/` | 0.888 | 两个 NSF proposal 工作树，属于需要核对用途的实际工作目录 |
| `~/.codex/scratch/` | 0.143 | `csci699-visual-vet-20261011`；虽然名为 scratch，位于 home 内，重启不会清空 |
| `~/.claude/projects/` | 6.575 | Claude 会话、子 agent 记录和项目记忆 |
| `~/.cache/codex-runtimes/` | 1.635 | Codex 依赖运行时，属于安装资源 |
| `~/Library/Caches/Codex/` | 1.831 | Codex 应用缓存，位于 `.codex` 目录之外 |

Codex 的 `.codex`、`codex-runtimes` 和 `Library/Caches/Codex` 三处合计约 **22.510 GB**；这个数值包含日志、数据库、安装包和工作目录，不能全部叫作日志。

### Agy 的持久 scratch

`brain` 下已有以下较大任务目录，容量来自同日早一轮文件元数据扫描，保留 UUID 便于复查：

| brain 下的任务目录 | 大小 GB | 主要内容 |
| --- | ---: | --- |
| `bd014e8b-7bad-49ee-ba46-47c27d6dac9c/` | 4.027 | `scratch/r1/dsclone` 约 3.472 GB；另有两套虚拟环境，合计约 0.320 GB，及多个代码副本 |
| `4d70e583-d847-42a9-afa8-4ae6ce84611b/` | 1.141 | `scratch/full2.json` 约 603 MB，`scratch/by2.pkl` 约 492 MB |
| `1afdd8c4-8056-457c-a810-0777cbd760e0/` | 0.890 | `scratch/tau2-bench` 克隆及其数据、结果文件 |

这三处定向 `lsof` 检查没有发现打开的文件句柄，但这不能证明任务已经结束或内容可以删除。它们位于 home 下，属于持久存储，系统临时目录的清理不会覆盖这里。原 Claude 报告把 9.6 GiB 标在 brain 路径上；复测显示该数字对应整个 `antigravity-cli`，brain 本身为 7.460 GB。

### 临时工作区留下的 Claude 历史

`~/.claude/projects/` 中约 **604 个目录、2.303 GB** 的记录对应 `/private/tmp/` 或 `/private/var/folders/` 下的工作区。即使原工作区后来消失，持久会话记录仍可能保留。该容量是 6.575 GB 总量的一部分，不另行累加。这些记录可能仍有恢复或追溯用途，暂不判为垃圾。

## 工具版本与下载缓存

| 路径 | 2026-10-12 大小 GB | 内容及复查判断 |
| --- | ---: | --- |
| `~/.codex/packages/` | 4.323 | 包含 standalone CLI 和 app-server-daemon；已包含在 `.codex` 总量中 |
| `~/.codex/packages/standalone/releases/` | 3.990 | 12 个版本，从 0.156.1 到 0.162.1；检查时 `current` 指向 0.162.1。此行已包含在上一行中 |
| `~/.local/share/claude/versions/` | 0.717 | 三个 Claude Code 原生版本：2.1.294、2.1.295、2.1.296 |
| `~/.cache/huggingface/` | 9.681 | 主要为 Qwen3 4B 权重约 8.061 GB、Qwen3 0.6B 约 1.519 GB，以及较小模型和元数据 |
| `~/Library/Caches/pip/` | 2.292 | Python 下载和构建缓存 |
| `~/miniforge3/pkgs/` | 2.320 | conda 包缓存；可能与已安装环境存在硬链接 |
| `~/Library/Application Support/Claude/vm_bundles/` | 12.101 | Claude 桌面 App 的虚拟机资源，约 11.269 GiB；与项目输出分开判断，目前没有证据表明其无限累积 |

原报告中的“三个约 235 MB 的旧版 CLI”与 Claude Code 的版本文件相符；Codex standalone 实际有 12 个版本。当前安装资源与历史版本需要分开核对，不能整目录清空。

缓存会随新模型、新 revision 或新依赖下载增加；重复下载同一份已缓存文件不一定增加容量。持久会话记录会随新任务产生。现有扫描证明了文件仍在，但没有确认所有工具的自动保留上限，因此不能据此断言“永远只增不减”。模型缓存和包缓存也可能被离线复现或活跃环境使用，清理前要核对依赖。

## 已处理资料与潜在写入入口

用户提供的另一 active session 已把 `~/research-data/` 移到 `~/PycharmProjects/research-data/`，并更新路径记录，其中 `agent-when-to-ask/` 保存两个实验存档。本轮确认 `research-data` 总目录为 **0.044 GB**。该 session 另报告已删除约 1.2 GB 的 API 调查克隆，本轮不把它计入现存容量，也不重复执行清理。

[pyod3 substrate pilot](../../pyod3-experiments/scripts/substrate_pilot.py) 默认把 trial 工作区写到 `~/.cache/pyod3-substrate-trials/`。该目录在本轮不存在，但默认路径仍可能在未来运行时产生持久实验工作区。[grade 下载脚本](../../grade/experiment/agent_graph_openhands.py) 等调用 `hf_hub_download` 时没有显式指定项目内缓存目录；实际落点取决于运行环境的 Hugging Face 配置，不能把目前所有 9.681 GB 都归因于 grade。

目前采用的存放原则是：项目产出放仓库或会话的系统临时目录；需要长期保留且不进入 Git 的资料统一放 `~/PycharmProjects/research-data/`。此原则并未自动约束工具自己的缓存、历史库和 Agy brain，也没有在本轮改写所有实验脚本的默认路径。

## 下次复查范围

优先复查 Agy 的三个大 scratch 目录、Documents 的方向探索目录和 QEM release 副本，确认是否有唯一结果、复现依赖或活跃任务，再决定迁移或清理。会话记录、工具版本、模型缓存和桌面 VM 分别按各自保留机制判断，不用同一套删除规则。

复查时使用相同路径和 `du -sk` 口径，记录日期、GB 和相对于本次基线的变化；新出现的路径也加入表中。至少核对新文件的来源、最后写入时间、进程使用情况，以及持久产物是否已在仓库或 `research-data` 中有完整副本。单次测量不能给出增长率。

`/private/tmp/claude-501/` 和 `/private/var/folders/.../T/` 属于本次用户排除的系统临时范围，不计入上述持久目录清单。这里不以“重启必然清空所有临时文件”作为清理保证。有意保留的备份和正在使用的 Python 环境也不按僵尸路径处理。

后续复查由用户再次发起；本次没有设置定时扫描或自动清理。
