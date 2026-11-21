# Mac 持久存储审计与复查记录

2026-10-12 合并 Codex 的只读扫描与用户提供的 Claude 独立扫描，关注 `~/PycharmProjects/` 外的持久实验产物、agent 工作区、历史记录和缓存。2026-11-07 清理四个旅行备份目录。2026-11-16 再次扫描，并在用户授权后归档试验合并与旧 IDE 历史、清理四个历史遗留路径；2026-11-17 补录结果。以下按日期保留测量和处置记录。

本记录与 [Mac 设置与重装恢复指南](mac-mouse-preferences.md) 一起维护，只保存在 agent-config。复查使用私人 [mac-storage-audit skill](../reference-skills/mac-storage-audit/SKILL.md)。扫描默认只读，清理需要用户授权。

## 每周扫描

Codex 任务「Mac 每周存储审计」（ID `mac`）于每周六上午 11:00 按洛杉矶当地时间运行。任务使用本页链接的私人 skill，在原聊天中用中文报告，与最近一次可比实测对照。报告记录 Data 卷已用和可用空间、主要目录变化、权限缺口，以及需要处理的具体路径。

优先检查已结束任务留在项目外的持久 scratch、旧环境和可能独有的研究成果。对每项记录所属任务、使用情况和恢复证据，复查已清路径是否重新出现，并追踪下文三个旧 Agy 目录的归档线索。周任务只读运行。删除、归档、修改项目、提交、推送和调用付费 reviewer 均需另行授权。

## 2026-11-21 周六手动扫描

10:24 PST 开始扫描。Data 卷已用 **589.004 GB**、可用 **379.352 GB**，比 11 月 16 日清理完成时多 **16.437 GB** 可用空间。扫描期间使用十进制 GB，目录分配量与卷可用空间分别比较。

| 主要路径 | 11 月 16 日清理前 GB | 11 月 21 日 GB |
| --- | ---: | ---: |
| `~/PycharmProjects/` | 159.664 | 163.421 |
| `~/Documents/` | 148.901 | 148.901 |
| `~/Library/` 可读部分 | 64.156 | 54.122 |
| `/Applications/` | 41.886 | 42.521 |
| `~/.codex/` | 21.094 | 22.210 |
| `~/.cache/` | 20.277 | 17.926 |
| `~/.claude/` | 15.067 | 14.772 |
| `~/.gemini/` | 9.048 | 3.371 |

home 扫描有 498 条错误，受保护目录统计不全。`/Library`、`/private/var/folders` 和 `/private/tmp` 的可读部分分别为 9.875、3.973 和 0.538 GB。表内 Library 两次均为部分可读范围。

上次清理的四个原路径均未重现，两个归档文件仍在且大小与记录一致。Codex 运行时目录仅有当前版本（1.747 GB），旅行备份目录为空。Agy brain 从 6.801 GB 降至 1.159 GB，三个旧 UUID 仍不在原位置。Spotlight 与 research-data 内的文件名搜索均未找到 `full2.json` 或 `by2.pkl`，恢复来源继续待查。

research-data 从 40.505 GB 增至 41.352 GB，包含上次清理归档和 0.209 GB 的 `internal-writing/git-reconcile-2026-11-16/`。上次记录的 internal-writing 分叉已解决，本地 HEAD 与实时远端 main 同为 `073e7cb6`。0.750 GB 的付费实验原始结果和 CatchBench 人工回传表仍在本机，离机副本待核实。Time Machine 未配置目的地，Data 卷未列出 APFS 快照。

## 2026-11-16 扫描与历史遗留处置（2026-11-17 补录）

本轮重点是任务结束后无人维护的永久性历史遗留，以及可能无法恢复的成果。协调者完成扫描，用户授权的 `prun` Agy 复核增长和旧环境，Grok 复核恢复风险；两个 dispatcher 均成功退出，实际模型核验均为 `status=ok`。随后用户明确授权清除无用内容、归档独有内容。检查与删除由协调者执行，未修改活跃项目或同步其 Git 历史。

### 扫描容量与增长

时间均为 America/Los_Angeles，大小为十进制 GB。11 月 16 日约 16:43 开始扫描，Data 卷已用 **610.861 GB**、可用 **357.486 GB**，比 11 月 7 日清理后的可用空间减少约 **13.195 GB**。扫描期间应用仍在写入，以下目录值不是冻结快照，也不是清理后的新基线。

| 路径或范围 | 扫描时 GB | 较 11 月 7 日 GB | 说明 |
| --- | ---: | ---: | --- |
| `~/PycharmProjects/` | 159.664 | -3.094 | research-data 包含在内 |
| `~/Documents/` | 148.901 | 约 0 | Winref、QEM 发布资料等仍在 |
| `~/Library/` 可读部分 | 64.156 | +8.583 | 权限覆盖可能不同，只作可读范围对照 |
| `/Applications/` | 41.886 | -0.191 | 应用安装资源 |
| `~/qemscore-r8/`、`r9/`、`r10/` | 27.490 | 约 0 | 本轮未清理 |
| `~/.codex/` | 21.094 | +1.243 | 会话、数据库、运行资源与工作树 |
| `~/.cache/` | 20.277 | +2.068 | 包含下述 Codex 旧安装残留 |
| `~/.claude/` | 15.067 | +1.187 | 主要为项目会话记录 |
| `~/.gemini/` | 9.048 | +6.770 | brain 6.801、conversations 1.904；活跃复核期间继续增长 |
| `/private/var/folders/` 可读部分 | 3.557 | -6.288 | 不推断具体自动清理机制 |
| `/private/tmp/` 可读部分 | 0.004 | -0.931 | 不保证重启清除所有临时文件 |
| `~/repo-backups/` | 0 | 0（与上次清理后比较） | 旅行备份没有重新累积 |
| `~/PycharmProjects/research-data/` | 40.505 | +1.923 | 嵌套在项目总量内，不另行相加 |

`internal-writing/.git` 从 14.843 GB 降到约 4.267 GB，未确认缩小机制。Library 的 Caches 约 20.870 GB、Mobile Documents 约 19.199 GB；Agy 新增的大目录包含近期依赖环境，不能统称为僵尸路径。约 1.003 GB 的 agentpile probe 数据路径和大小与完整缓存对应，差异集中在 15 个小型元数据文件；未做内容哈希验证，恢复风险较此前降低，但不能称为已验证的逐字节副本。

扫描覆盖 home、两处系统临时目录、Applications、Library 和 `/opt`。home 扫描有 489 条错误，主要是 Library、Photos 权限限制；不可读区域未计作零。`du` 是分配量，父子目录、APFS 共享块、硬链接、权限缺口和活跃写入使其不能机械相加还原 `df`。本机未配置 Time Machine 目的地，Data 卷未列出 APFS 快照；未核验离线外置盘、集群和所有云端副本。

### 已完成处置的四个路径

| 原路径 | 删除前 GB | 结论与执行结果 |
| --- | ---: | --- |
| `~/.gemini/antigravity-cli/brain/a64521a1-09c5-41ae-b5e0-35747817e7ea/scratch/trial-merge-1/` | 0.970 | 确认是 research-impact 的试验合并；完整归档工作区和 `.git`，校验后删除原目录 |
| `~/Library/Caches/JetBrains/PyCharm2026.2/` | 5.011 | 归档 LocalHistory、fileHistory、editor、restart 后删除旧版本目录；活跃 2026.3 保留 |
| `~/.cache/codex-runtimes/codex-runtime-install-DLrBSx/` | 2.041 | 旧 bundle `26.1105.12137` 的安装包与解压残留，已删除 |
| `~/.cache/codex-runtimes/codex-runtime-install-LS86pC/` | 0.338 | 旧安装包与空 payload，已删除 |

trial HEAD 为 `995770192add74af070cbc3a8363f5a197ff22d4`。两个父提交 `74ea4f379f157c28219d7b5c1a6ed88dd429dd86`、`f0fd478381f437b09cb1c16dfac47f6b1bbcb01c` 均在 `~/PycharmProjects/research-impact` 中；15,363 个受跟踪条目只有 `.gitattributes`、`.gitignore` 的 blob 版本不在该仓库可达历史对象清单里。此前只检查 internal-writing 得出的“来源未明”已解决。trial 没有修改、未跟踪或忽略文件，没有符号链接和外部 Git object alternates；保留完整归档以保存试验提交和原始状态，不把本地对象存在误写为远端备份证明。

归档位于 `~/PycharmProjects/research-data/storage-retirement-2026-11-16/`，包含 README、两个压缩包、逐文件 SHA-256 manifest 和 `closeout.json`。trial 的 15,573 个文件、PyCharm 历史的 457 个文件均从压缩包读回，与源文件 SHA-256 比对通过；删除前再次核对文件清单、大小和修改时间。恢复时在新目录执行 `tar -xzf ARCHIVE -C NEW_DIRECTORY`，不要直接覆盖活跃 IDE 的历史。

| 归档 | 压缩包 bytes | SHA-256 |
| --- | ---: | --- |
| `trial-merge-1.tar.gz` | 535078175 | `b14d659b7adae0a888728539a9c1c0e89488f9fbe4f5d9ca4d111f33d19edd33` |
| `pycharm-2026.2-history.tar.gz` | 1154494 | `313f907d442e2d1d434935065e9cafb08959bd49ec6eb76283c2278570957fa7` |

归档和记录共约 **0.542 GB**，四个源目录原分配量共 **8.360 GB**，扣除归档后目录分配量净减少约 **7.817 GB**。删除前（归档已写入）Data 已用 **613.594 GB**、可用 **354.754 GB**；约 23:29 完成后已用 **605.432 GB**、可用 **362.915 GB**。删除阶段可用空间增加约 **8.162 GB**，与目录净减少不是同一口径，期间还有其他应用写入。最终使用非 force 的 `rm -r`，四个原路径均确认不存在，当前 Codex runtime 和 PyCharm 2026.3 均保留。归档是本机集中存放，尚未验证离机副本。

### 未结案：三个旧 Agy 目录去向不明

以下路径均相对于 `~/.gemini/antigravity-cli/brain/`。大小是 **2026-10-12 历史测量值**，不是现存占用；合计约 6.058 GB。本轮没有删除它们，它们在清理前就已不在原位置。

| 原目录 UUID | 历史 GB | 历史内容与当前状态 |
| --- | ---: | --- |
| `bd014e8b-7bad-49ee-ba46-47c27d6dac9c` | 4.027 | `scratch/r1/dsclone`、虚拟环境及代码副本；未确认回迁或归档位置 |
| `4d70e583-d847-42a9-afa8-4ae6ce84611b` | 1.141 | `scratch/full2.json`、`scratch/by2.pkl`；未找到可确认的替代副本 |
| `1afdd8c4-8056-457c-a810-0777cbd760e0` | 0.890 | `scratch/tau2-bench` 及数据、结果；未确认回迁或归档位置 |

本轮核对原路径、Spotlight 特征文件名和 research-data 文件名，未找到这三个目录名或 `full2.json`、`by2.pkl`。用户此前表示不确定是否归档，需要之后查。有限范围的搜索不证明数据丢失，也不证明 Agy 自动轮换；不能把这三项记为清理完成或可恢复。结案需要定位与原任务对应的归档、远端或集群结果，并验证内容。保留这些具体标识供追查，不再把已消失目录当作可释放空间。

### 其他恢复来源待核对

新增 `research-data/llm-recruitment-assessment/runs-2026-11-14` 约 **0.750 GB**，README 声明为不进 Git 的原始付费实验结果；重跑不能恢复同一次观测。其 datasets 约 0.474 GB 来源混合，并非全为固定 revision 的 Hugging Face 下载。`research-data/usc-email` 增至约 **0.705 GB**，尚未与邮箱或其他导出逐文件比对。

CatchBench 人工回传 `catchbench-human-slice-2026-11-12/2-put-returned-file-here/second-file/tool-check.xlsx` 为 16,654 bytes，另有 internal-writing 中未跟踪的 `human_labels.json`；未核实离机副本，未读取 workbook 或个人申请材料。扫描时 internal-writing 本地 HEAD `8b30a492537049855210dc8d868cba741a02b8f8` 与实时远端 main `7e6216d6e147632c962dc8f437d335e273209650` 分叉，本地独有 19 个提交、远端独有 36 个，默认 status 有 146 条记录。此为当时状态，不代表后续仍未同步；本轮没有合并、提交或推送该项目。

后续按具体遗留项结案：仍在使用、已归档、已删除，或有明确待查证据的恢复来源未明。活跃环境和用途清楚的大目录不因体积大而列为垃圾。此次四个路径已结案，三个旧 Agy 目录与上述恢复来源继续单列；未设置自动删除。

## 2026-11-07 扫描与旅行备份清理

日期和时间均为 America/Los_Angeles，容量统一为十进制 GB。扫描覆盖 home、主要项目、两处系统临时目录、Applications 和可读的 Library；使用 `df -k`、`du -k`、文件哈希、只读 Git 历史和远端引用检查。Photos、部分 Library 和系统目录受权限限制，未读取部分不能当作零占用。扫描和清理并非同时发生，期间其他任务继续运行。

### 容量与主要占用

| 测量时点 | Data 已用 GB | 可用 GB | 说明 |
| --- | ---: | ---: | --- |
| 2026-10-25 上轮扫描 | 634.120 | 332.172 | 本聊天中的实测记录，补录作比较基线 |
| 2026-11-07 约 14:42，扫描开始 | 594.227 | 373.140 | 比上轮可用空间增加约 40.968 GB |
| 2026-11-07 晚间，清理前 | 602.106 | 365.261 | 与下午扫描相隔数小时，不能把期间变化算作清理效果 |
| 2026-11-07 约 20:17，清理完成 | 596.686 | 370.681 | 清理前后可用空间净增加约 5.420 GB |

| 路径或范围 | 扫描时大小 GB | 与 10 月 25 日比较及内容 |
| --- | ---: | --- |
| `~/PycharmProjects/` | 162.758 | 约 +14.551；包含下述 research-data，不重复累加 |
| `~/Documents/` | 148.901 | 大致不变；其中 Winref 为 143.447 |
| `~/Library/` 可读部分 | 55.573 | 约 +5.680；包含 App 数据、缓存和 iCloud 本地文件 |
| `/Applications/` | 42.077 | 约 +2.886 |
| `~/.codex/` | 19.851 | 约 +1.334；含历史、数据库、安装资源和 worktrees |
| `~/.claude/` | 13.880 | 约 -1.559 |
| `~/.gemini/` | 2.278 | 约 +0.146；不要与旧表的 antigravity-cli 子目录直接比较 |
| `~/.cache/` | 18.209 | 约 +0.340 |
| `~/qemscore-r8/`、`r9/`、`r10/` | 27.490 | 大致不变，混有代码、数据和实验产物 |
| `/private/tmp/` 可读部分 | 0.935 | 上轮约 33.555 |
| `/private/var/folders/` 可读部分 | 9.845 | 上轮约 41.782；两处临时范围合计减少约 64.6 GB |
| `~/repo-backups/` | 8.958 | 本轮随后授权清理，完成后为空 |
| `~/PycharmProjects/research-data/` | 38.582 | 包含在项目总量内；其中 agentpile-cache 为 34.814 |

`internal-writing` 从约 20.508 GB 增至 27.088 GB，其 `.git` 从约 8.32 GB 增至 14.843 GB，是项目增长的明显来源。目录大小不能机械相加还原 `df`：父子目录重叠、APFS 共享块、硬链接、权限缺口及活跃写入都会影响比较。未确认临时目录减少的具体清理机制。

### 已执行的清理

用户已回家、旅行结束，明确授权删除无用旅行备份，并要求用本地 `prun` 一起决策。协调者核对后，两组 Agy worker 均使用 `gemini-3.8-flash-high`，一组复核 NSF，另一组复核其余三个目录。worker 只读，删除由协调者执行。 <!-- agent-models: allow -->

| 已删除路径，位于 `~/repo-backups/` | 原大小 GB | 删除依据 |
| --- | ---: | --- |
| `travel-work-backup-20261027/` | 1.476 | 工作区干净，无未跟踪或忽略内容；本地 HEAD 与 GitHub main 均为 `94fb42da08223c97266848bb715038717e45d798`。33 个归档分片的大小及 SHA-256 已校验，远端仓库保留 |
| `trading-doc-travel-20261027/` | 0.135 | 2,582 个文件与当前项目相同，11 个旧版本在 Git 历史中；GitHub 比较确认旅行提交 `3c10549f` 已包含在当时远端 `43c2d1a9` 的历史中。使用不带 force 的 `git worktree remove` 移除，保留分支 |
| `return-sync-20261104/` | 0.177 | MAAD 两组 251 和 247 个文件、trading 两组各 8 个文件均匹配当前项目；NSF 的 13 个原始或历史版本在 Git 历史中。两个不同的 `.merged` 文件仍带冲突标记，是中间产物，其余为同步报告 |
| `nsf-travel-20261026/` | 7.170 | 主快照 15,652 项原位置一致、270 个文件有迁移后的相同副本、125 个旧版本在 Git 历史中。root bundle 的 52 个引用目标和 microscopy stash 均在当前仓库找到；剩余内容按下段判断为过期过程材料 |

NSF 主快照未匹配的 15 个文件合计约 2.22 MB，主要是约 2.04 MB 的旧 UMaine 编译 PDF、LaTeX 日志、缓存、IDE 和 agent 配置、工具脚本及小型忽略规则。附加工作区中 324 项匹配当前内容、5 项匹配历史，另 35 项主要是合并决策、检查脚本、渲染检查副本及 Git 中间状态。结合旅行已结束和回迁证据，决定不因这些旧版本字节不同而继续保留完整备份。此判断不意味着每个中间文件都有异地副本。

NSF 发布提交 `8d50119fe6fc5e54700b157bb8ce772b8e2ccf34` 已包含在核对时远端 `2a6af178` 的历史中；microscopy stash `5cfcdf610812503fba24e7485838929f6445361a` 在当前 `proposals/nsf-ai-datasets-2026-due-1104/overleaf` 找到。部分克隆缺少 promisor blobs，检查使用 `GIT_NO_LAZY_FETCH=1` 和 `rev-list --missing=print`，没有为审计自动下载缺失对象。

删除使用 `git worktree remove` 和 `rm -r`；NSF 只读备份内的文件及目录先恢复用户写权限。完成后确认 `~/repo-backups/` 为空、trading worktree 列表仅保留主工作区。删除目录原统计合计约 8.958 GB，磁盘可用空间净增加约 5.420 GB；不把目录总量当作实际释放量。GitHub 旅行归档及活跃项目保留，没有清理模型缓存或研究数据。

### 仍需核对的恢复来源

下表是待核对清单，不是删除候选，也不表示已证明不存在其他副本。

| 优先项 | 大小 GB | 已确认情况与下一步 |
| --- | ---: | --- |
| 三个旧 Agy brain 任务，UUID 见历史表 | 原合计 6.058 | 10 月 25 日及 11 月 7 日均不在原位置。用户不确定是否另存；本次 Spotlight 和 Documents、research-data、现有 Gemini 目录的精确文件名检查未找到 `full2.json`、`by2.pkl`。后续查归档、远端任务结果或改名副本；不能认定已丢失，也不能认定由自动保留机制删除 |
| `research-data/agent-observer-effect/` | 2.344 | 原始 run outputs、云端拉取和分析材料仍在；README 要求视作独有。需要确认集群或其他离机副本，重新跑实验不等于恢复原始记录 |
| `research-data/agent-when-to-ask/` | 0.969 | 日志、工作结果和存档仍在，混有可下载的公开代码；未验证全部原始结果有备用副本 |
| `research-data/llm-dreaming/` | 0.178 | calibration 数据及结果仍在，备用副本未验证 |
| `research-data/maad-bench-dgx-backup-2026-10-18/` | 0.129 | DGX 历史备份仍在，需确认 DGX 原始副本或其他归档 |
| `research-data/maad-bench-release-update-2026-10-18/` | 0.088 | 历史待应用更新仍在；本轮没有逐项证明其内容已纳入当前 release，不能沿用目录名称判断是否仍待应用 |
| `~/Documents/ab-directions-scratch-2026-10-11/` | 0.739 | A/B 原始材料与 scratch 备份仍在；总结文档不等于原始 traces 的备份 |
| `research-data/usc-email/` | 0.060 | 新增院校参考与申请材料；原始材料需保留，完整备用副本未验证 |
| `research-data/agentpile-cache/agent_reward_bench_probe/` | 1.003 | 本地开发 probe，恢复来源未确认；不能因上级名为 cache 就视作可下载 |
| QEM 三个主目录及 release-assets | 27.490 + 0.836 | 仍混有未版本控制的数据和产物；Git remote 及 SHA 文件分别不能证明所有数据有备份或存在第二份副本 |
| `~/Documents/Winref/` | 143.447 | Windows 迁移备份仍在；原机器或其他盘是否还保留完整副本未知 |

上述小型研究材料、A/B 材料和 probe 合计约 5.5 GB，是优先确认离机副本的现存范围，但不意味着其中每个文件都独有。agentpile-cache 其余约 33.8 GB 有按 revision 下载的清单依据，恢复仍依赖上游可用性和访问权限，本轮没有完整重下载验证。

旅行归档提供部分论文、图源、分支和 stash 的远端保护，明确不覆盖全部 research-data，也不自动覆盖归档后的新修改。本次在 internal-writing、NSF proposal、usc-email 和 research-compute 看到了活跃的未提交修改或新增文件。三个有内容的 Codex proposal worktree 未发现已跟踪文件修改，其 HEAD 没有相对于本地 remote refs 的独有提交；这不覆盖忽略文件，也不是完整远端恢复证明。

`tmutil destinationinfo` 仍报告未配置目的地，Data 卷未列出 APFS 快照。本轮未检查离线外置盘或集群全部副本，未做完整恢复演练。下次优先处理恢复来源清单，再按需评估缓存增长；未设置自动扫描或自动删除。

## 2026-10-12 历史测量基线

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
