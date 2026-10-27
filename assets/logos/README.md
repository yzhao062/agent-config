# 六个开源项目的 Logo 设计方案

日期：2026-10-22。状态：用户已选择 B，完成一轮矢量精修并推送至六个仓库的 main，已核对远程提交。

发布提交：agent-risk `b47ecc5`，agent-defs `1d7bdff`，agent-style `52f3f72`，anywhere-agents `ebf6517`，catchbench `c6df914`，auditable `eba386a`。本仓库的概念记录与构造脚本保留在本地，尚未提交。

CI 后续修复：agent-style 的 README 多余空行触发 MD012，已移除并修正本地接入脚本。agent-risk、agent-defs、agent-style、auditable 的 Python 3.9 Linux 任务在 Ubuntu 26.04 上找不到解释器，已仅将这些组合固定到 Ubuntu 24.04，保留原测试覆盖。修复提交依次为 `a1ab24a`、`8054083`、`7da99e0`、`8dd93c7`。2026-10-23 06:37 UTC 已核对六个仓库 main 最新提交，所有相关 CI 均通过，包括 anywhere-agents 的 Validate 和 Docs strict build；自动跟进已删除。

## B 精修版

[六个并排效果](refined-b/family.png) 和 [HTML 展示](refined-b/family.html) 使用真实 SVG。anywhere-agents 简化为双接口，auditable 保留五节点 A 的连接结构，换成菱形节点并去掉底框。所有字标采用 Inter SemiBold 600，字体版本 4.001（git-66647c0bb），按 SIL OFL 1.1 附许可证；发布字标已转路径，字体与可编辑构造源仍保留。

母版为 200 × 200，主体约在 24 至 176 的范围；主要笔画为 18 至 22 单位，auditable 连线为 16 单位以平衡节点重量。转角为直线切角，共享深色 #0F172A 和强调色 #4C9B91；深底使用白色和 #70C4B8。透明图标不加底框，favicon 单独采用深色切角底框。各项目资产在 `refined-b/<project>/`，构造与导出脚本为 `build_family.py`。

已检查浅底、深底、16/24/32/64 px 对照、字标导出及 42 个发布 SVG 的 XML 结构。SVG 不含嵌入位图、脚本或字体依赖。16 px 主要靠轮廓辨认，细节展示建议至少 24 px。CatchBench 的仓库入口要求运行 PRE board，已成功复现。六个仓库均新增 `docs/assets/brand/` 并接入 README；anywhere-agents 的中文 README 和两个 MkDocs 站点的导航图标、favicon 同步接入。原 auditable SVG 保留。

## 概念板

[A：圆角连接](concepts/board-a.png) 与 [B：切角开口](concepts/board-b.png) 均包含六个项目、缩小对照、Inter 与 Manrope 真实字体样张，以及 auditable 原件与无底框衍生研究。可编辑排版分别见 [A HTML](concepts/board-a.html) 和 [B HTML](concepts/board-b.html)，由 `concepts/build_boards.py` 生成。字体文件与许可证保存在 `concepts/fonts/`。

A 已调整 agent-risk 和 anywhere-agents 的轮廓，减少两者都像分叉图形的问题。用户选择 B，认为切角方向更有设计感，并要求对 auditable 做统一风格适配。两张早期概念板中的 auditable 均使用未经修改的原 SVG，作为保留的对照记录。

五个新标识目前是生成式位图概念，字标为真实字体排版，尚未重建为可编辑 SVG。缩小对照用于概念比较，不代表已通过 16 px favicon 验收。原始生成图和 A 的首版保留在 `concepts/`。

## 范围与目标

本轮覆盖 yzhao062 账号下的 agent-risk、agent-defs、agent-style、anywhere-agents、CatchBench 和 auditable。agentpile 据用户说明已在另一个 repo 完成 logo，不纳入。目标是为 GitHub README、文档导航和项目图标建立一个可认出的家族身份，六个成员仍容易区分。本文件决定后续设计方法，不把文字构想当作视觉成果，也不修改六个远程仓库。

## 推荐方向

用户确认优先关注成套感与品牌统一。推荐设计为同一家族的六个成员：统一字标字体、几何语言、端点与转角处理、视觉重量、图标与字标间距及展示规格，项目含义通过各自的轮廓表达。auditable 与 CatchBench 分别承担方法库和检测基准角色，可在同一家族内进一步呼应。先建立一套共同母版，再将它应用于全部六个标识；不得逐个设计完再靠换色拼成套装。代价是减少各项目风格自由度，收益是网站、文档和 README 并排展示时能被识别为同一作者的工具系列。以下符号和颜色仍待出图验证。

| 项目 | 首选探索方向 | 需要避免的误读 |
|---|---|---|
| agent-risk | 一条历史轨迹分出一个变化分支，简洁的分叉轮廓 | Git 分支/fork 图标、实时拦截或风险消除保证 |
| agent-defs | 一段文本穿过开口扫描框，保留一个匹配标记 | 沙箱隔离或阻断所有攻击的承诺 |
| agent-style | 有特征的编辑字形，优先比较定制字母与笔尖 | 段落格式标记或只做 Markdown 格式检查 |
| anywhere-agents | 同一配置适配不同接口；比较适配器和折叠配置页 | 多 agent 工作流运行时 |
| CatchBench | 比较三个位置表示检测时点的构形与 C 形构形，保持与 auditable 的家族关联 | 分数持续上涨的柱状图，或保证拦住失败 |
| auditable | 以现有五节点 A 为保留基线，先探索配套字标和背景适配 | 自动改名为 Auditable AI、默认推倒重做 |

配色由家族母版统一管理：共同深色字标与中性色（深色默认取 auditable 底色 #0F172A），少量共享强调色；不为六个项目预先各配一套无关颜色。两板均比较同色并排与有限强调色并排。anywhere-agents 现有酒红色、CatchBench 薄荷绿与暖橙为来源参考；若保留，须纳入共同明度和饱和度规则。浅色填充在小尺寸版本改用足够清楚的深色轮廓或实色，实际渲染后决定。

## 参考及边界

本地 editable-figure 图库 14（MemoHarness）提供协调色彩、清楚组织和打磨程度的参考；04（CatchBench）只提供已确认喜欢的配色。已查看两张参考图。论文图的技术密度、公式和 3D 不作为 logo 的要求，也不把论文审美视为已经确认的 logo 偏好。

auditable 的现有 SVG 已读取并渲染查看：白色五节点 A，深色圆角方底。原文件保留不改。它不是其他五个项目必须复制的模板。其品牌名称、节点结构和深底基线也不因通用配色建议被覆盖。
来源：https://raw.githubusercontent.com/yzhao062/auditable/main/docs/assets/auditable-mark.svg

功能依据为六个项目当前官方 README：
https://github.com/yzhao062/agent-risk
https://github.com/yzhao062/agent-defs
https://github.com/yzhao062/agent-style
https://github.com/yzhao062/anywhere-agents
https://github.com/yzhao062/catchbench
https://github.com/yzhao062/auditable

## 后续制作

1. 先做两张实际生成的家族概念板，每张包含六个标识，并固定项目顺序与名称。A 板探索 auditable 五节点 A 所启发的连接与端点语言；B 板探索统一切角和开口的图形语言。每张板只采用一种共同几何语法。auditable 两板均保留原始 A 基线，额外适配版必须并排标明，不能默认替换。原 A 不合某板语法时，该板加放一个从原 SVG 编辑的标明适配版，家族陈列是否采用它随概念选择一起确认。生成器只绘制五个新标识，auditable 的槽位在排版时直接放原 SVG 的渲染图，不让生成器重画。传递参考映射与色值，不把论文参考图作为直接重绘对象。排版阶段同步用两到三款真实字体制作六个名称的样张，让两套方向连同真实字标一起比较。对比的是实际图片，不能以两份提示词代替。
2. 先选家族方向，再在该方向内逐项目优化。可借用另一板的符号构想，但必须按选定语法重绘，不能直接混搭成品。展示一项推荐及理由，保留候选图。只对真实存在的设计分歧追加生成。
3. 重建前在本文件记录选定方向的画布、安全区、名义笔画比例、端点、转角和底框规则。笔画比例以 auditable 的 24/512 为初始参照，按并排视觉重量校正并记录偏差。对选中的五个新标识重建可编辑 SVG；auditable 的适配版直接从原 SVG 编辑，原始生成图另存；不能把 PNG 放进 SVG 容器冒充矢量。先确认选中形状能适应小尺寸，再制作整套导出。
4. 每个项目交付 icon、横向字标组合、浅色背景版、深色背景版、单色版及 PNG 预览。auditable 保留原始深底 icon，另外测试保留五节点位置与边关系的无底框单色适配版，明确标为衍生版。字标固定为 agent-risk、agent-defs、agent-style、anywhere-agents、CatchBench、auditable；长标题与介绍文字留在 README。衍生 SVG 的 title 与 aria-label 对应这些名称，原 auditable 文件原样保留。先用两到三款真实开源字体排出六个名称，在浅色和深色背景的 240 px 宽样张中选定全系列一款字体，记录名称、版本和许可证。生成图里的字只作排版参考。字标保留可编辑文本源，发布版文字转路径并保留字体许可证。主格式是 SVG；本任务没有 PPTX 要求。
5. 资产保存在 /Users/yzhao062/PycharmProjects/agent-config/assets/logos/<project>/，候选放 assets/logos/concepts/，最终选择与规范写入 assets/logos/README.md。发布到各项目另行处理。

## 验收

检查 16、24、32、64 px 图标及 240 px 宽横向字标；若细节在 16 px 消失，制作保持身份的小尺寸简化版。检查 GitHub 浅色和深色背景、纯黑与纯白版本；圆形裁切只作为将来头像使用的附加检查，并将六个无文字图标并排比较。同一张并排对照板同时判断家族一致性与项目区别：是否共享字体、端点、转角、视觉重量和配色逻辑，是否仍保留六种可区分轮廓。颜色不能是唯一辨识线索。出图前不预设通用笔画宽度或固定填充率，按实际渲染做光学校正。32 px 灰度无字对照条用于项目对应检查，需由实际观看确认能区分；同时放入 Git 分支/fork 图标检查 agent-risk 的近似风险。现有 auditable 在小尺寸的节点细节和深色画布上的底框分离需要实测，必要时提供标明改动的小尺寸与深底适配候选，原 512 px 母版不变。

图标不嵌项目名和口号；完整名称交给字标。避免无依据的防护保证和性能暗示。检查 SVG 无外部图片、脚本与未解析字体依赖，PNG 与最终 SVG 一致。参考只用于分析，不能照搬其他项目标识。

## 评审与未定项

已完成两路 Agy prun 设计研究及两轮 /vet both（Claude Code + Antigravity）方案评审。第二轮 Antigravity 通过，Claude 在补齐重建前构造规范后条件通过；相关修正已落实并核对，未再发起第三轮。实际概念图生成后再审轮廓、可读性和差异度；本轮文字评审不能证明视觉质量。两位评审均已核查用户补充的成套感与品牌统一重点。未定项是共同母版和每个项目最终符号及共享配色，以及全系列共用的一款真实字体，须由出图比较解决，不需要提前填写审美问卷。
