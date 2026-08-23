# Grok 作为第四个 reviewer 的评估

**日期**:2026-08-22
**工作流**:`implement-review` 的 reviewer backend 选型
**状态**:调查完成,结论为暂不接入;保留三条可执行路径
**读者**:本仓库维护者,以及未来任何重新提出"再加一家审查厂商"的会话

---

## 1. 这份文档回答什么

维护者提出三个递进的问题:

1. `implement-review` 搭配 Grok 会不会更快?
2. 如果每月 300 美元不是约束,对整个工作流的增益是多少?
3. 按实际用量,应该选哪个套餐;网上流传的那些优惠是真的吗?

调查分两轮完成。第一轮六个单元回答"值不值得接",第二轮两个 prun 单元加一个二十一个 agent 的 Workflow 回答"选哪档、怎么省钱"。两轮都采用跨厂商双面板:Codex 侧单元与 Claude 侧 agent 独立回答同一批问题,不互相通气,让分歧自己浮出来。分歧确实出现了,而且有几条推翻了单面板的结论,记录在第 9 节。

一句话结论:**不建议为这个工作流购买 Grok 订阅。如果要试,先用最小成本验证一件事实,再决定是否付费,并且永远不要把它接成能阻塞审查流程的第四个后端。**

---

## 2. 调查基数:维护者的真实负载

下表四项是本机命令产出的实测值。**本节其余数字(单轮 token 消耗、440 轮、以及第 12 节的工时)是估算或情景,不是实测**,各自在出现处标注。

| 指标 | 实测值 |
|---|---|
| `agent-config` 近 30 天提交 | 34 |
| `agent-config` 近 7 天提交 | 17(在加速) |
| 平均每次提交改动行数 | 587.15(最近 40 次;见下方口径) |
| 本机全部仓库近 30 天提交 | 1,347(53 个仓库,见口径) |

**基准与复现口径。** 基准 commit 为 `agent-config` 的 `132c0bde2cf61c45d7220224b7a6a79392dbf259`。**仅钉 commit 不够**:`--since='30 days ago'` 相对执行时刻计算,同一个 commit 在不同日期重跑会得到不同窗口。因此下表统一使用**固定 ISO 截止日 `2026-07-23T00:00:00`**(即 2026-08-22 回溯 30 天)。

| 数字 | 命令 | 值 |
|---|---|---|
| 30 天 / 7 天提交数 | `git rev-list --count --since=2026-07-23T00:00:00 HEAD` 及 `--since=2026-08-15T00:00:00` | 34 / 17 |
| 最近 40 次提交的平均改动行数 | `git log -40 --shortstat`,总改动 23,486 行除以 40 | **587.15** |
| 30 天窗口的平均改动行数 | `git log --since=2026-07-23T00:00:00 --numstat`(34 次提交,23,080 行) | 678.82 |
| 全部本地仓库 30 天提交数 | 见下方仓库集定义 | **1,347** |

**仓库集定义**(缺了它这个数不可复现):遍历 `~/PycharmProjects` 的**直接子目录**(不递归,递归会把 fetch 下来的嵌套仓库算进去),取其中含 `.git` 的目录,对每个跑 `git -C <repo> rev-list --count --since=2026-07-23T00:00:00 HEAD`,忽略失败者并求和。快照结果:**55 个含 `.git`,53 个成功,2 个无有效 HEAD,合计 1,347**。

两个均值的 population 不同,都不算错。**初稿写的 643 是错的**:当时的除数取了 insertion/deletion 词元数的一半(73/2 = 36.5),那不是提交数;40 次提交全部有 stat 行,正确除数是 40。本文后续沿用 587.15。

全仓库数在本次调查中出现过 1,329、1,326、1,347 三个值。前两个是滑动窗口在会话不同时刻测得的;1,347 用的是固定截止日。

**但固定截止日也不能让这个数字冻结,本文一度声称它可复现,那是错的。** Round 4 审查按同一程序复跑得到 **1,348**,因为期间某个被统计的仓库有了新提交。钉住 `agent-config` 的 commit 只冻结了 `agent-config`,冻结不了另外 52 个仓库的 HEAD。要真正冻结需要一份 53 个仓库名加 OID 的清单,而把本地项目名写进公开仓库不值得。

因此:**1,347 是一个带日期的快照,不是可复现值**,后续成本计算把它当作一个明确标注的情景使用。这四个数字的漂移本身就是这类测量不可复现的实例。

**440 轮是情景假设,不是实测负载。** 维护者的既定规则是每次提交都过一遍 `implement-review`,按字面理解应为每月 1,347 轮。440 来自"三次提交合并成一轮"的假设,该假设未经测量,且与前一句的政策陈述冲突,除非审查流程确实批量合并。后文把 **440 与 1,347 当作两个并列情景**分别计价,不把任一方当作已知负载。

单轮审查的 token 消耗按 Codex 侧单元估算:中位 83,000(4 万未缓存输入、4 万缓存读取输入、3 千输出),低估 42,000,高估 166,000。**三者均为 UNVERIFIED 情景**:原始单元报告位于会话临时目录,本文没有保留可复核样本,因此不得当作实测值使用。

初稿曾把 50,103 / 7,210 / 41,000 / 1,893 这组数字归因于 xAI 的 headless 文档。Round 3 审查抓取该页确认**页面不含这些值**,该归因已删除。

按每月 440 轮的**情景**换算(见上,440 不是实测负载):

| 情形 | 每轮 | 每周 | 每月 |
|---|---:|---:|---:|
| 低 | 42,000 | 4.25M | 18.48M |
| 中 | 83,000 | 8.40M | 36.52M |
| 高 | 166,000 | 16.81M | 73.04M |

---

## 3. 产品事实:两个同名产品,先分清

这是整份调查里最容易出错的一点,第一轮的一个单元就在这里跨了一步,第二轮才被证伪。

**网页版 in-chat builder** [S19],原名 Build Mode,2026-07-28 上线时仅限 SuperGrok Heavy,2026-08-19 对所有档位开放,含免费档。它运行在 Grok 聊天应用内,产出 grok.me 分享链接。它不是 repo-aware 的终端 agent,填不了审查者的位置。

**终端 CLI**,即 Grok Build CLI,2026-05-14 发布时仅限 Heavy,2026-05-25 开放给 SuperGrok 与 X Premium Plus 订阅者 [S7]。这才是能接进 `implement-review` 的产品。

**关于免费试用,当前一手证据。** 截至 2026-08-22,`x.ai/build` 是 CLI 安装页,其免费试用文案因此覆盖 Build CLI;Grok 4.6 公告也把 CLI 安装命令放在免费试用标题下 [S1]。较早的 2026-05 CLI 公告只列 SuperGrok 与 X Premium Plus [S7],说明权益曾经不同,或当前文案仍不完整。同时 `docs.x.ai/grok/faq` 把免费档的范围限定在 Chat 与 Voice,并把 Build 归入"周限到顶后暂停"的付费功能 [S9]。三处第一方材料互相冲突。

可以成立的结论只有一条:**厂商当前声明 CLI 可免费试用,但账号资格、额度、地区、期限和重置规则均为 UNVERIFIED**,不能把免费试用当作持续保证,也不能反过来断言免费仅覆盖 in-chat builder。第 11.2 节第一步是对这一条的实测。

**厂商主体也变了。** SpaceX 于 2026-02-02 以全股票方式收购 xAI(SpaceX 估值 1 万亿美元,xAI 2500 亿,合计 1.25 万亿),2026-07-06 更名为 SpaceXAI。Grok、SuperGrok、API 保留原品牌。这一条与第 7 节的合规讨论相关。

---

## 4. 档位与价格

档位阶梯已由第一方页面确认 [S8]。`x.ai/pricing` 直接渲染 SuperGrok Plus 的 100 美元月费卡片,比较表列出七列:Free、SuperGrok Lite、SuperGrok、SuperGrok Plus、SuperGrok Heavy、Business、Enterprise。

| 档位 | 月费 | 年费 | 证据强度 |
|---|---:|---:|---|
| Free | 0 | 不适用 | 第一方定价页 |
| SuperGrok Lite | 10 | 100 | StoreKit SKU,定价页未标价 |
| SuperGrok | 30 | 300 | 第一方定价页 |
| SuperGrok Plus | 100 | 1,000 | 第一方定价页 |
| SuperGrok Heavy | 300 | 未公开 | StoreKit SKU,定价页未标价 |
| X Premium | 8 | 未查 | X 帮助中心 [S21] |
| X Premium Plus | 40 | 395 | X 帮助中心 [S21] |

年费与月费恰好是 10 比 1,折合十个月的钱买十二个月,省 16.7%。需要注意的是,"年付"这个解读来自 10 比 1 的比例推断,而非任何页面上的计费周期标签,验证 agent 因此把置信度从高降到中。印度商店的 ₹9,900 与 ₹99,900 配对提供了独立佐证。Heavy 的年费确实存在(FAQ 承认),但没有任何可达页面公布数字;按 10 倍推算是 3,000 美元,这是推断而非来源。

**SuperGrok Plus 是真实且普遍可用的档位,不是灰度测试。** 验证 agent 拉取了七个区域商店,它在每一个区都是完整价格本地化的 SKU:英国 100 英镑、加拿大 129 加元、澳大利亚 150 澳元、德国 100 欧元、日本 15,000 日元、印度 9,900 卢比。灰度测试不会同时具备七区完整本地化和厂商自有定价页上的可购买卡片。此前会话只知道 30 与 300 两档,遗漏了这一层。

各档位的差别是定性描述而非数字。定价页对 Plus 的措辞是 Chat、Imagine、Voice、Build 上"显著更高"的用量,加 1080p 视频、更快响应、高峰期优先、抢先体验。开源 CLI 源码把 Heavy 描述为用量上限最高的档位。**xAI 不公布任何档位的计算单元数或百分比倍数** [S9],因此任何"Plus 是 SuperGrok 的 N 倍"的说法都缺乏来源。

---

## 5. 计量与配额:决定可行性的部分

### 5.1 两个独立计量表

Claude 面板澄清了一条结构性事实,并推翻了单面板此前的表述。xAI 运行两个独立计量表,走哪个由**客户端如何认证**决定,而不是由使用哪个产品决定。

**表一,订阅周池** [S9]**。** 位置在 `grok.com` 的 Settings 与 Usage,以百分比计,每周重置,按产品拆分为 API、Build、Chat、Imagine、Voice 五项。其中的 API 一项指的是通过 xAI 账号登录的第三方客户端产生的流量(文档举的例子是 Warp)。浏览器认证的 Grok Build CLI 落在这里。表内溢出靠 Extra Usage Credits,仅网页购买,最低 5 美元,购买后一年过期,按"标准费率"计价,单次动作成本高于套餐内含用量的实际费率。

**表二,开发者 API** [S11]**。** 位置在 `console.x.ai`,按每百万 token 的美元计价,由预付额度或月结账单支付,按 API key 分别统计,速率上限档位由累计消费决定。带 API key 运行的 Grok Build CLI 落在这里,**不消耗周池**。

两个表的溢出路径不同,不可混谈:Extra Usage Credits 补的是表一,console 预付额度或月结补的是表二。

### 5.2 凭证优先级,以及一个可用的设计

三个独立单元都确认了同一条优先级链 [S10][S17]:`model.api_key` → `model.env_key` → 活跃 session token → 裸 `XAI_API_KEY`。

由此得到一个此前没想到的做法。裸环境变量 `XAI_API_KEY` 输给有效 session,所以它不能用来把生产 loop 定向到表二。但 `~/.grok/config.toml` 里**给某个 model 条目单独配置 `api_key` 或 `env_key`,优先级高于 session**。于是:

> 给审查用的 model 条目配一个专用 API key,把无人值守的 loop 定向到表二;交互式使用继续走订阅 session。

这样生产 loop 拿到的是已公布的单价、可设的硬上限、可预算的月度支出,同时保留订阅用于日常交互。第 7 节会说明这个做法还附带一项合规上的好处。

### 5.3 周池到顶之后

默认路径,即 Auto Top Up 关闭且 Extra Usage Credits 余额为零时,付费功能暂停到下一次周重置 [S9]。Build 不在免费档兜底范围内(兜底只覆盖 Chat 与 Voice),因此 dispatch 拿不到任何审查结果。这是一次干净的停止。

开启 Auto Top Up 或持有额度余额时,行为相反。FAQ 的原话是"撞到周限不是硬停止":额度可以"立即继续用量",Auto Top Up 会"在余额偏低时自动补充"。**loop 不会在 100% 停下,它会跨进按量付费继续运行并持续计费,而且没有人在旁边。** 唯一的上限是 Auto Top Up 的月度封顶。

按每天 15 轮、每轮 5 万到 15 万输入 token 的规模,这是一个真实的无人值守支出敞口。**在启动任何自动化 loop 之前,确认 Auto Top Up 关闭且额度余额为零。**

两个面板在 HTTP 状态码上有分歧。Codex 侧读取了开源 CLI 的 `billing.rs`,得到 402 Payment Required [S15] 与提示语 "You hit your weekly limit";Claude 侧给出 429,但自行标注为低置信度,因为 changelog 页面当时被挡。本文采信 402,因为它有源码级证据。这条分歧不影响操作:两边都同意默认路径以非零码退出,wrapper 照样必须捕获 exit code 与 stderr。

### 5.4 实测容量

以下是社区实测 [S13],不是厂商承诺,且服务端权重可以随时调整。逐条来源见第 15 节。

| 档位与日期 | 实测消耗 |
|---|---|
| SuperGrok 30 美元,8 月 15 日 | 约 260 万含缓存 token 每 1%,推算周池约 2.6 亿 raw token,缓存命中 94% 到 95% |
| SuperGrok 30 美元,同帖另一人 | 每周 1.7 亿到 1.8 亿 |
| SuperGrok 30 美元,7 月 25 日 | 最低推理档做 HTML 与文本,一天消耗 40% |
| SuperGrok,6 月 | 试用 Build 第一天即触及周限 |
| Heavy,8 月 17 日 | 六小时不间断 grok-4.6 xhigh 编码消耗 10% |
| Heavy,7 月 25 日 | 二十个乃至一百个 agent 的集群"很难花掉最后 50%" |
| Heavy,7 月 | 已确认的 bug:设置显示 15% 但 Build 返回周限错误 |

最强的 30 美元档实测(1.7 亿到 2.6 亿 raw token 每周)是本工作流中位负载(每周 840 万)的 **20 到 31 倍**。即便按高估的每周 1,681 万算,也只占池子的 6% 到 10%。

这支持把 30 美元作为起始档位,但**不构成服务等级承诺**。同一批社区记录里同时存在一天耗尽、百分比消耗速率突变、以及虚假耗尽状态的报告。

---

## 6. 能力证据:没有支持更换审查者的依据

### 6.1 代码审查的直接对比不存在

没有任何公开评测比较过 grok-4.6 或 grok-build-0.1 与 GPT-5.6 Sol、Claude Opus 5 在代码审查精度、召回、严重度校准或独有确认缺陷上的表现。SWE-bench、DeepSWE、Terminal-Bench 一类测的是补丁生成与任务完成,是编码能力的合理代理,但不是审查与找错的证据。

独立榜单上的位置(全部来自 [S28]):

| 评测 | Grok 4.6 | GPT-5.6 Sol | Claude Opus 5 |
|---|---:|---:|---:|
| AA Intelligence Index | 61 | 61 | 63 |
| GPQA Diamond | 94.9% | 94.1% | 93.2% |
| Humanity's Last Exam | 42.9% | 49.5% | 54.9% |
| AA 长上下文推理 | 75.0 | 77.7 | 75.7 |
| SciCode | 53.6 | 56.1 | 55.7 |
| Terminal-Bench 2.1 | 88.4 | 89.5 | 89.1 |

唯一干净的领先是 GPQA Diamond 上不到两个百分点,而那是研究生水平的科学选择题,与代码审查无关。Humanity's Last Exam 给出最清晰的反向结果,Grok 落后 Opus 5 达 12 个百分点。

### 6.2 两条值得单独记住的证据

**上下文更大不等于审查更好** [S6]**。** SWE-PRBench 包含 350 个带人工标注审查问题的 pull request。八个受测模型在仅给 diff 的条件下只找到人类标注问题的 15% 到 31%,而且**提供更多上下文通常让结果变差而非变好**。这直接否定了"500K 上下文窗口意味着更强 reviewer"的推断。

**重复聚合有实证支持,但它并未证明跨厂商更差。** SWR-Bench [S25] 在 1000 个人工核验的 pull request 上评估审查评论,聚合多次独立审查确实提升 F1。这里必须区分两种「最强」:**绝对 F1 最高**的是 Gemini 2.5 Pro 自聚合 n=5,F1 为 23.84%;**相对增益最大**的是 Gemini 2.5 Flash 自聚合 n=10,F1 21.91%(增幅 43.67%),召回 30.44%(增幅 118.83%)。论文点名 **n=5 是实用甜点**,超过之后收益递减而成本线性增长。

该论文**同时**评估了跨模型聚合,结论是聚合小模型的多次运行可以低成本地匹敌或超过大模型的单次运行。那是一条成本论证,并没有确立自聚合优于跨厂商聚合。还要注意绝对分数整体很低,峰值 F1 只有 23.84%,与 SWE-PRBench 的 15% 到 31% 同量级。

PoLL 研究 [S26] 支持异质评审团在判分任务上减少同族偏好,但未测软件缺陷发现。另一项覆盖 26.5 万样本的研究 [S27]发现模型间一致性只是弱到中等的正确性信号,前沿模型会一致且自信地出错。

结论是:证据支持的是"多跑几次并聚合",而非"换一家厂商"。而多跑几次可以在既有的 Codex 独立配额里完成,不需要新后端。

### 6.3 速度

维护者的原始动机是"速度非常快、质量还凑合"。这个画像属于 grok-build-0.1 那条便宜快模型线,而 Grok Build CLI 当前默认运行的是 grok-4.6。

| 模型 | 输出速度 | 首 token |
|---|---:|---:|
| grok-build-0.1(OpenRouter 中位) | 约 127 tok/s | 约 0.42s |
| grok-4.6 | 约 71 tok/s | 48.4s |
| GPT-5.6 Sol | 约 70 tok/s | 97.2s |
| Claude Opus 5 | 约 56 tok/s | 40.7s |

**上表是 2026-08 的一次快照,且这些是会持续变动的服务端测量值,按 UNVERIFIED 引用。** Round 4 复核时 AA 页面已给出不同的首 token 值(Grok 39.72s、Opus 32.30s),与表中数字不符,这说明该表只能用于判断量级而非精确比较。

就量级而言:用 grok-4.6 替换 gpt-5.6-sol,输出速度基本相当;首 token 的差距即便按表中较大的口径算,放进一轮 20 分钟的审查也只是个位数百分比。端到端的 CLI 任务延迟没有任何受控对比。

要拿到真正的速度提升就得用 grok-build-0.1,也就是把质量较弱的那个模型放到 gatekeeper 位置。这与 `skills/implement-review/SKILL.md:104` 的单向棘轮规则直接冲突:`xhigh` 是地板,dispatching agent 只能向上调,理由是 agent 为自己的产出选择审查深度会形成自评循环。

对现有 Codex dispatcher,`SKILL.md:104` 的 effort 下限是无条件的 `xhigh`,**本文不提出任何低于该下限的实验**。初稿曾提出过一个三次 `high` 的方案并给出错误论证,记录见 11.3。若以后要比较 Grok 系模型,必须另行定义并验证该后端自己的质量门槛,不能把 Codex 的 effort 标签直接映射到另一家后端。

---

## 7. 数据治理与合规

这一节独立于性能,并且对学术侧的工作构成硬性约束。

### 7.1 2026 年 7 月的仓库外泄事故

安全研究者 Cereblab 于 2026-07-12 发布线级分析,7 月 14 日登上 Hacker News 首页。经 The Register、The Hacker News、TheNextWeb 等多家独立报道 [S12]:

- Grok Build CLI 把**整个 tracked 仓库**打包上传至 Google Cloud Storage,包含完整 git 历史与已提交的 secret、API key。
- 上传数据量约为编码任务实际所需的 **27,800 倍**。
- xAI 当时的营销表述是 session 期间不会有任何 codebase 内容传输到 xAI 服务器,线级数据与之矛盾。
- **自助的 `/privacy` 开关无效。** 真正止住上传的是一个未文档化的全局标志 `disable_codebase_upload: true`。研究者的表述是 `/privacy` 是按 session 的留存开关,不是修复此问题的那个开关。
- 受影响的是**个人 SuperGrok 与 X Premium Plus 订阅者**;持有零数据留存合同的企业客户与 API key 用法不受影响。
- 7 月 16 日 Grok Build 开源,据后续报道外泄相关代码仍留在开源版本中 [S29]。
- Musk 承诺删除此前上传的全部用户数据,但没有独立第三方确认删除已执行。

一条推论值得记下,它连接两个已核实的事实而非来自任何单一来源:该问题是通过交互式测试发现的,而在无人值守的后台子进程中,同样的行为**更不容易被人察觉**。

### 7.2 平台侧的沙箱缺口

Grok 的操作系统级沙箱**仅对 Unix 编译** [S3]:Linux 使用 Landlock,macOS 使用 Seatbelt。非 Unix 分支直接返回并报告沙箱不可用,不施加任何边界。网络隔离是 Linux 独有。

维护者在 Windows 11 上工作。这意味着 `--sandbox strict` 一类的 profile 不生效,唯一的约束只剩权限层 [S16](`--permission-mode dontAsk` 加窄 `--allow` 规则加 `--tools` 白名单),那是应用层的自我约束而非操作系统边界。无法可靠阻止子进程联网,也无法强制单仓库文件系统边界。

这与 7.1 同向:那次事故正是应用层开关未能管住数据外传,而在 Windows 上连操作系统这层兜底也没有。

**这里必须说清楚一点,以免夸大对比。** 缺少 OS 边界是真实的,但它**不是 Grok 相对本工作流现有 Codex 后端的差异项**:`SKILL.md:92-94` 里 Codex Auto-terminal 在 Windows 上是刻意用 `--sandbox danger-full-access` 启动的,同样没有 OS 边界。真正让 Grok 这一条更重要的,是它自己的数据外传历史 [S12] 与 USC 的数据分级约束 [S4],不是"Codex 有隔离而 Grok 没有"。

若要用 **Grok 自带的沙箱**,必须**在 WSL 内运行 Linux 版二进制**。通过 WSL 互操作调用 `grok.exe` 是无效的:那样跑的仍是 Windows 二进制,无沙箱行为原样保留。若不依赖 Grok 自带沙箱,外套一层独立沙箱是另一条同样可行的路径。

### 7.3 机构与资助方规则

USC 于 2026-01-09 生效的 Generative AI General Policy [S4] 规定,个人 AI 工具**只能接收公开数据**;Internal Use Only、Confidential、Restricted 均不允许。政策把"个人 AI 工具"定义为非经 USC 采购与管理的工具。按该定义,未发表的提案正文、未投稿的手稿、预算说明、学生相关材料至少属于 Internal Use Only。自费购买的 SuperGrok 属于个人工具,与档位无关。

USC 已提供 ChatGPT Edu,其协议排除将提示与输出用于训练 [S23]。USC 的企业 AI 目录列出 ChatGPT Edu、Zoom AI Companion、Microsoft Copilot、Gemini、NotebookLM,**没有 Grok**。

顺带一条与 Grok 无关但更实在的发现:**USC ITS 向符合条件的在职教职工提供 Codex**。维护者目前自费订阅 ChatGPT 与 Codex,值得向 ITS 询问。

NSF 禁止评审人将提案内容或评审记录上传至未经批准的生成式 AI 工具 [S5],并视之为保密违规。会议规则各异 [S24]:ICML 2026 只允许受限且符合隐私要求的辅助,禁止用 LLM 总结或评判投稿;NeurIPS 2026 在其授权实验之外基本全面禁止;ICLR 2026 允许写作辅助但要求责任与披露。

### 7.4 消费者档与 API 档的留存差异

API 档的表述 [S14] 是:请求与响应加密存储 30 天用于审计,xAI 不在此数据上训练,30 天后自动删除,未经明确许可绝不训练。

同一页面对消费者档的表述明显更弱:聊天与 build session"为产品功能而保留",在开关启用时"可能用于产品与模型改进"。多个二手来源报告消费者档训练默认开启,需手动关闭,且退出仅对未来生效。消费者条款还写明无法保证安全性。

**这构成 5.2 节那个设计的第二个理由,但它不构成 USC 合规例外。** 把生产 loop 通过 per-model API key 定向到表二,可以拿到"不训练、30 天自动删除、静态加密"的厂商承诺 [S14],计价也可预算。

**但个人 `console.x.ai` 账户仍然是 USC 定义的 Individual AI Tool** [S4]:该政策的判据是"是否由 USC 采购并管理",不是厂商的留存条款有多好。更强的留存承诺不改变数据分级。所以未发表手稿、提案、内部代码与学生数据**仍然不得输入**,除非 USC 完成采购并把该服务批准为 Enterprise AI Tool,或由相关办公室书面批准例外。

这条限制与 7.3 节一致,不要把 5.2 的设计读成绕过它的通道。API key 路线改善的是成本可预测性与厂商侧留存,适用范围仍限于公开数据。

### 7.5 所有权

SpaceX 于 2026-02-02 收购 xAI,2026-07-06 更名 SpaceXAI [S30]。未发表的联邦提案文本若送入该平台,接收方是一家大型联邦承包商的子公司。这是利益冲突层面需要维护者自行判断的事实陈述,不含政治判断。

---

## 8. 成本模型

现行短上下文 API 价格 [S11]:grok-4.6 每百万 token 为 2 美元未缓存输入、0.50 美元缓存输入、6 美元输出;grok-build-0.1 为 1 美元、0.20 美元、2 美元。**提示达到 20 万 token 时,该次请求的全部 token 按双倍长上下文费率计。** 这意味着限制 reviewer 读取的仓库范围有直接的价格意义。

按每月 440 轮、计入缓存的模型:

| 情形 | grok-4.6 | grok-build-0.1 |
|---|---:|---:|
| 低 | 27.28 | 12.32 |
| 中 | 51.92 | 23.76 |
| 高 | 103.84 | 47.52 |

若全部输入按未缓存计费,grok-4.6 对应 40.48、78.32、156.64 美元。

若范围扩大到全部 1,347 次提交而非 440 轮,倍数是 **3.0614**,中位为 grok-4.6 的 **158.95 美元**与 grok-build-0.1 的 **72.74 美元**。不计缓存的模型给出 1,347 轮在代表性规模下 **239.77 美元**(1,347 × 0.178,与本节其他处使用的同一单价)。长上下文阈值上是 **1,239.24 美元**,该值对应的工作量假设是每轮 20 万未缓存输入加 1 万输出、全部按双倍费率计:1,347 ×(200,000 × $4/M + 10,000 × $12/M)。

**仅在 `agent-config` 上运行 advisory 第二意见(每月 34 轮),代表性规模下:计入缓存模型 4.01 美元(34 × 0.118),全部输入按未缓存计费 6.05 美元(34 × 0.178)。** 本节其余论证采用计入缓存的模型,因为社区实测缓存命中率是 94% 到 95% [S13],所以 4.01 是更贴近现实的那个数。

对照订阅:30 美元低于 grok-4.6 的中位 API 等价,接近 grok-build-0.1 的中位等价;100 美元约等于 grok-4.6 计入缓存的高估情形,但买到的是不公开的池子而非已知的审查容量;300 美元远高于每一个建模场景。

这些是价格换算,不能证明不公开的订阅池能承载相应数量的长编码审查。两者是不同的问题。

---

## 9. 面板间分歧与裁决

跨厂商双面板的价值在这一节体现。以下每一条都是单面板给出过、被另一面板推翻或修正的。

| 议题 | 一方结论 | 另一方结论 | 裁决 |
|---|---|---|---|
| 免费额度 | Codex 侧:`x.ai/build` 写着免费试用,可零成本起步 | Claude 侧:两个产品同名,免费的是 in-chat builder 不是 CLI | **两侧都不完全成立,原裁决已撤回。** Round 1 审查抓取当前页面后确认 `x.ai/build` 就是 CLI 安装页,免费试用文案覆盖 CLI [S1];但资格、额度与持续性仍为 UNVERIFIED。见第 3 节修订 |
| 周池耗尽后的行为 | 早期表述:会静默掉到 API 计费 | Codex 侧读 `billing.rs`:402 且非零退出;session 优先于裸环境变量 | **采信 Codex 侧**,源码级证据。早期表述混淆了 session 过期与配额耗尽两种失败模式 |
| HTTP 状态码 | Codex 侧:402 | Claude 侧:429(自标低置信度) | **采信 Codex 侧**。不影响操作 |
| 计量表结构 | 早期表述:API 与订阅共用一个池 | Claude 侧:两个独立计量表,由认证方式决定 | **采信 Claude 侧**,并由此得到 5.2 节的设计 |
| X Premium Plus 权益 | Codex 侧:含 SuperGrok 等价权限 | Claude 侧:X 帮助中心只说"更高的 Grok 限额","含 SuperGrok 权限"的措辞保留给 Business 与 Organization | **部分采信**。两边都同意 Premium Plus 确实给 CLI 权限;是否"等价"存疑;配额等同性两边均未验证 |
| stream-death 检测 | 早期预测:比 Codex 后端更差 | 技术契约单元:钉住 commit 的源码里有 `end` 与 `error` 终止事件 | **保持 UNVERIFIED** [S2][S31]。官方 docs 页只确认 `streaming-json` 是逐行 JSON,未公布终止事件 schema 或退出码映射。须在固定 CLI 版本上采集正常结束、认证失败、配额失败与中断四类样本后,再设计严格谓词 |
| 官方页面不可达 | 多个单元:x.ai 返回 403,只能退而求其次 | Claude 侧验证 agent:403 是 User-Agent 过滤,加浏览器 UA 全部返回 200;`grok.com/pricing` 是 404,真实路径是 `grok.com/plans` | **推翻**。前几轮若干"文档未提及"的标记是抓取器产物而非真实信息缺口 |

最后一条有方法论意义:后续任何针对 x.ai 的调查都应先设置浏览器 User-Agent,否则会系统性地低估可获得的第一方证据。

---

## 10. 优惠与条款边界

### 10.1 已核实的正当路径

**年付省 16.7%**,即十个月的价格买十二个月 [S8]。计费周期标签未在任何页面出现,该解读来自 10 比 1 的 SKU 比例。

**没有学生或教职折扣** [S8]**。** 两个面板独立确认同一件事:xAI 构建了教育折扣然后关闭了它。实时客户端配置中 `disable_edu_discount: true`,EDU 促销 ID 就在该禁用标志旁边。x.ai 没有教育页面,定价页没有学生行,FAQ 中 "student" 出现零次。Google Play 上那个美国 .edu 两个月免费的活动页面自己写明即将过期,已不生效。2024 年那笔每月 25 美元的 API 额度是公开测试期的活动,已明确结束。

**机构路径存在但不是折扣。** 正当做法是请 USC ITS 与采购评估 Business 或 Enterprise 协议,SpaceXAI 提供组织批量定价与自定义速率上限。USC 政策要求各部门在获取个人 AI 工具前咨询指定的安全、伦理与法务办公室并走采购流程。把个人订阅包装成机构许可不属于此列。

### 10.2 网上流传的两条,都已过期

**Heavy 每月 99 美元的促销不是当前公开报价。** 从美国网络拉取的 grok.com 实时配置返回 `temp_supergrok_heavy_discount_enabled: false`,美区 App Store 仍列 300 美元。该促销**确实存在过**:TestingCatalog 于 2026-05-18 报道 xAI 为推广 Grok Build 将 Heavy 降价 67%。它是定向或限时的,期限来源冲突(加密资讯站称六个月,Medium 与 X 称三个月),没有 xAI 官方公告。只有在自己登录后的结账页面显示了促销价、期限与续费价,才算数。

**免费 Cursor Ultra 权益已于 2026-08-21 取消** [S20],即维护者提问的前一天。该路径在七天内走完了三种状态:一个月期,然后 Heavy 有效期间无限期,然后取消。Cursor 员工在 2026-08-15 还给出相反说法,改动是静默的,没有公告与截止日期,提出质疑的论坛帖被合并并锁定。已领取者看起来被保留,但依据只有一条论坛发言,背后没有条款页面,应视为可撤销。

相关的两条:Grok Bot 只有 SuperGrok Plus 与 Heavy 有资格,30 美元标准档没有;Grok Bot 的用量**计在 Cursor 账户上,不消耗 xAI 周池**。此外,一个账户只有一台持久云计算机,该账户下所有 Bot 共用,而非每个 Bot 一台。

### 10.3 Cursor 作为接触 Grok 的替代路径

> **审查状态说明**:本小节于 2026-08-22 四轮审查**结束之后**追加,未经过 `implement-review` 轮次。其证据强度低于本文其余部分。

维护者在评估 SuperGrok 之后追问 Cursor Individual Ultra。结论是 Ultra 不适合,但这条线索意外给出了本次调查中**接触 Grok 最便宜的正规路径**。

**抓取限制先说明。** `cursor.com/pricing` 对自动抓取器把三个付费档都渲染成 "$20/mo base",那是模板产物。因此下表的价格与额度**来自二手来源,不是第一方页面直读** [S32],按 UNVERIFIED 引用。

| 档 | 月费(美元) | 「其他模型」额度池(美元) |
|---|---:|---:|
| Hobby | 0 | 无 |
| Pro | 20 | 20 |
| Pro+ | 60 | 70 |
| Ultra | 200 | 400 |

三档**功能相同,唯一差别是池子大小**,Ultra 的杠杆是 2 倍。计量机制分两个池:Auto 模式由 Cursor 挑省钱模型,无限且**不消耗**池子;手动指定前沿模型或开 Max Mode 才扣池子,按各模型 API 原价计。池子耗尽后退回无限 Auto,或按 API 原价续费且无加价 [S33]。

**Ultra 对本维护者不适用**,两个理由:

1. $400 池子买的是 Claude、GPT、Gemini 的**计量**访问,而 Claude Max 与 ChatGPT/Codex 订阅已经提供前两家的**不计量**访问。真正新增的只有 Gemini 与 Grok。
2. Cursor 是 VS Code 分支,其价值主要在编辑器加 agent 的交互;维护者使用 PyCharm。不换编辑器则只买到一个额度池和一个 CLI。

**但 Cursor Pro 是本次调查中接触 Grok 最便宜的正规路径。** Cursor 每一档都标注 "generous limits for Grok",Grok Bot 访问在 Pro+ 与 Ultra [S32]。对比 SuperGrok Heavy 的 300 美元与 Cursor Ultra 的 200 美元,若目的只是试用 Grok 审代码,**20 美元的 Pro 即可**。注意 Cursor Ultra 与 SuperGrok Heavy 的联动权益已于 2026-08-21 取消 [S20],且 Grok Bot 用量计在 Cursor 账户而非 xAI 周池,两边同时购买没有叠加效应。

**两个警告。** Cursor 论坛有用户报告在 400 美元承诺值中的 250 美元处即触及速率限制 [S34];这是单一未验证报告,但与 xAI 周池同属「广告值不等于实得值」的问题。其次,Cursor 的 `agent` CLI 确有 print 模式(`--output-format text`,官方定位为脚本与 CI 用途),但**认证方式、订阅是否覆盖 CLI 用量、退出码约定官方文档均未记载** [S35]。这与第 12 节列出的 Grok 后端契约缺口完全同类,接第五家的成本量级相同。

数据治理不变:个人 Cursor 订阅同样是 USC 定义的 Individual AI Tool,7.3 节的约束原样适用 [S4]。

### 10.4 条款边界

xAI 消费者条款 [S18] 要求提供准确完整的信息,禁止共享账户凭证,允许因违约终止,并写明被终止用户不获退款。可接受使用政策禁止虚假账户、实质性不实陈述、转售、绕过保护措施与规避限制。

| 做法 | 定性 | 具体风险 |
|---|---|---|
| 按真实账单国家的公布价格购买,选择年付 | 正当。这是在公开报价内做选择 | 仅有常规订阅与续费风险 |
| 以虚假居住地或账单信息做区域套利 | **违反条款**。冲突于准确注册与账单要求。普通使用 VPN 不是问题,虚构资格才是 | 账户终止、已付时长因不退款条款作废、支付撤销或暂停;对学术人员另有机构诚信与采购合规暴露 |
| 通过新建或虚假身份反复使用免费试用 | **违反条款**。规避试用资格,冲突于准确信息与虚假账户条款 | 同上 |
| 凭证或订阅共享 | **违反条款**。消费者条款明文禁止共享凭证或将账户提供给他人 | 同上,另加仓库数据与账户活动的暴露 |
| 推荐链刷量 | 官方在营计划内的真实推荐正当;自我推荐、循环推荐、虚假账户刷量违反条款。目前未找到第一方 Grok 推荐计划 | 滥用循环:同上 |
| 灰市转售的账户、席位或 API key | **违反条款**。构成禁止的凭证共享或转售,且通常缺乏有效账户授权 | 账户或 key 终止、已付时长作废、原支付被争议时的撤销;另有数据安全暴露 |

本文不提供任何违反条款做法的操作步骤。对一位有联邦经费背景的教职人员,为节省二三十美元而触碰这些做法,风险收益比是负的。

---

## 11. 建议

### 11.1 主结论

**不为这个工作流购买 Grok 订阅。** 理由按证据强度排序:

1. 学术侧受 USC 政策、NSF 评审规则与消费者档留存政策共同约束,不合格,且与性能无关(第 7 节)。
2. 代码侧没有任何证据支持 Grok 是更好的审查者,而"多加一家厂商"的直觉本身证据薄弱(第 6 节)。
3. Windows 上没有操作系统级沙箱,而这正是七月事故暴露的那一层(7.2)。
4. 生产级第四后端需要 52 到 78 工时,加每年 16 到 32 工时维护,并永久留在公开分发面上(第 12 节)。
5. 300 美元档与 30 美元档运行同一个模型,多付的部分是不公开的周池(第 4、5 节)。

### 11.2 若仍要试,按此顺序

**第一步,先过数据安全门,再测权益。** 不得在 Windows 上从本仓库、任何未公开代码仓库、论文、提案或学生数据目录运行 Grok CLI。理由在 7.1 与 7.2:Windows 没有 OS 级沙箱 [S3],而该 CLI 有过整仓连同 git 历史上传的事故记录 [S12]。

只在厂商明确支持 OS 级沙箱的 Linux 或 macOS 隔离环境中,创建一个一次性仓库,内容仅含合成且可公开的数据。记录 CLI 版本、账号档位、地区与时间。执行 `grok login` 后运行 `grok -p "Reply only with OK"`(`-p` 必须带 prompt 字符串 [S2])。

成功只证明该账号在该时点可用,不能推导出持续的免费额度。401 记为认证失败,402 记为额度或消费限制,其他结果记为 UNVERIFIED。

**第二步,若需付费,购买 30 美元 SuperGrok 月付,不要年付。** 同时试一下 10 美元的 Lite 是否也授予 CLI 权限,发布公告只写 SuperGrok,没有说明 Lite 是否算数,无人验证过。不要购买 Plus 或 Heavy,没有证据支持为不公开的余量预付。

**第三步,启动前关闭 Auto Top Up 并清零 Extra Usage Credits 余额。** 这是防止无人值守超支的唯一闸门(5.3)。

**第四步,把一次性实验与正式接入分开。**

一次性实验的输出写入一次性状态目录,**不得命名为 `Review-*.md`**。`auto-watch.{sh,ps1}` 的 glob 就是 `Review-*.md`。把一个 review 形状的文件放进那个搜索路径、同时又跳过 Phase 2.0 检查,等于在现有 intake 逻辑一定会发现它的位置上绕开契约。实验结束后核对网络传输、服务端保留与删除证据。

正式后端若将来真要做,必须完整遵守 Phase 1c 的原子保存契约与 Phase 2.0 的 health checks,不能静默失败。`advisory-only` 只降低可用性故障对主流程的影响,它对 Windows 无沙箱、仓库上传和数据留存这三类风险没有任何缓解作用,不要把它当成安全措施。

**第五步,仪表化测量。** 每 50 到 100 轮记录一次 Settings 与 Usage 中的 Build 百分比。连续四个周重置都稳定低于 70% 才考虑年付。

**第六步,若公开代码或合成数据上的第二意见后来变成必需的,不要升档,改用 per-model API key 定向到表二**(5.2)。已公布单价、可设上限、附带不训练与 30 天删除的承诺 [S14]。**这不改变 7.3 节的数据分级限制:个人 API key 不得接收未公开的 USC 数据** [S4]。

### 11.3 更值得做的改动

本次调查真正的收获在别处。SWR-Bench [S25] 支持把多份独立审查聚合,并且**同时**验证了自聚合与跨模型聚合,论文不裁决哪一种更优。先试 Codex 自聚合是一个**本地选择**,依据是现有配额、更低的接入成本与更小的数据治理面,不是论文证明了同模型优于跨厂商。当前 `implement-review` 每轮只跑一次 Codex。

建议的实验:**同一批 staged diff,一次 `xhigh` 对三次相互独立的 `xhigh` 加聚合**,比较确认的 High 级发现数、误报率、token 成本与 wall-clock。该实验完全在既有的 Codex 独立配额内完成,不增加公开分发面,不引入第四家厂商的数据治理问题。若结果为正,skill 需要新增的是聚合与去重机制,那是当前缺失的部分。

**一处曾经写错的推理,记录在此以免重犯。** 本文初稿提议的是"三次 `high`",并论证 `SKILL.md:104` 的单向棘轮不适用,理由是该规则针对 agent 的自由裁量,而固定策略不涉及裁量。Round 1 审查指出这是在合理化,该判断成立。规范句是 "It must never pass a value below `xhigh`",无条件成立;消除逐轮裁量并不能使 `high` 达到或高于地板。理由解释规则,不划定规则的适用边界。

若确实要研究 `high` 的重复次数与质量权衡,有两条正当路径:在不调用现有 dispatcher 的离线评测 harness 中预注册方案,或者单独提交一项明确的 effort-policy 变更并让它走自己的审查。

### 11.4 与 Grok 无关但应当执行的一项

向 USC ITS 询问 Codex 的教职工提供(7.3)。维护者目前自费订阅,这可能直接免去一笔已在支付的费用。

---

## 12. 接入工程成本(若将来重新提出)

以下工时是**前瞻性估算**,由读取本仓库真实代码的单元给出。其中引用的行数、测试数与 parity 行为是实测值(复现命令见第 15 节末表),被估算的是完成这些工作所需的时间。

**生产级 `implement-review` 后端:52 到 78 工时。**

| 任务 | 工时 |
|---|---:|
| 活体 CLI spike | 5 到 8 |
| 传输与隔离设计 | 5 到 8 |
| Bash dispatcher 与 postflight | 6 到 8 |
| PowerShell dispatcher | 8 到 12 |
| health 签名与 stall/retry 决策 | 5 到 8 |
| skill 路由与文档 | 4 到 6 |
| 跨 shell mock 测试与回归 | 10 到 14 |
| parity、公开镜像、wheel 打包 | 4 到 6 |
| 双平台 dogfood | 5 到 8 |

窄原型 12 到 20 工时,但达不到 `dispatch-copilot` 的测试标准,不应公开发布。该标准在本次审查中实测为:`tests/test_dispatch_copilot.py` 有 **30 个 `def test_` 定义,pytest 收集到 50 个用例**,差额来自共享 mixin 被 Bash 与 PowerShell 两个具体类各继承一次。引用时用后一个数,或两个都写。`prun` 侧的 executor 再加 18 到 30 工时。

**维护税每年 16 到 32 工时**,每个破坏性 Grok CLI 版本另加 3 到 6 工时。

**可复用比例低于直觉。** `dispatch-copilot.sh` 共 387 物理行、**349 非空行**(该总数可由命令复现)。按物理职责的拆分是**人工估计,仓库内没有可复现的分类器**:可复用生命周期结构约 171 行,厂商特定的二进制发现、认证、调用、策略与错误处理约 178 行,合计 349。引用该比例时应连"人工估计"一起写,或先把分类台账落盘。可复用的那一半是设计模板而非可直接复制的代码。

**一个具体的陷阱。** `check-parity.sh` 的递归树比对会自动捕获新脚本,但**新测试文件不会被捕获**,除非同时插入显式共享测试清单与 `test_check_parity.py` 的成员下限。遗漏不会报错。

**降级行为需要如实描述。** 若 Grok 的流在进程仍存活时死亡:不写 marker,不 reap,不重新派发,600 秒后仅写一条软 stall 警告,且 marker 写入失败会被吞掉。但**审查结论的接受路径仍然 fail-closed**:缺失、过期或结构不合法的审查文件照样导致非零结果或 Phase 2.0 失败。准确的表述是"无人值守的死流恢复能力缺失",而不是"错误结论会被接受"。

首个版本应当与 Copilot 和 Claude 后端对齐,保留通用静默警告并验证最终产物,暂不实现立即重试。当前官方文档只确认 `streaming-json` 输出 [S2];`--prompt-file`、`end` 与 `error` 终止事件、以及 0/1/130/143 退出码目前**只有钉住 commit 的源码支持** [S31],必须由固定版本的 `grok --help`、实测样本或源码 permalink 复核。**在复核之前不得据此声称其终止谓词比 Codex 更干净。**

---

## 13. 未解决项

以下每一条都经过尝试且确认无法从公开来源得到答案,不是调查疏漏。

- **任何档位周池的绝对大小**,以 token、请求数、美元或计算单元计。xAI 只公布百分比 [S9]。这是最大的缺口,且是刻意不披露,Heavy 也不例外。
- **免费试用的账号资格、额度、地区、期限与重置规则。** 当前厂商页面只证明 CLI 带免费试用文案 [S1],而 FAQ 又把 Build 归入付费功能 [S9],两者冲突。第 11.2 节第一步是对这一条的实测,须在隔离环境中进行。
- **SuperGrok Lite 是否授予 CLI 权限。** 发布公告只写 SuperGrok。
- **Heavy 的年费。** FAQ 承认存在,无页面公布数字。
- **Extra Usage Credits 的实际费率是否等同开发者 API 价格。** xAI 称按"标准费率",未公布 Build 的额度资费表。一位 Heavy 用户实测 5 美元充值得到的是按秒计的 Imagine 费率,而非公开的 token 价目表。
- **X Premium Plus 与标准 SuperGrok 的配额是否等同。** 权益已确认,容量未确认。
- **npm 稳定版 1.0.5 的 flag 与钉住 commit 的一致性。** `--prompt-file` 存在于源码,稳定二进制需运行 `grok --help` 确认。
- **Grok Build 的 GA 状态。** 一方说 changelog 到 v1.0.5(8 月 15 日)[S22] 但无 GA 声明,另一方说 8 月 7 日发布 v1.0.0 即 GA。两边都发现 GitHub 仓库没有任何 release tag。
- **Grok 在代码审查任务上与 GPT-5.6 Sol、Opus 5 的受控对比。** 不存在。
- **端到端 CLI 任务延迟的匹配对比。** 不存在。
- **七月事故的历史数据是否真的已删除。** 仅有 xAI 自己的声明,无独立确认。

---

## 14. 方法与证据约定

### 14.1 证据分级约定

本文只把可复核的一手来源写成已核实。规则如下,后续修订必须沿用:

- **VENDOR / POLICY / PAPER / PRESS** 级来源在第 15 节登记,正文以 `[S#]` 引用。
- **COMMUNITY** 指社区实测(主要是 Reddit)。它可以用来给出量级和方差,**不得**当作厂商承诺或容量保证,引用时必须带 COMMUNITY 标签。
- 无法保留直接来源、或无法由本仓库命令复现的数字写成 **UNVERIFIED**,不得单独用它裁决购买、数据治理或接入决策。
- **面板结论本身不是证据来源。** 第 9 节的裁决依据的是各方引用的一手来源,不是"哪个面板说的"。

### 14.2 调查方法

第一轮六个单元:订阅权益、CLI 技术契约、能力对比、接入成本(读本仓库真实代码)、学术侧评估、以及一个 Claude 侧的交叉核验单元。第二轮两个 prun 单元(档位、优惠)加一个 21 个 agent 的 Workflow,三个研究维度,每个维度的结论交由对抗性 agent 逐条尝试证伪。

对抗性验证这一层产出了第 9 节的全部内容。若只跑单面板,至少四条错误结论会进入最终建议,其中两条会直接改变操作步骤。这一模式值得在后续的高风险选型调查中复用。

单元原始报告位于会话 scratchpad 的 `prun-grok/` 目录,Workflow 的逐 agent 返回值位于该 run 的 `journal.jsonl`。**两者都是临时文件,会随会话消失**,所以第 15 节是本文唯一的留存证据入口。

### 14.3 本文自身的审查历史

Round 1 由 Codex 审查,判定 BLOCK,4 High 加 2 Medium,全部接受并已修订。其中两条改变了结论:免费试用的裁决被当前一手证据推翻(见第 3 节与第 9 节),第 11.3 节的实验设计违反了 `SKILL.md:104` 的 effort 地板并已改正。该轮审查还发现初稿**零个 URL**,第 15 节即为其修复。

---

## 15. 证据登记

访问日期统一为 2026-08-22,除非另行标注。

### 厂商一手来源(VENDOR)

| ID | 支持的主张 | 来源 |
|---|---|---|
| S1 | Build CLI 当前带免费试用文案,额度与资格未公开 | https://x.ai/build · https://x.ai/news/grok-4-6 |
| S2 | headless 调用:`-p` / `--single` 携带 prompt,输出格式 `plain` / `json` / `streaming-json` | https://docs.x.ai/build/cli/headless-scripting |
| S31 | **仅源码级,未见于 docs 页**:`--prompt-file`、`end` 与 `error` 终止事件、退出码 0/1/130/143。核验于源码 commit `19d42e35c07a`;**稳定二进制是否一致为 UNVERIFIED**,仍需 `grok --help` 与活体样本 | https://github.com/xai-org/grok-build/blob/19d42e35c07a9c9244f03f6df0c4c353f970d4f9/crates/codegen/xai-grok-pager/src/app/cli.rs · https://github.com/xai-org/grok-build/blob/19d42e35c07a9c9244f03f6df0c4c353f970d4f9/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md |
| S3 | OS 级沙箱只覆盖 Linux(Landlock)与 macOS(Seatbelt),不覆盖 Windows;网络隔离 Linux 独有 | https://docs.x.ai/build/features/sandbox · https://github.com/xai-org/grok-build |
| S7 | 2026-05 CLI 公告,权益为 SuperGrok 与 X Premium Plus | https://x.ai/news/grok-build-cli |
| S8 | 档位阶梯与 SuperGrok Plus 100 美元;StoreKit SKU 与多区本地化 | https://x.ai/pricing · https://apps.apple.com/us/app/grok/id6670324846 |
| S9 | 共享周池、按产品拆分、免费档仅覆盖 Chat 与 Voice、Extra Usage Credits、Auto Top Up、周限行为 | https://docs.x.ai/grok/faq |
| S10 | 四种认证方式;凭证优先级 per-model key → session → 裸 `XAI_API_KEY`;device-code 适用于无浏览器主机 | https://docs.x.ai/build/enterprise |
| S11 | API 价格,含 20 万 token 长上下文双倍费率 | https://docs.x.ai/developers/pricing |
| S14 | API 档:不训练、30 天自动删除、静态加密;消费者档措辞明显更弱 | https://docs.x.ai/developers/faq/security |
| S15 | 周限耗尽在 CLI 源码中归类为 HTTP 402。核验于同一 commit `19d42e35c07a`;**稳定二进制未核** | https://github.com/xai-org/grok-build/blob/19d42e35c07a9c9244f03f6df0c4c353f970d4f9/crates/codegen/xai-grok-pager/src/app/dispatch/billing.rs |
| S16 | 权限模型:`--permission-mode`、`--allow` / `--deny`、`--tools` | https://docs.x.ai/build/features/permissions |
| S17 | `~/.grok/config.toml` 键位,含 per-model `api_key` / `env_key` | https://docs.x.ai/build/settings/reference |
| S18 | 消费者条款与可接受使用政策(禁止凭证共享、虚假信息、转售、规避限制;终止不退款) | https://x.ai/legal/terms-of-service · https://x.ai/legal/acceptable-use-policy |
| S19 | in-chat builder(原 Build Mode)与终端 CLI 是两个产品 | https://x.ai/news/grok-build-mode |
| S20 | Grok Bot 资格与计量归属;Cursor 联动条款 | https://docs.x.ai/grok-bot/faq · https://cursor.com/help/grok-bot/plans |
| S21 | X Premium 与 Premium Plus 价格及 Grok 权益措辞 | https://help.x.com/en/using-x/x-premium |
| S22 | CLI 变更日志(v1.0.5,2026-08-15) | https://x.ai/build/changelog |

### 机构与资助方政策(POLICY)

| ID | 支持的主张 | 来源 |
|---|---|---|
| S4 | USC 生成式 AI 政策:个人 AI 工具仅可接收公开数据;企业 AI 目录不含 Grok;ITS 向教职工提供 Codex | https://policy.usc.edu/generative-ai-general-policy/ · https://itservices.usc.edu/ai/ · https://itservices.usc.edu/ai/ai-faqs/ |
| S5 | NSF 禁止评审人将提案内容上传至未批准的生成式 AI 工具 | https://www.nsf.gov/policies/ai/merit-review |
| S23 | USC 提供 ChatGPT Edu,协议排除训练用途 | https://www.provost.usc.edu/faculty-guidance-chatgpt-edu-spring-2026/ |
| S24 | 会议规则:ICML 2026 / NeurIPS 2026 / ICLR 2026 | https://icml.cc/Conferences/2026/LLM-Policy · https://dev.neurips.cc/Conferences/2026/ai-reviewing-experiment · https://iclr.cc/Conferences/2026/ReviewerGuide |

### 研究文献(PAPER)

| ID | 支持的主张 | 来源 |
|---|---|---|
| S6 | SWE-PRBench:350 个 PR,八个模型仅找到人工标注问题的 15% 到 31%,更多上下文通常让结果变差 | https://arxiv.org/abs/2603.26130 |
| S25 | SWR-Bench:1000 个 PR;绝对 F1 最高 23.84%(Gemini 2.5 Pro 自聚合 n=5);相对增益最大为 Gemini 2.5 Flash 自聚合 n=10(F1 +43.67%,recall +118.83%);n=5 为实用甜点;同时评估了跨模型聚合 | https://arxiv.org/abs/2509.01494 · https://arxiv.org/html/2509.01494 |
| S26 | PoLL:异质评审团在判分任务上减少同族偏好 | https://arxiv.org/abs/2404.18796 |
| S27 | 模型一致性只是弱到中等的正确性信号(26.5 万样本) | https://arxiv.org/abs/2607.08065 |
| S28 | **仅覆盖第 6.1 节的五张评测分数表**(下列五个链接,Round 4 已逐项核对一致)。第 6.1 的 AA Intelligence Index 与 **6.3 的全部速度/吞吐数字不在本行覆盖范围内**,按 UNVERIFIED 引用 | https://artificialanalysis.ai/evaluations/gpqa-diamond · https://artificialanalysis.ai/evaluations/humanitys-last-exam · https://artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning · https://artificialanalysis.ai/evaluations/scicode · https://artificialanalysis.ai/evaluations/terminalbench-v2-1 |

### 事故与新闻(PRESS)

| ID | 支持的主张 | 来源 |
|---|---|---|
| S12 | 2026-07 Grok Build 整仓上传事故:含 git 历史与已提交 secret,约 27,800 倍数据量,`/privacy` 开关无效,受影响者为个人订阅者 | https://www.theregister.com/ai-and-ml/2026/07/14/musk-promises-purge-after-grok-build-caught-sending-entire-repos-to-the-cloud/5271123 · https://thehackernews.com/2026/07/grok-build-uploads-entire-git.html · https://thenextweb.com/news/grok-build-uploaded-entire-git-repositories-secrets |
| S29 | 开源后外泄代码仍留在版本中(2026-07-16 后续报道) | https://www.techtimes.com/articles/320671/20260716/grok-build-open-sourced-after-covert-upload-code-exfiltrate-repos-stays.htm |
| S30 | SpaceX 于 2026-02-02 收购 xAI,2026-07-06 更名 SpaceXAI | https://en.wikipedia.org/wiki/SpaceXAI · https://dataconomy.com/2026/07/07/elon-musk-rebrands-merged-xai-and-spacex-as-spacexai/ |
| S32 | Cursor 个人档位与额度池金额,以及各档的 Grok 权益措辞。**第一方页面对抓取器不渲染档位价格,金额取自二手来源,按 UNVERIFIED 引用** | https://cursor.com/pricing · https://cursor.com/docs/models-and-pricing |
| S33 | Cursor 两个额度池的计量机制:Auto 模式不扣池,手动选前沿模型或 Max Mode 才扣,耗尽后退回 Auto 或按 API 原价无加价续费 | https://usagebox.com/articles/cursor-usage-based-pricing-overage-explained-2026 |
| S34 | 用户报告在 400 美元承诺值的 250 美元处触及速率限制。**单一未验证报告** | https://forum.cursor.com/t/confusion-regarding-ultra-plan-api-value-hit-rate-limit-at-250-of-400-promised-value/126601 |
| S35 | Cursor `agent` CLI 存在 print 模式(`--output-format text`),官方定位为脚本与 CI;认证、计费归属、退出码约定均未记载 | https://cursor.com/docs/cli/overview |

### 社区实测(COMMUNITY,不是厂商保证)

| ID | 支持的主张 | 来源 |
|---|---|---|
| S13 | 第 5.4 节表格的全部社区测量,逐条来源见下表 | 见下表 |

这些是个别用户在特定工作负载下的观察,服务端权重可随时调整,**不得**据此做容量规划,也不得当作厂商承诺。

| 观察 | 来源 |
|---|---|
| SuperGrok 30 美元档:约 2.6M 含缓存 token 每 1%,缓存命中 94% 到 95% | https://www.reddit.com/r/cursor/comments/1vokcwq/ |
| SuperGrok 30 美元档:最低推理档一天消耗 40% | https://www.reddit.com/r/grok/comments/1v6azkg/ |
| SuperGrok:试用 Build 第一天即触及周限 | https://www.reddit.com/r/grok/comments/1u9uwxk/ |
| SuperGrok:五天以上重度 CLI 使用未触及周限(反向证据) | https://www.reddit.com/r/grok/comments/1uox2uq/ |
| Heavy:六小时 xhigh 编码消耗 10% | https://www.reddit.com/r/codex/comments/1vqjhn2/ |
| Heavy:大规模 agent 集群难以耗尽后 50% | https://www.reddit.com/r/grok/comments/1v6bc1u/ |
| Heavy:设置显示 15% 但 Build 返回周限错误(已确认的 bug) | https://www.reddit.com/r/grok/comments/1utm6n2/ |
| Heavy:5 美元充值的实际扣费口径 | https://www.reddit.com/r/grok/comments/1uwj3ng/ |
| Heavy:七个并行终端的消耗观察 | https://www.reddit.com/r/GrokBuild/comments/1vs40aa/ |

### 本仓库内可复现的测量

以下数字由命令产生。**带滑动窗口的那几项只有配上第 2 节的固定 ISO 截止日才可复现**,否则重跑会得到不同窗口;其余各项在给定基准 commit 上可直接复跑:

| 主张 | 复现命令 |
|---|---|
| 提交计数 34 / 17 | `git rev-list --count --since=2026-07-23T00:00:00 132c0bde2cf61c45d7220224b7a6a79392dbf259`,`--since=2026-08-15T00:00:00` |
| 均值 587.15(最近 40 次提交,总 23,486 行除以 40) | `git log -40 --shortstat` |
| 均值 678.82(30 天窗口,34 次提交,23,080 行) | `git log --since=2026-07-23T00:00:00 --numstat 132c0bde2cf61c45d7220224b7a6a79392dbf259` |
| `dispatch-copilot.sh` 349 非空行 | `grep -c '[^[:space:]]' skills/implement-review/scripts/dispatch-copilot.sh` |
| 30 个测试定义 / 50 个收集用例 | `rg -c "^\s*def test_" tests/test_dispatch_copilot.py`;`pytest --collect-only -q tests/test_dispatch_copilot.py` |
| 严格共享测试清单与成员下限 | `scripts/check-parity.sh`,`tests/test_check_parity.py` |
