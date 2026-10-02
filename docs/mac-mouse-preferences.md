# Mac 设置与重装恢复指南

此文件是个人 Mac 配置的统一记录，保留原文件名，避免已有链接失效。只保存在 agent-config，不同步到 anywhere-agents。首次记录于 2026-09-23；2026-10-01 扩充并核对本机配置。后续修改机器设置时更新对应章节，注明日期、最终值和验证结果。

本文区分用户偏好、历史已验证结果和当前实测值。它记录恢复方法，不是整机备份。密码、API token、私钥和 OAuth 缓存不进入 Git。历史检查不代表今天的凭据仍有效，也不代表应用升级后所有菜单位置不变。

2026-10-01 又通过本地 `prun` 完成五组 Agy 审计：开发环境、桌面偏好、Agent/启动项、repo 本地工作、备份覆盖；两项结果经定向复核后整合。恢复附件的用途和顺序见 [附件说明](mac-restore-assets/README.md)。实测值来自运行中的系统，未在空白 Mac 上进行完整重装演练。

## 重装前必须保留的东西

2026-10-01 执行 `tmutil destinationinfo` 返回 `No destinations configured`，没有配置 Time Machine 目标。本文和下面的恢复附件已写入本地工作区；是否已推送必须以 Git 状态为准。重装前应把 Git 之外的重要数据备份到另一块加密磁盘或其他已验证的备份位置，不能只放在本机另一个目录。

| 内容 | 路径或范围 | 恢复原则 |
| --- | --- | --- |
| 开发项目与本地工作 | `~/PycharmProjects/` | GitHub 是已推送代码的来源；未提交、未推送、未跟踪、被忽略文件和本地分支仍要单独保留。不能只重新 clone 就认为完整恢复 |
| Windows 迁移参考 | `~/Documents/Winref/` | 用户计划保留约一个月，2026-10-01 仍存在。到期前核对独有的 `.env`、发布凭据、数据、稿件和项目配置；不要把整棵目录复制进 Git |
| 项目私有设置 | 各 repo 的 `.env*`、`agent-config.local.yaml`、`.claude/settings.local.json`、手写 `AGENTS.local.md` 和 IDE 配置 | 按项目恢复，先检查是否包含密钥；生成配置由 bootstrap 重建 |
| 发布与云凭据 | 见下文凭据表 | 单独加密备份，或重装后重新登录、签发；不写进本指南 |
| Agent 设置与本地历史 | `~/.codex/`、`~/.claude/`、`~/.gemini/`，以及 ChatGPT/Claude 的应用数据 | 如需保留本地聊天、任务、MCP 配置和草稿，应在退出相关应用后备份。配置与认证状态不能只靠重装 CLI 恢复 |
| IDE 和日常应用 | `~/Library/Application Support/JetBrains/`、Logi Options+ 配置、浏览器 profile、Shortcuts | 优先使用应用自身的设置导出或同步；完整本地副本属于私有备份，恢复后检查权限与登录 |
| Shell 和启动任务 | `~/.zshrc`、`~/.zprofile`、`~/.gitconfig`、`~/Library/LaunchAgents/`、`~/.local/share/cli-auto-update/` | 修改用户名或安装目录后要调整绝对路径；不要整批盲目加载旧启动项 |

`AutoFigure-Edit` 不在恢复清单中；`tokyo-relay` 已被用户指定为废弃项目，不要因为它出现在旧备份里就重新部署。

### 扩展审计发现的本地资料

本次扫描 `~/PycharmProjects/` 的 55 个顶层目录，发现 52 个 Git repo，其中 23 个在扫描时有未提交或未跟踪内容。另有两个非 Git 的会议 supplementary 目录，不能从 remote clone 恢复。发现一个当前分支比缓存 upstream 多 4 个提交、另一个 repo 有未被缓存 remote-tracking refs 覆盖的分支，以及一个 stash。没有 fetch，因此这些是相对于本机远端引用缓存的结果，不能据此断言 GitHub 当下缺少哪些提交。

详细 repo/remote/分支和文件元数据清单保存在 `~/.local/state/mac-recovery/2026-10-01/repos-inventory.md` 和 `repos-audit.json`，目录权限为 `0700`，文件为 `0600`。它们没有文件内容或凭据值，仍作为个人清单放在 Git 之外。重装前把该目录随私有备份一并保存。审计数值会随其他任务变化；Git 把部分目录合并成一条状态记录，不能把条目数当成穷尽的文件计数。

补充备份范围包括 `~/Documents/windows-archive-20260922/`（旧迁移的未推送稿件、图源等归档）和 `~/data/`。本次还找到 14 个项目 `.env` 文件及 Cloudflare Workers 使用的 `.dev.vars`，只核对位置和权限，不把内容收进恢复附件。被忽略目录没有全部递归展开，实际备份应覆盖完整工作目录并按需排除明确可重建的缓存。

Winref 的项目位于 `~/Documents/Winref/PycharmProjects/`。其中还有当前 Mac 工作目录没有的 repo、零提交本地 repo 和归档目录；不能把“已经 clone 常用 repo”理解为 Winref 可以全部丢弃。用户说保留约一个月，没有配置固定日期的自动删除任务。

本轮看到 FileVault 已开启，未配置 Time Machine 目标，也没有挂载外部备份卷。不能据此排除用户另有离线盘或远程备份。FreeFileSync 已安装，但本次找到的 macOS 默认配置没有有效源/目标配对，旧 Windows 同步预设使用 Windows 盘符，不能直接作为 Mac 的可用备份。FileVault 保护磁盘上的数据，不能替代备份；同步开启也不代表每个路径都已上传。先验证备份目标与可恢复性，再重装。

## 基础环境和恢复顺序

2026-10-01 本机实测为 Apple M5 Pro、18 个 CPU 核心、64 GiB 内存，macOS 27.0.1（26A434）。工作目录为 `~/PycharmProjects/`，登录 shell 为 zsh。这些是当前机器快照，不是下一台机器必须匹配的版本要求。

1. 先确认外部备份可读，保留未推送代码和私有文件，再执行重装。
2. 安装开发工具和 Miniforge，恢复 `py312` 环境，安装 PyCharm、GitHub CLI、Codex、Claude Code、Agy。当前 `brew` 不在 PATH 中，不应假设旧环境通过 Homebrew 管理。
3. 登录 GitHub，按 [ONBOARDING.md](../ONBOARDING.md) 恢复相邻的 agent-config、anywhere-agents、agent-style、agent-pack，再 clone 所需 consumer repo。旧本地副本用于找 remote 和补齐本地文件，不覆盖远端的新提交。
4. Consumer 安装 anywhere-agents 并按其 `AGENTS.md` 运行 bootstrap，恢复项目的 pack 选择与私有覆盖。四项源仓库判定成立的 repo 按其说明跳过自举，不能把 consumer bootstrap 套进源仓库。
5. 恢复或重新签发各平台凭据，逐项验证身份；接着恢复 Agent 个性化设置、IDE、鼠标和窗口管理。
6. 在 CLI 都安装好之后恢复自动更新和 VibeSignal 启动任务，检查日志；最后按文末验收表验证。

### Python、Shell 和工具位置

| 项目 | 2026-10-01 实测或已确认偏好 |
| --- | --- |
| Miniforge | `~/miniforge3/`；已有 `base` 和 `py312` 两个环境 |
| 首选 Python | `~/miniforge3/envs/py312/bin/python`；新建/安装环境优先使用 mamba |
| 用户 CLI 入口 | `~/.local/bin/`，在 `~/.zprofile` 和 `~/.zshrc` 中加入 PATH；`.zshrc` 已有 conda init 段 |
| pipx | `~/miniforge3/bin/pipx`；虚拟环境位于 `~/.local/pipx/venvs/` |
| pipx 管理的工具 | anywhere-agents、vibesignal、twine、azure-cli |
| Codex CLI | `~/.local/bin/codex` 指向 `~/.codex/packages/standalone/releases/` 下的安装版本 |
| Claude Code | `~/.local/bin/claude` 指向 `~/.local/share/claude/versions/` 下的原生安装版本 |
| Agy、gh | `~/.local/bin/agy`、`~/.local/bin/gh` |
| AWS CLI | `~/.local/bin/aws` 指向 `~/.local/share/aws-cli/aws` |
| Google Cloud CLI | `~/.local/share/google-cloud-sdk/`，gcloud/bq/gsutil 入口在 `~/.local/bin/` |
| LaTeX | 本机现在已有 `/Applications/TeX`，`pdflatex` 和 `latexmk` 均可从 `/Library/TeX/texbin/` 找到；此前“未装 LaTeX”的判断已过时。本轮没有编译测试 |

重装前用 `conda env export --from-history -n py312` 保存直接安装需求，并用 `conda env export -n py312` 保存完整环境快照，再另存 `pipx list`。这些导出可能含本机路径或私有依赖源，先检查再决定存放位置。不要把整套旧 Miniforge 二进制目录作为跨版本恢复的唯一方法。

### 已保存的环境清单与安装顺序

已实际导出并检查 [base 直接依赖](mac-restore-assets/base-history.yml)、[py312 直接依赖](mac-restore-assets/py312-history.yml)、[开发环境清单](mac-restore-assets/development-inventory.json) 和 [py312 中 pip 管理的版本](mac-restore-assets/py312-pip-observed.txt)。清单只含包名、版本、构建标识和已知 channel，不含私有包源 URL。Conda 提示混用 pip 的环境不能由它完整锁定，因此这些是观察快照，不是已经验证能一次安装成功的 lockfile。

| 额外依赖 | 2026-10-01 实测 | 恢复要点 |
| --- | --- | --- |
| Xcode Command Line Tools | `/Library/Developer/CommandLineTools` | 在编译依赖和使用系统 Git 前恢复；用 `xcode-select -p` 检查 |
| Python | base 为 3.14.7；py312 为 3.12.14 | 项目和 pipx 工具显式选择 py312，避免默认落到 base 的 3.14 |
| py312 的 Conda 直接依赖 | python=3.12、pip、ripgrep、git-delta、bat、fd-find、cairo、lightgbm、boto3、awscli、pandoc | 先按 history 文件创建环境，再恢复 pip 依赖和本地包 |
| Node.js / npm | `/usr/local/bin/`，Node v26.10.0、npm 11.19.1 | 当前使用 macOS pkg 安装方式；没有观察到 nvm/fnm 或额外全局 npm 包 |
| MacTeX | TeX Live 2026，`/usr/local/texlive/2026/`，latexmk 4.88 | PATH 注册在 `/etc/paths.d/TeX`；Ghostscript 在 `/usr/local/bin/gs`；不是 Homebrew 安装链 |
| Python GUI 工具 | VibeSignal 为 `vibesignal[macos]` | pipx 恢复时保留 macos extra 和 py312 解释器；只装基础包可能缺 GUI 依赖 |
| AWS CLI 两个安装来源 | 用户入口在 `~/.local/bin/aws`，py312 也有 Conda awscli | 恢复后用 `command -v aws` 和 `aws --version` 确认当前 shell 调用哪个版本 |

六个 editable 包需要先恢复源 repo，再运行对应的 `python -m pip install -e <repo>`；不要把它们作为同名 PyPI 发行包直接替代：

| 包名 | `~/PycharmProjects/` 下的目录 |
| --- | --- |
| catchbench | auditablebench |
| grade | grade |
| meta-finder | meta-finder |
| pyod | pyod |
| QEMScore | qem-bench |
| vibesignal | vibesignal |

py312 的 editable VibeSignal 和 pipx 的 widget 安装是两个环境，恢复时分别检查。pipx 中已核对的包为 anywhere-agents 0.9.0、azure-cli 2.90.0、twine 7.0.0、vibesignal 0.1.2；这些是当日版本，自动更新会继续推进。

在已经安装 Miniforge、尚未创建这些环境的机器上，以下命令可作为恢复起点；先读附件说明，按项目要求处理旧版本依赖冲突。此轮没有执行安装：

```bash
"$HOME/miniforge3/bin/mamba" env create -f "$HOME/PycharmProjects/agent-config/docs/mac-restore-assets/py312-history.yml"
"$HOME/miniforge3/bin/mamba" install -n base pipx
"$HOME/miniforge3/bin/pipx" install --python "$HOME/miniforge3/envs/py312/bin/python" anywhere-agents
"$HOME/miniforge3/bin/pipx" install --python "$HOME/miniforge3/envs/py312/bin/python" azure-cli
"$HOME/miniforge3/bin/pipx" install --python "$HOME/miniforge3/envs/py312/bin/python" twine
"$HOME/miniforge3/bin/pipx" install --python "$HOME/miniforge3/envs/py312/bin/python" "vibesignal[macos]"
```

Git 的全局忽略项已保存为 [git-global-ignore.txt](mac-restore-assets/git-global-ignore.txt)，恢复到 `~/.config/git/ignore`，内容是 `.DS_Store` 和 `**/.claude/settings.local.json`。另行恢复 Git 身份、GitHub 的 gh credential helper，以及 Overleaf 专属 helper；不要把原有 `.gitconfig` 中的本机绝对路径照搬给不同用户名。主要 GitHub remote 使用 HTTPS，SSH 登录失败本身不能证明 gh 或 HTTPS clone 不可用。

## Agent 配置和状态显示

ac 指 agent-config，aa 指 anywhere-agents。共享规则与个人本机设置可能有意不同，恢复时先看当时版本的 `AGENTS.md` 与本机覆盖，不自动用旧模型名覆盖新设置。

| 项目 | 配置位置 | 2026-10-01 本机值 |
| --- | --- | --- |
| Codex CLI 默认模型 | `~/.codex/config.toml` | `model = "gpt-6-astra"`，`model_reasoning_effort = "high"` |
| Codex 其他设置 | 同上 | `service_tier = "default"`、`approval_policy = "on-request"`、`project_doc_max_bytes = 262144`、`[features] fast_mode = false` |
| Claude Code effort | `~/.claude/settings.json` | `effortLevel = "xhigh"`，`env.CLAUDE_CODE_EFFORT_LEVEL = "xhigh"`；此文件没有显式 `model` |
| Claude 状态栏 | 同上 `statusLine` | command 为 `"$HOME/.claude/hooks/_python" "$HOME/.claude/statusline.py"`，恢复 bootstrap 提供的 hook 和状态栏脚本 |
| Agy 模型 | `~/.gemini/antigravity-cli/settings.json` | `Gemini 3.8 Flash (High)`；同文件还有 trustedWorkspaces |
| Agy MCP 和项目设置 | `~/.gemini/config/` | 有项目配置；本轮确认 `mcp_config.json` 是 0 字节，不能据此称为已配置 MCP；按敏感配置处理 |
| anywhere-agents 用户设置 | `~/.config/anywhere-agents/config.yaml` | 文件存在；恢复后检查共享配置与各项目覆盖 |

当前共享 `AGENTS.md` 声明的 Codex 默认是 `gpt-6.1-sol / xhigh / standard`，与上述本机快照不同。本轮仅记录差异，没有修改任何模型设置，也没有断言这是误配置。桌面聊天可以另选模型，CLI 默认不能证明每个桌面聊天的实际模型。恢复后分别核对 CLI、桌面任务、项目覆盖和 `/vet` 的实际运行配置。

VibeSignal 的 widget 由下文 LaunchAgent 启动，状态目录为 `~/.vibesignal/`。ChatGPT 的 pet 用户偏好为关闭；重新登录或重装后在应用中确认，本轮未重新检查 pet 的运行状态。

### Agent 恢复遗漏项

[agent-preferences.json](mac-restore-assets/agent-preferences.json) 保存经过字段筛选的参考值，不是可以整体覆盖安装的配置。额外实测值包括：Codex 的 `preventSleepWhileRunning=true`、`ambient-suggestions-enabled=false`、`followUpQueueMode=steer`；Claude 的自动压缩阈值环境项为 `70`、每 session web search 上限为 `1000`、review channel 为 `auto`。这些是当前个人设置，不把它们改成共享默认。

个人规则包选择已保存为 [anywhere-agents.config.yaml](mac-restore-assets/anywhere-agents.config.yaml)：agent-pack 的 profile、paper-workflow、acad-skills 指向 main，agent-style 指向 v0.4.1。恢复到 `~/.config/anywhere-agents/config.yaml` 后，再运行 consumer bootstrap。规则包 pin 与 py312 中安装的 agent-style Python 包版本属于不同层，不要求两个数字机械相等。

| 补充恢复范围 | 位置与处理 |
| --- | --- |
| Codex 全局规则 | `~/.codex/AGENTS.md`；属于用户级规则，不能只恢复 repo 的 AGENTS.md。全文保留在个人备份，恢复时与最新共享规则核对 |
| Codex 定时任务 | `~/.codex/automations/`；本轮发现 3 项，2 项 ACTIVE、1 项 PAUSED。定义可能关联原来的聊天或项目，在应用内确认目标仍存在后再启用；不能只复制目录就认定调度已恢复 |
| Codex 认证与本地状态 | `~/.codex/auth.json` 及本地数据库按私有数据备份，登录状态可能需重新建立；生成的运行时包可重新安装 |
| Codex helper | `~/.local/bin/codex-code-mode-host` 与 codex 同属 standalone bundle；两个入口经 `~/.codex/packages/standalone/current/` 指向当前版本 |
| Claude 用户状态与桌面设置 | `~/.claude.json`、`~/Library/Application Support/Claude/claude_desktop_config.json`；保留私有副本，可能含账号或连接信息，不公开整体配置 |
| Claude 同步技能 | `~/.claude/skills/synced/`；恢复后确认日常 docs/pdf/pptx 等技能实际可用，不把插件缓存当作唯一来源 |
| Agy 登录与工作区信任 | `~/.gemini/antigravity-cli/` 中的认证文件和 trustedWorkspaces；新机器重新登录，按所需目录设置信任范围 |
| PyCharm MCP | IDE 的 MCP Server 已启用，Claude 用户配置中有本机 PyCharm HTTP 连接；恢复后重新获取 IDE 提供的地址，避免照搬旧端口 |
| Codex 内置工具 | node_repl 指向 ChatGPT.app 内的运行时。marketplace/cache、computer-use notify 等路径可能随应用安装更新，交给桌面应用重新建立 |

这里仅记录定时任务的存放位置和状态数量，没有创建、变更或启用任何自动任务。私有备份应保留任务定义及所需本地历史；恢复后通过应用检查，而不是手写旧 thread ID 重新注册。

## 无人值守 CLI 更新和 VibeSignal 启动

2026-10-01 已保存当前本机脚本和两个自建 LaunchAgent 的原样副本，供恢复时使用：

| 恢复附件 | 安装位置 |
| --- | --- |
| [cli-auto-update.py](mac-restore-assets/cli-auto-update.py) | `~/.local/share/cli-auto-update/update.py` |
| [io.github.yzhao062.cli-auto-update.plist](mac-restore-assets/io.github.yzhao062.cli-auto-update.plist) | `~/Library/LaunchAgents/io.github.yzhao062.cli-auto-update.plist` |
| [io.github.yzhao062.vibesignal.plist](mac-restore-assets/io.github.yzhao062.vibesignal.plist) | `~/Library/LaunchAgents/io.github.yzhao062.vibesignal.plist` |

这些附件仅包含已检查的程序和启动配置，不含凭据。plist 使用 `/Users/yzhao062` 的绝对路径，换用户名必须先修改。更新任务由 `/usr/bin/python3` 执行，恢复前先验证该解释器存在且可运行脚本，或明确改为新机器上的有效 Python 路径。

更新任务设置为 `RunAtLoad = true`，每天本机时间 04:15 运行。登录后加载任务也会运行，因此恢复过程不依赖电脑恰好在 04:15 开机。电脑关闭或睡眠时不能依靠脚本持续运行；恢复后应以日志确认是否补跑。脚本有防重入锁和轮换日志，没有失败后立即重试的循环。

脚本依次更新 Codex、Claude Code、Agy、AWS CLI、Google Cloud CLI、anywhere-agents、VibeSignal、Twine、Azure CLI 和 gh。gh 下载后核对 release 提供的 SHA-256。日志为 `~/.local/share/cli-auto-update/update.log`，启动器输出为同目录的 `launcher.out.log` 和 `launcher.err.log`。2026-10-01 04:15 的运行记录以 `Update run completed` 结束。这是一次成功记录，不保证以后更新不会失败。桌面应用、macOS、LaTeX 和 Rectangle 不由此脚本统一更新。

VibeSignal 的参数为 `~/.local/pipx/venvs/vibesignal/bin/vibesignal widget`，`RunAtLoad = true`、`KeepAlive = false`；退出后不会由这个配置反复重启。日志为 `/tmp/io.github.yzhao062.vibesignal.log` 和 `.err`，临时目录日志不作为长期恢复资料。

先安装依赖、建立目标目录、复制上面的三个文件并修正路径，再通过 `plutil -lint` 检查 plist。仅在任务尚未加载时，用以下命令注册；注册自动更新任务会立即开始更新：

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/io.github.yzhao062.cli-auto-update.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/io.github.yzhao062.vibesignal.plist"
```

用 `launchctl print "gui/$(id -u)/io.github.yzhao062.cli-auto-update"` 检查注册状态，配合 update.log 判断实际结果。不要把 Google、Microsoft、Adobe 的旧更新器 plist 全部复制回去，由相应应用安装程序重新配置。

仅让 widget 开机启动还不够，Agent 要有事件 hooks 才能更新状态。当前 VibeSignal hooks 分别在 `~/.claude/settings.json` 与 `~/.codex/hooks.json`。恢复命令已通过本机 CLI help 核对；在 bootstrap 恢复共享 hooks 后执行，再确认共享 hooks 仍存在：

```bash
vibesignal install-hooks --agent claude
vibesignal install-hooks --agent codex
```

`vibesignal install-autostart` 可以重新生成当前用户的启动项并启动 widget，是手动复制旧 VibeSignal plist 的另一种方法，选其中一种即可。共享 `guard.py`、`session_bootstrap.py`、`_python`、`statusline.py` 和 `agent-quota.py` 已对照源 repo，由 bootstrap 恢复；不要仅保留旧机器生成的副本。`~/.claude/agent-quota.py` 可用于检查状态栏所用的跨 Agent 额度读数。

## 凭据和登录恢复

下表只记录位置。2026-10-01 已确认各路径存在，没有输出密钥，也没有在本轮调用云 API 或执行包发布来验证权限。

| 用途 | 需要保留或重建的位置 | 重装后验证 |
| --- | --- | --- |
| PyPI / Twine | `~/.pypirc`，以及项目通过 `.env` 提供的发布 token | 核对目标仓库与 token 权限；`twine check` 只检查分发包，不能验证登录，不要为测试凭据发布包 |
| npm | `~/.npmrc` | 检查 registry；在实际需要的 registry 上验证身份 |
| AWS | `~/.aws/config`、`~/.aws/credentials`，以及实际使用的 SSO 登录 | `aws sts get-caller-identity`，命名 profile 需逐个验证；不要把输出中的账户信息放进公开文档 |
| Azure | `~/.azure/` | 重装后 `az login`，用 `az account show` 核对订阅；旧 token 缓存不是永久登录保证 |
| GCP | `~/.config/gcloud/`，包括 `application_default_credentials.json` | gcloud CLI 登录和 ADC 都要考虑；`gcloud auth list`、当前 project，以及实际使用 ADC 的程序分别确认 |
| GitHub | `~/.config/gh/`、系统钥匙串、`~/.gitconfig` | `gh auth login` / `gh auth status`；核对 Git clone/pull 所用协议和 credential helper |
| SSH | `~/.ssh/` | 私钥、config、known_hosts 单独加密备份；新系统检查私钥权限并实际测试需要的远端 |
| OpenStack | `~/.config/openstack/clouds.yaml` | 文件存在；恢复前确认是否仍使用该云，不根据文件存在推断登录有效 |
| Overleaf Git | `~/.overleaf-credentials` | 全局 Git helper 指向此文件；从加密备份恢复或重新生成 Overleaf Git 凭据 |
| HPC | `~/.psc-bridges2.env`，以及 SSH config 中的远端别名 | 作为私有配置保存；新系统按需测试实际集群访问 |
| OpenStack rc 脚本 | `~/.config/openstack/app-cred-claude-monitor-openrc.sh` | 也在备份范围内，不能只保存 clouds.yaml |
| Cloudflare Workers | 项目中的 `.dev.vars` | 与 `.env` 同等对待；不能从普通 clone 恢复其值 |
| GCP 多账号状态 | `~/.config/gcloud/legacy_credentials/`、`credentials.db`、`access_tokens.db` | 不漏掉其他账户的 ADC/配置；优先重新登录，核对实际 project 与 ADC 消费者 |

Azure 和 GCP 是用户明确要求保留的迁移范围。历史登录完成不替代重装后的验证。系统钥匙串与设备绑定的认证信息可能需要重新登录；恢复文件不能保证所有应用自动认证。

完整 `.ssh/` 中发现 5 个私钥文件及多个主机别名，实际密钥和远端配置只存个人加密备份。旧迁移目录和云同步目录也存在名称像凭据的文件，应纳入到期前的私有文件核对；文件名或大小不能证明其中 token 仍有效。本轮没有移动或删除这些文件。重装验收应优先使用应用原生同步、迁移和登录机制，不强制导出明文密码 CSV，也不对运行中的应用数据库执行手工 SQL 修复。

## 终端外观、输入法和日常应用

PyCharm Terminal 字号偏好是 **14**。2026-10-01 已核对 `~/Library/Application Support/JetBrains/PyCharm2026.2/options/terminal-font.xml` 中 `FONT_SIZE=14`、`FONT_SIZE_2D=14.0`。恢复时在 PyCharm 设置中搜索 Terminal Font 调整，避免把旧版本整个 options 目录直接覆盖新版本。

macOS Terminal 历史偏好为白色背景。2026-10-01 实测 `com.apple.Terminal` 中 `Startup Window Settings = Clear Light`，但 `Default Window Settings = Clear Dark`，两者不同。本轮未改主题。恢复时若继续采用白底偏好，应在 Terminal 的 Profiles 中选择浅色主题并设为默认，同时检查启动窗口和新建窗口；不要把这个快照误写成“所有窗口已经统一白底”。自定义 profile 可通过 Terminal 导出 `.terminal` 文件，保存在个人备份中。

输入英文出现宽字距时，先检查输入法全角模式。此前 WeType 的 `Option + Shift + H` 切换后用户确认恢复正常；若新版本快捷键变化，以输入法设置为准。`Shift`、`Option`、`Control` 和 `Command` 是不同的修饰键。

日常应用恢复范围包括 PyCharm、ChatGPT、Claude、Chrome、Edge、Microsoft Office/Outlook、Logi Options+、Rectangle、Amphetamine、Zoom、WeChat、Lark、Termius 和所需 VPN。浏览器分别恢复各自的同步/登录；不要把 Google 登录当成 Chrome 与 Edge 的本地缓存已共享。

### 桌面偏好补充快照

[desktop-preferences.json](mac-restore-assets/desktop-preferences.json) 保存经筛选的参考值。它不是 macOS 可直接导入的配置，也不代表所有值都由本次会话设置。恢复后逐项验证，特别是权限、插件和跨版本界面行为。

| 范围 | 2026-10-01 实测值 | 恢复方式 |
| --- | --- | --- |
| PyCharm 编辑器 | 字号 15、行距 1.5，鼠标滚轮改字体已开启；Terminal 独立为 14 | 在 Editor Font 和 Terminal Font 分别恢复 |
| PyCharm 主题 | Islands Light，自动检测已开启 | 新版本按外观设置核对 |
| PyCharm 键位 | `macOS copy`，Optimize Imports 为 `Command + Option + O`，GotoSymbol 未绑定 | 保留 `keymaps/` 和 `options/mac/keymap.xml`；不要仅复制 VM options |
| PyCharm Settings Sync | 本地设置为启用 | 登录 JetBrains 后确认同步完成；本地标志不能证明远端副本最新 |
| PyCharm 插件 | 用户插件含 Claude Code、PDF viewer、PowerShell 等，另有 22 项 disabled plugin ID | 完整名单在 JSON；按新版本需求复核，不盲目关闭新增功能 |
| Terminal | Clear Light/Clear Dark 均为 SFMonoTerminal-Regular 12pt，120 列、30 行；Clear Dark 的 Option as Meta 开启、Bell 关闭 | 使用 Profiles 导出/导入，白底偏好与当前 profile 差异见上文 |
| 输入源 | U.S. 和 WeType Pinyin；Fn/Globe 切换输入源 | 快捷键为 `Control + Space` / `Control + Option + Space`；在系统设置恢复 |
| Trackpad | 轻点点击、三指拖移已开启；四指横滑切桌面、四指竖滑 Mission Control | 在触控板与辅助功能设置核对；鼠标 Thumb button 仍为 Launchpad |
| Dock / Finder | Dock 不自动隐藏、不显示最近应用；Finder 搜索默认当前文件夹，桌面显示外置磁盘/可移动介质，不显示内置硬盘 | 在各自设置恢复；不复制旧屏幕 UUID 或窗口坐标 |
| 登录项 | Rectangle、Amphetamine、Acrobat Collaboration Synchronizer | 前两项按个人需要开启，Adobe 项交给应用安装管理；登录项存在不代表某个防睡眠会话正在运行 |
| Shortcuts | 仍为原有 7 项，测试项 New Shortcut 3 不存在 | 核对应用同步或逐项导出 `.shortcut`；不把数据库文件当跨版本导入格式 |
| 字体 / TeX 用户树 | 未找到 `~/Library/Fonts`、`~/Library/texmf`、`~/texmf` | 本次未发现需要单独迁移的这些目录；项目自带字体、cls/sty 仍随项目保存 |

Logi Options+ 的配置库位于 `~/Library/Application Support/LogiOptionsPlus/settings.db`。它可能混有账户和设备信息，不能整个提交到 Git。先使用应用提供的备份功能或按下表手动重建，再验证设备专属设置。WeType 词库位于 `~/Library/Application Support/WeType/`，Termius 的主机与登录配置也属于私有备份范围；应用安装完成不代表这些内容已恢复。

Zoom 的取景问题增加了一条可核对线索：Logi Options+ 内保存的 Brio 手动裁剪 preset 为 `fov=90`、`zoom=120`，手动图像 preset 为 brightness 153、contrast 89、saturation 130、sharpness 137，另有 HDR/exposure 配置，原始值见 JSON。这里只确认保存的 preset，未验证 Zoom 当前选择哪台摄像头、哪套 preset 生效，也未重新观察画面。重装后应在实际 Zoom 预览里调整并确认，不把这组值认定为此前问题已经解决的证据。

## 鼠标与 Desktop

设备：Logitech MX Master 3S。配置工具：Logi Options+。记录于 2026-09-23。

| 按键 | 配置范围 | 动作 |
| --- | --- | --- |
| 滚轮后方的 Top button | All Apps（全局） | Keyboard shortcut：`⌘W` |
| 滚轮后方的 Top button | Google Chrome 专属配置 | `Close tab` |
| 左侧拇指滚轮（Thumb wheel） | All Apps，以及 Google Chrome、Microsoft Excel、Microsoft PowerPoint、Microsoft Word、Safari 的专属配置 | `Switch between desktops` |
| 拇指下方的 Thumb button（原 Gestures 按键） | All Apps，以及 Google Chrome、Microsoft Excel、Microsoft PowerPoint、Microsoft Word、Safari 的专属配置 | `Launchpad`，打开应用列表与搜索 |

应用专属配置会覆盖 All Apps。Chrome 的 Top button 因此要单独设为 `Close tab`；其他应用若没有专属覆盖，则使用全局 `⌘W`，其具体效果由应用决定。拇指滚轮也要在现有的应用专属配置中逐一设置，才能在这些应用里切换 Desktop。这个设置替代了 Chrome 和 Safari 的滚轮切换标签页、Excel 的横向滚动，以及 Word 和 PowerPoint 的滚轮缩放。若某个应用里的按键行为不同，先检查该应用的专属配置。

在新 Mac 上恢复时，在 Logi Options+ 中选择 MX Master 3S，先设置 All Apps，再逐一检查上表列出的应用专属配置。Top button 是滚轮后方的小按钮，不是按下滚轮的 Middle button。Thumb button 设置为 `Launchpad` 后，原来的按住并移动鼠标进行窗口导航的 Gestures 不再由此按键触发。

2026-10-01 读到的应用覆盖补充：Safari、Excel、Word、PowerPoint 的 Top button 当前为 `MODE_SHIFT`，会覆盖全局 `⌘W`；Chrome 为 Close tab。Office 的 Back/Forward 分别为 Undo `⌘Z` 和 Redo `⇧⌘Z`。这些是当前配置观察，不能把它们解释为用户后来主动改变了偏好；恢复时若目标仍是各 app 关闭当前页，需要单独检查该按钮。Thumb button 和 Thumb wheel 在上述应用里仍分别为 Launchpad 和切换 Desktop。本轮没有修改映射。

不使用触控板时，拨动左侧拇指滚轮切换 Desktop。要把窗口移到相邻 Desktop，按住标题栏拖到屏幕左侧或右侧边缘，等桌面切换后松开；要移到指定 Desktop，按 `Control + ↑` 打开 Mission Control，再把窗口拖到屏幕顶部的目标 Desktop。

## 窗口分屏

使用 Rectangle 1.100（106）的默认快捷键。日常只需要左右半屏，以及左、中、右三列；不额外定制四分屏。`⌃` 是 Control，`⌥` 是 Option，`⇧` 是 Shift，三个键不同。

| 动作 | 快捷键 |
| --- | --- |
| 左半屏 | `Control + Option + ←` |
| 右半屏 | `Control + Option + →` |
| 左侧三分之一 | `Control + Option + D` |
| 中间三分之一 | `Control + Option + F` |
| 右侧三分之一 | `Control + Option + G` |
| 最大化当前窗口 | `Control + Option + Return` |
| 恢复窗口原来的大小和位置 | `Control + Option + Delete（⌫）` |

快捷键作用于当前窗口。三分屏时，依次选中三个窗口，分别按 `Control + Option + D / F / G`。2026-09-23 用户实测确认左侧三分之一生效，其余快捷键已核对配置，未逐项人工实测。

Rectangle 保留辅助功能权限、开机启动和自动检查更新。自动检查更新不代表已经启用无人值守安装更新。Rectangle 的 `Snap windows by dragging` 关闭，保留 macOS 自带的拖动贴边分屏。新机器从 [Rectangle 官网](https://rectangleapp.com/) 安装，选择 Rectangle 默认快捷键，并恢复这些选项。

原始偏好还有 `subsequentExecutionMode=1`、`reflowTodo` 的 `Control + Option + N` 和 `toggleTodo` 的 `Control + Option + B`；这些不属于用户明确要求新增的常用快捷键，本轮仅记录，不增加日常操作要求。需要完整的私有导出时可使用 `defaults export com.knollsoft.Rectangle <文件路径>`，导入前退出 Rectangle、检查版本和原有配置。不要批量导入所有系统 defaults 或重置系统快捷键来恢复几个窗口功能。

## 分屏配置的临时改动清理

2026-09-23 核对本次分屏设置过程中的试验项：

| 试验项 | 最终状态 |
| --- | --- |
| All Applications 中试加的 `Window->Move & Resize->Left`、`Right` 和 `Left` 菜单快捷键 | 已删除；全局 `NSUserKeyEquivalents` 为空 |
| 临时开启的 Keyboard navigation | 已关闭；`AppleKeyboardUIMode = 0` |
| Shortcuts 中测试用的 `New Shortcut 3` | 已删除；原有 7 个快捷指令保留 |
| Rectangle 录入过程中误记的 `A` 快捷键 | 已通过恢复 Rectangle 默认快捷键清除 |
| macOS 原生窗口管理快捷键 | 保留原生设置；没有执行系统快捷键整体重置 |

本次核对范围是分屏配置过程中已知的临时改动。没有配置前的完整系统快照，不能据此断言所有系统偏好都与配置前完全一致。鼠标映射、终端外观等此前明确要求的个人设置继续保留。此文档属于 agent-config 的个人偏好，不同步到 anywhere-agents。

### 系统性复核（2026-09-23）

对照本次分屏配置的工具操作记录，再读系统偏好、应用界面及启动项。原生四个半屏快捷键仍为 `Control + Fn + 方向键`，全部启用，与操作前界面记录一致。全局及已扫描的应用偏好中没有残留菜单快捷键；ByHost 中未发现额外修饰键映射，`hidutil` 的 `UserKeyMapping` 均为空。Keyboard navigation 仍关闭，Shortcuts 保留原有 7 项。

Shortcuts 再次复核时的保留列表为 `New Shortcut 2`、`Open App`、`New Shortcut`、`New Shortcut 1`、`Take a Break`、`Text Last Image`、`Shazam shortcut`。其中 `New Shortcut`、`New Shortcut 1` 和 `New Shortcut 2` 均属于原有内容；本次创建并删除的测试项是 `New Shortcut 3`。

Rectangle 的左右半屏及 `D / F / G` 三列快捷键已再次在界面核对，拖动贴边功能关闭。`Remove keyboard shortcut restrictions` 保持开启：[官方首次启动代码](https://github.com/rxhanson/Rectangle/blob/main/Rectangle/AppDelegate.swift)会自动开启此项，因此不将它认定为录键测试残留。

检查用户及系统 LaunchAgents、LaunchDaemons 和相关已加载任务，没有发现本次试验新增的分屏脚本或额外窗口管理服务。用户没有 crontab。既有的 CLI 自动更新和 VibeSignal 启动项继续保留。

发现 Rectangle 安装镜像仍挂载，已推出 `/Volumes/Rectangle1.100`，并确认没有剩余挂载镜像。下载的 `Rectangle1.100.dmg` 保留为普通安装文件，不会在后台执行。本轮未发现需要继续撤销的已知试验配置；没有重置来源不明的其他系统偏好。

## PyCharm 内存

64 GB 内存的 Mac 上，PyCharm 最大 JVM 堆内存设置为 12 GB（`-Xmx12288m`），初始堆保持 `-Xms256m`。用户配置文件为 `~/Library/Application Support/JetBrains/PyCharm2026.2/pycharm.vmoptions`，其余选项与安装默认值一致。2026-09-23 已按用户授权重启，并通过运行中 JVM 的 `MaxHeapSize=12884901888` 验证生效；新版本优先通过 `Help > Change Memory Settings` 设置为 `12288 MiB`。

调整原因：原来的 2 GB 上限在索引 trading-doc 的 EDGAR 原始数据时发生 `OutOfMemoryError: Java heap space`。当时该数据目录包含 5,036 个文件，约 11.6 GB。建议将不需要代码索引的原始数据目录标为 Excluded，此项尚未修改。重启前应先处理 IDE 终端内正在运行的 Claude/Codex 任务。

2026-10-01 再读该文件，仍为 `-Xms256m`、`-Xmx12288m`。12 GB 是 JVM 堆上限，IDE 的实际进程内存还包括其他分配；IDE 内启动的 Python、Claude、Codex 和浏览器也有独立进程。不要因为机器有 64 GB 就把所有进程的内存额度都调大。新项目默认解释器使用 `~/miniforge3/envs/py312/bin/python`，个别项目确有专用环境时保留它的设置。

## 性能排查和未实施的建议

2026-10-01 的高 CPU 已追溯到 internal-writing 中由 PyCharm 终端内 Claude 启动的 `regen.py` 和 `mlpseeds.py`。前者当时占用约 10 至 16 个核心，属于数据重建计算；后者在做多随机种子的 MLP 比较。用户确认让其继续运行。没有因此修改进程优先级、线程数、电源配置或 PyCharm 堆上限，也没有杀进程。PID 和瞬时占用不属于需要恢复的配置。

以后遇到卡顿，先看当前 CPU、内存压力和 swap，再定位具体进程及项目。浏览器和桌面应用的多个 renderer 不能直接当作相同数量的遗留标签页；RSS 求和可能重复计算共享内存。此前没有设置自动清理 Codex 闲置浏览器的任务，也没有建立定时重启机制。CPU 满载时降低后台计算优先级只是建议，未实施。

## 重装后的验收

| 检查 | 通过条件 |
| --- | --- |
| 代码和本地资料 | 所需 repo 的 remote 正确；未推送工作、`.env`、数据和私有配置已逐项找回；不重新部署废弃 repo |
| Python / IDE | py312 可运行；PyCharm 指向正确解释器，Terminal 字号 14，最大堆 12288 MiB；重要项目可以打开 |
| CLI | gh、codex、claude、agy、anywhere-agents、aws、az、gcloud、twine 能运行并显示版本 |
| 模型和 effort | CLI 默认、桌面任务、项目覆盖、共享规则和 review dispatch 分别核对，差异有记录 |
| Consumer bootstrap | 在普通 consumer 执行成功；共享规则、所需 packs、hooks 和状态栏存在；源仓库按其规则处理 |
| 登录和发布准备 | GitHub、AWS、Azure、GCP/ADC 逐项验证；PyPI/npm 凭据通过其管理页面或非发布方式检查 |
| 自动更新 | 两个自建 LaunchAgent 路径有效；更新日志有新的完成记录；VibeSignal widget 能显示 |
| 鼠标和窗口 | Top button 关闭当前页；Thumb button 打开应用列表；拇指滚轮切 Desktop；Chrome 等应用专属设置没有覆盖错 |
| 分屏和终端 | Rectangle 左右半屏、D/F/G 三列生效；Terminal 默认与启动 profile 符合选定的浅色偏好 |
| 系统授权 | Rectangle、Logi Options+ 和需要操作界面的应用重新取得所需辅助功能等权限；不要直接覆盖旧权限数据库 |
| LaTeX | pdflatex/latexmk 在 PATH 中，实际项目可以编译；仅发现可执行文件不算编译成功 |
| 备份 | 外部备份可读，并确认后续备份方式；Windows 参考目录到期前已处理独有资料 |

## 后续维护规则

个人配置变更继续更新本文件，至少记录最终值、配置路径、恢复方法、验证日期，以及试验项是否撤销。需要本地脚本才能恢复的功能，同时更新 `mac-restore-assets/` 中经过检查的无密钥附件。不要把“提出过的建议”写成“已经执行”，也不要把文件存在写成认证有效。提交和推送仍遵守仓库的明确授权规则。
