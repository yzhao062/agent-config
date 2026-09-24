# Mac 鼠标与窗口管理偏好

设备：Logitech MX Master 3S。配置工具：Logi Options+。记录于 2026-09-23。

| 按键 | 配置范围 | 动作 |
| --- | --- | --- |
| 滚轮后方的 Top button | All Apps（全局） | Keyboard shortcut：`⌘W` |
| 滚轮后方的 Top button | Google Chrome 专属配置 | `Close tab` |
| 左侧拇指滚轮（Thumb wheel） | All Apps，以及 Google Chrome、Microsoft Excel、Microsoft PowerPoint、Microsoft Word、Safari 的专属配置 | `Switch between desktops` |
| 拇指下方的 Thumb button（原 Gestures 按键） | All Apps，以及 Google Chrome、Microsoft Excel、Microsoft PowerPoint、Microsoft Word、Safari 的专属配置 | `Launchpad`，打开应用列表与搜索 |

应用专属配置会覆盖 All Apps。Chrome 的 Top button 因此要单独设为 `Close tab`；其他应用若没有专属覆盖，则使用全局 `⌘W`，其具体效果由应用决定。拇指滚轮也要在现有的应用专属配置中逐一设置，才能在这些应用里切换 Desktop。这个设置替代了 Chrome 和 Safari 的滚轮切换标签页、Excel 的横向滚动，以及 Word 和 PowerPoint 的滚轮缩放。若某个应用里的按键行为不同，先检查该应用的专属配置。

在新 Mac 上恢复时，在 Logi Options+ 中选择 MX Master 3S，先设置 All Apps，再逐一检查上表列出的应用专属配置。Top button 是滚轮后方的小按钮，不是按下滚轮的 Middle button。Thumb button 设置为 `Launchpad` 后，原来的按住并移动鼠标进行窗口导航的 Gestures 不再由此按键触发。

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
