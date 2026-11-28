# Mac 存储审计交接（2026-11-27）

在本机的 `~/PycharmProjects/agent-config` 工作。先读 [私人扫描 skill](../reference-skills/mac-storage-audit/SKILL.md) 和 [长期审计记录](mac-storage-audit.md)。长期记录最近一节实测为 11 月 21 日；下面补接 11 月 22 日、26 日的调查。本机周任务 ID 为 `mac`，洛杉矶时间周六上午 11 点只读运行。另一个 session 可从这个仓库独立复核。

## 接手时先查什么

用户最关心已结束的实验把唯一的原始结果留在 scratch。先查任务是否已交付，再将具体文件与仓库、归档或集群中的候选副本按内容核对。源码可用只能说明可以重跑。此次交接供只读复核；历史清理授权针对当时列明的路径。

以下是 11 月 26 日发现的线索，路径均相对于 `~/.gemini/antigravity-cli/brain/`。未核实这三组原始输出在 scratch 之外有相同副本，任务结束情况也待查。

| 所属评测 | 具体文件 |
| --- | --- |
| Ironheights | `64af075d-ef85-4271-b2f6-4b263ae945a5/scratch/fresh-env/ledger.json`（63,090 bytes） |
| Arquia | `ff31d40a-7750-49d8-8c42-d2c275a3f085/scratch/checks-v0.2.4/` 中的 41 个 `*.receipt.json` 和对应 stdout |
| Agent Retry Rodeo | `655883a1-4dc9-45e8-97f8-17d7ad6fdc21/scratch/before/results.json` 与同一 scratch 下的 `after/results.json` |

另一处优先项是 `/private/tmp/claude-501/-Users-yzhao062-PycharmProjects-NSF-Proposal-Template-Yue/ccd1745f-86db-4a95-91de-e97b94a79425/scratchpad/vet-wt`。11 月 26 日有五份修改过的 `research-support-*.md`，需与 NSF 主仓库核对。同日 `/private/tmp/portal-vet.OZv33N4P/repo` 内两份资助 CSV 和两个 manifest 已与来源项目 `meta-finder` 逐字节核对相同；该判断只覆盖这四个文件。

## 容量与已查事项

11 月 22 日 Data 卷可用约 274 GB，18 个大型审查状态目录合计约 77.7 GB。11 月 26 日晚复扫结束时约 631 GB 已用、333 GB 可用，原先的 18 个目录已不在原位置。当晚开始时另有三个审查快照，合计 5.86 GB，复测时原路径也已消失。提交 `b95c825` 为 dispatcher 加入退出时清理快照的逻辑。目录消失的具体原因需单独取证。

11 月 26 日核对了两个临时 Git 工作树。GRADE 的 `/private/tmp/grade-arr-20261126-publish` 为 8.41 GB，提交 `bd878deb`；NSF 的 `/private/tmp/meta-note-push-20261125` 为 2.92 GB，提交 `baa4cb99`。当时两者的提交均已包含在实时远端 main 历史中，工作区干净，仅 GRADE 有一份忽略的 Python 字节码。后续若考虑移除，先重新确认使用状态和本地改动。

历史记录列出的三个旧 Agy UUID（`bd014e8b…`、`4d70e583…`、`1afdd8c4…`）去向仍未确认。用户明确说明 `~/Documents/ab-directions-scratch-2026-10-11/` 是本人删除，这一项已结案。此前归档的 trial-merge-1 和旧 PyCharm 历史在 `~/PycharmProjects/research-data/storage-retirement-2026-11-16/`，含 README、校验清单和 closeout.json。

11 月 26 日的临时证据目录为 `$TMPDIR/storage-1126.LuPrad/`，其中 `measure` 为容量采样，`agent-io/tmp.md` 和 `agent-io/risk.md` 为两路 prun 调查，`panel/Review-*.md` 为 Claude、Agy、Grok 对首轮容量及恢复判断的复核。临时证据可能被系统清理。复测时沿用私人 skill 的十进制 GB 口径，并标明不可读目录。

## 11 月 27 日复核结论与第一批清理

上面几项待查已有结论。三组 Agy 评测的任务均已交付；原始文件在各自 brain scratch 之外没有相同副本，结果文本还保存在对应 brain 的 `.system_generated/logs/transcript_full.jsonl` 中。NSF 的 `vet-wt` 是审查用的副本，目录已不在；对应提交 `46a8ba6a` 已在本地记录的远端 main 中，已消失的工作副本无法再逐字节比较。系统于 11 月 23 日 21:41 重启。核查时仍存在的临时条目都创建于重启之后。18 个审查目录可能在重启时被清理，未找到逐项删除记录。三个旧 Agy UUID 目前无法在 Agy 中恢复；Agy 1.5.14 及以前启动时只保留最近 500 个对话，可能解释了它们的缺失。

第一批删除的是可以重新生成的持久缓存，共 8 项、998 个条目，manifest SHA-256 为 `4dd632134e98ab5e1605616cec5eec45e546070b7480b4cfc8f7e247c40f03c1`：

| 项目 | GB | 恢复方式 |
| --- | ---: | --- |
| 27 个 repo 中未被 `pack-lock.json` 引用的 974 个 pack cache 槽 | 19.67 | 所有锁定槽均保留；核查时涉及的 41 个 commit 在 GitHub 上仍可访问 |
| `~/qemscore-r9/upstream/ml-qem` | 11.34 | `git clone https://github.com/qiskit-community/ml-qem.git`，再 `checkout --detach b1eccf8cf5ef4e9e498f3fe66e03951bc6b4a4d3`；`run_r9_local.sh` 和 `shift/run_shift.sh` 重跑前需要 |
| Hugging Face 的 Qwen3-4B-Instruct-2507 及其 3 个独占 blob | 8.05 | Hub 修订版 `cdbee75f` 仍公开 |
| `~/.cache/agentpile-dev` 中的 venv（保留 `recipes/train/venv/hf-home`） | 6.00 | 重建 venv |
| Claude 桌面版中断下载的两个 rootfs 文件 | 5.93 | 应用下次启动 Cowork 时重下 |
| pip 的 `http-v2` 和 `http` 缓存 | 4.32 | pip 按需重建 |
| SWE-rebench 的未完成下载和空快照 | 2.68 | 完整 parquet 在 `research-data/agentpile-cache`，摘要已核对 |
| `~/Library/pnpm/store/v11` | 2.53 | pnpm 重新拉取 |

删除脚本按 manifest 摘要绑定，逐项复核后才删，并沿祖先目录用 `O_NOFOLLOW` 固定父目录。三轮复核后，Codex、Agy、Grok 在各自列出的条件下同意删除全部 8 项。最终总评为 Codex、Agy 要求修改，Grok 通过；两项修改意见针对不在删除流程中的沙箱测试脚本，该脚本修复后已在临时目录实测通过。Codex 另要求执行期间没有进程写入目标，执行前已用 `lsof` 和进程检查确认。

执行时间为 11 月 27 日 15:30 至 15:33：998 项删除，0 跳过，0 部分失败。Data 卷可用空间从 332.0 GB 升到 385.4 GB，增加 53.4 GB；按分配块统计为 60.52 GB，多出的 7.1 GB 原因未确认。本机没有本地快照，pack cache 中也没有硬链接，APFS 写时复制共享的块是一种可能。执行后已逐项核对保留项。各 repo 的锁定 pack 槽、ml-qem 旁的 `upstream/qlear`、pip 的 `wheels/` 和 VM 的 `sessiondata.img` 均完好。Hugging Face 的 token、共享 tokenizer blob、Qwen3-0.6B 和 Qwen3-14B，以及 agentpile 的 `~/.cache/agentpile` 链接、`hf-home` 和 SWE parquet 也均完好。

脚本、manifest、执行日志和三轮复核在会话 scratchpad `/private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/b2fe6cf1-851d-493f-99bf-1d804d5f5440/scratchpad/deadwood-batch1/`，临时目录可能随系统清理而消失；本节是保留下来的记录。

第二批尚未执行。先把开头表中三组评测的唯一原始文件保存到持久目录，再处理 Agy brain。其他待处理项需要先核验恢复路径并保存唯一副本，再决定是否删除：Codex worktree（用 `git worktree remove`）、figure1 JSON、github.io scratch 中的证据、agent-insurance 的 PDF、旧 Claude workflow 记录，以及 Grok 审查会话（用 `grok sessions delete`）。让存储保持稳态、不再依赖这类清理的机制见[存储稳态计划](followups/2026-11-27-storage-steady-state.md)。

## 有意保留的备份

`~/Documents/Winref` 是用户从上一台 Windows 电脑迁移时留下的备份，保留至今是为了日后可能需要的文件。目录创建于 2026 年 9 月 21 日。11 月 27 日按分配块计，备份约占 143.4 GB，与 11 月 7 日长期记录中的数值相同，整个 `~/Documents` 约占 144.8 GB。用户预计几个月后可能会删除这份备份。在用户作出决定前，各批清理均跳过该目录，审计只报告其大小。旧电脑或其他磁盘上是否还有完整副本尚未核实，删除前按唯一副本对待。若用户决定删除，先按 [Mac 设置与重装恢复指南](mac-mouse-preferences.md) 中的清单和目录内的 `START-HERE.md`，确认独有文件和未迁移的仓库都已迁出。不要在该目录内运行 Git；各仓库的 Git 状态记录在目录内的 `migration-handoff/git-handoff-current.json`。
