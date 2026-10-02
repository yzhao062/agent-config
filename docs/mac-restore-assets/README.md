# Mac 恢复附件

记录日期：2026-10-01。主指南为 [Mac 设置与重装恢复指南](../mac-mouse-preferences.md)。此目录属于 agent-config 个人记录，不同步到 anywhere-agents。

这些文件是经过内容筛选的本机快照。没有密码、token、私钥、聊天正文或应用账户数据库，也没有完成空白 Mac 重装演练。不要把参考 JSON 直接覆盖到应用配置路径。

| 文件 | 用途和恢复目标 |
| --- | --- |
| `base-history.yml` | base 的 Conda 直接依赖参考；新 Miniforge 已经有 base，不要重复创建同名环境 |
| `py312-history.yml` | py312 的 Conda 直接依赖；在尚无该环境时用 mamba env create 创建 |
| `development-inventory.json` | base/py312 的包名、版本、构建标识、channel，以及 6 个 editable 包对应的源 repo；不含包源认证 URL |
| `py312-pip-observed.txt` | Conda 元数据中标为 pypi 的版本，排除 editable 包；需要时在 Conda 依赖之后安装，可能仍有平台或解析冲突 |
| `anywhere-agents.config.yaml` | 用户规则包选择，目标 `~/.config/anywhere-agents/config.yaml`；检查是否需与已有配置合并 |
| `agent-preferences.json` | Codex/Claude/Agy 的少量非密钥设置参考，按目标版本的实际配置结构合并 |
| `desktop-preferences.json` | 鼠标、窗口、字体、输入法、IDE、登录项等参考；含已标出的当前值与偏好差异 |
| `git-global-ignore.txt` | 两条全局 ignore 规则，目标 `~/.config/git/ignore`；已有文件则合并而非覆盖 |
| `cli-auto-update.py` | 原本机更新脚本的副本，目标 `~/.local/share/cli-auto-update/update.py` |
| `io.github.yzhao062.cli-auto-update.plist` | 自动更新的 LaunchAgent；安装路径与 Python 解释器先核对再加载 |
| `io.github.yzhao062.vibesignal.plist` | VibeSignal widget 的 LaunchAgent；也可由当前版本 `vibesignal install-autostart` 重建 |

## 快速恢复顺序

1. 安装开发工具、Miniforge、所需桌面应用，完成 GitHub 登录。
2. 恢复 repo 和其未提交工作；私有 `.env`、凭据、数据从独立加密备份取回。
3. 用 `py312-history.yml` 重建 Conda 环境，按项目的 requirements/lockfile 安装 Python 依赖；`py312-pip-observed.txt` 用于补齐旧环境或排查版本。新 base 中原有 9 个 pip 包的名字和版本在 JSON 中，按需要恢复。
4. 按 JSON 的 editable_packages 对应关系安装本地源包。不要把这些包换成 PyPI 同名版本。
5. pipx 显式使用 py312 安装 anywhere-agents、azure-cli、twine、`vibesignal[macos]`；安装 standalone CLI 并检查 PATH。
6. 恢复用户 packs，运行 consumer bootstrap，再合并个人 Agent 偏好、VibeSignal hooks 和 IDE 连接。
7. 应用内部恢复桌面偏好；检查鼠标 app overrides、权限、主题和字体。
8. 最后加载启动项，核对更新日志，按主指南验收并确认外部备份可恢复。

包清单记录观察到的状态，不代表推荐永久锁死所有版本。自动更新会使 CLI 版本继续变化。特别是 Python 3.14 的 base 与 Python 3.12 的项目环境不能混为一个解释器。

## 私有备份仍需另做

详细 repo 状态清单在 `~/.local/state/mac-recovery/2026-10-01/`，不在本目录。SSH/云/发布凭据、Overleaf/HPC 配置、Codex automation 定义和本地历史、浏览器/应用账户数据、项目未提交和忽略文件都需要独立备份。复制这份附件目录不能恢复这些内容。

手动归档应用数据前，先保存工作并正常退出相关应用；使用应用支持的同步、导出或系统迁移机制。重新登录和原设备授权可能仍是恢复步骤的一部分。恢复后确认成功，再处理旧备份。
