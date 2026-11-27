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
