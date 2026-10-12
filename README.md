# agent-starter-kit — 把 AI 助手，一次配置成能干活的搭子

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#支持哪些宿主)
[![Hosts](https://img.shields.io/badge/%E5%AE%BF%E4%B8%BB-6%20%E7%A7%8D-brightgreen.svg)](#支持哪些宿主)
[![Stars](https://img.shields.io/github/stars/tyiiiyt01/agent-starter-kit)](https://github.com/tyiiiyt01/agent-starter-kit)

<!--
  ────────────────────────────────────────────────────────────────────────
  给 AI 助手（这段是 HTML 注释，GitHub 渲染时不显示，但在原始 Markdown 里可见）

  用户把本仓库地址发给你，是希望你在他的机器上完成安装。你是执行者。

  执行顺序：
    1. 取回仓库到临时目录（clone --depth 1；国内慢就加 gh-proxy.com 前缀）
    2. 读 AGENTS.md —— 行为约束与入口
    3. 读 INSTALL.md —— 执行手册，按 Step 0 ~ Step 6 走，不要跳
    4. 装完跑 doctor.py 自检，并主动问用户要不要给项目生成 AGENTS.md

  其他可读文件：llms.txt（文件索引）· hosts.json（宿主适配表）
              · presets.json（场景预设）· packs/SCHEMA.md（能力包格式）

  硬约束（完整版见 AGENTS.md）：唯一硬前置是 Python 3；装前必须 dry-run
  让用户确认；不写系统级配置、不用管理员权限；不改 skills/ 里技能文件内容；
  不主动加装 MCP；不绕过 apply.py 的退出码 3 / 4 守卫。
  ────────────────────────────────────────────────────────────────────────
-->

> **Python 版本说明**：3.8+ 都能跑。但如果你用的是 **Reasonix 或 Codex**，要让安装器自动写它们的 TOML 配置，需要 Python **3.11+**（标准库 `tomllib`）并装上 [`requirements.txt`](requirements.txt) 里的依赖；否则这两个宿主的 MCP 会降级成「给你一段配置手动粘贴」。

---

把你自己那个 AI 助手接入可用的 API，然后把本仓库地址**粘进对话框**：

```console
$ # 复制下面这一行，粘进对话框发送（不用敲终端）
$ https://github.com/tyiiiyt01/agent-starter-kit
🤖 助手：收到。先探测一下你的环境……
   ✓ 检测到 Claude Code（macOS）
   ✓ Python 3.11 · Node.js 20 · uv 已就绪
🤖 助手：根据你说的用途，我打算装这些 ——
   ├ 技能   code 包的 python-workflow、cpp-workflow
   ├ MCP    filesystem
   └ 依赖   numpy、matplotlib、pandoc（约 40 MB）
   你回复「确认」我才动手。
你：确认
🤖 助手：装好了，自检通过。现在可用：Python 跑通闭环、
   matplotlib 中文绘图、pandoc 文档互转。
   要不要顺手给你的项目也生成一个 AGENTS.md？
```

上面这一幕，就是本项目的全部用法：**粘一行地址、说一句用途，剩下它全包。**

### 这是个什么东西

打个比方：你请了一位**很聪明、但完全不了解你工作**的实习生 —— 他脑子好使（就是你已经接好 API 的那个 AI 助手），可不知道你们学校的论文怎么排版、公司的周报要什么格式、实验数据该画成什么样。

这个仓库做的事，就是给这位实习生**发一份岗位手册、再配齐办公用品**：告诉它每一类活儿该怎么干，再把要用到的工具放到它手边。

它往你电脑上放的，其实就三样东西：

- **技能（skill）** —— 一份写给助手看的**操作手册**。比如「写论文」技能会告诉它：参考文献要按 GB/T 7714 排、图表里的中文别显示成方框、学校模板有哪些坑。这些事它本来不会，装上就会了。
- **MCP** —— 助手的**额外接口 / 插件**，让它能真正动手操作你本机的文件、网页等，而不只是陪你聊天。本套件对这块很克制，只装真正必要的。
- **依赖** —— 技能背后真正干活的**工具**（比如画图用的 Python 库、文档互转用的 pandoc）。技能是「说明书」，依赖是「说明书里要用的那台机器」。

### 它替我省掉了什么麻烦

**没有它的时候**，这些全得你自己来：翻教程、一条条敲安装命令（`pip install` 该装什么、装哪个版本，全靠摸索）、满世界找好用的技能文件、手工编辑助手的配置文件去加插件，最后还常常卡在「明明装了、助手却说找不到」这种说不清的问题上（行话叫 **PATH** 问题）。

**有了它**：探测环境、挑选技能、安装依赖、自检验证，全交给你的助手；动手之前先把清单摆给你看，你点「确认」它才开工。你全程只做两件事 —— **粘地址、点确认**。

📖 快速开始 · 🧩 [能力清单](#八个能力包--十七个技能) · ❓ [常见问题](#常见问题-faq) · ⬆️ [更新](#更新) · 🗑️ [卸载](#卸载)

## 目录

- [为什么用它](#为什么用它)
- [它到底做了什么](#它到底做了什么)
- [它不做什么](#它不做什么)
- [快速开始](#快速开始)
- [支持哪些宿主](#支持哪些宿主)
- [场景预设](#场景预设)
- [八个能力包 · 十七个技能](#八个能力包--十七个技能)
- [MCP 要克制](#mcp-要克制)
- [社区高星技能](#社区高星技能)
- [依赖分档](#依赖分档)
- [国内网络](#国内网络)
- [安全与边界](#安全与边界)
- [常见问题 FAQ](#常见问题-faq)
- [更新](#更新)
- [出问题了怎么办](#出问题了怎么办)
- [卸载](#卸载)
- [目录结构](#目录结构)
- [贡献](#贡献)
- [许可证](#许可证)

## 为什么用它

- **不用懂技术** —— 你只要说一句「我想写毕业论文」，它自己判断该装什么、怎么装、装完怎么验。你只需**粘地址、点确认**。
- **一次装齐全套** —— 编程、文献、数据、办公、学习五大方向的 17 个技能一次到位。**所以呢**：不用再「今天找个画图技能、明天配个文献工具」，省下的是你拼凑、调试的一整个下午。
- **装什么是确定的** —— 技能文件逐字节一致，你机器上的结果和别人完全一样；动手前先给你看清单。**所以呢**：不会出现「别人能用、到你这里就报错」的玄学差异。
- **专治「装了却用不了」** —— 自动检测没进 PATH 的工具并补一条转发脚本，自检会**真的执行一遍**确认能跑，而不是只看文件在不在。**所以呢**：告别「明明装了，助手却说找不到」。
- **不把 AI 变笨** —— 每个包只挂真正必要的少数插件（实测 3 个就能吃掉 200k 上下文的 72%）。**所以呢**：不会越装越慢、越装越健忘。
- **试错成本低** —— 可以先空跑预演（dry-run）、记一份「装过什么」的账本、按指引一键卸载，只删它自己装过的条目。**所以呢**：敢用、敢退，不怕把电脑搞乱。

## 它到底做了什么

不列功能名，说人话 —— 它在这些具体时刻替你干活：

- **写实验报告**：你手里有一份实验数据。以前得自己排版、自己调图表字体（中文经常显示成方框），还得套学校模板。现在把数据发给它，说一句「帮我写成实验报告」，它生成一份能直接交的 `.docx`。
- **写毕业论文**：查文献、精读 PDF、按学校模板排版、把参考文献整理成规范引用格式 —— 它一步步陪你走，你不用手动调样式。
- **整理数据**：一堆乱糟糟的 Excel / CSV，你说想按什么维度汇总、画什么图，它负责清洗、计算、出图，中文标签也不会乱码。
- **上课与作业**：把课件或题目发给它，它给你讲思路、拆步骤、出同类题帮你练（**只讲解和引导，不给答案**）。
- **办公日常**：把会议录音或速记整理成纪要；把一批文档套模板批量生成；把 PDF / Word / 表格互相转换。

> **一句诚实的边界**：它产出的文档追求的是「**结构正确、格式规范、能直接用**」，**不是「设计得赏心悦目」**。想要有设计感的整套 PPT，需要额外加装社区里的 `ppt-master` 技能（见 [社区高星技能](#社区高星技能)）；报告里的图表是「清晰、规范、中文不乱码」，不是「杂志级视觉」。宁可把话说保守，也不让你装完失望。

## 它不做什么

这套东西只做该做的。下面几件事它**明确不做**：

- **不代写作业** —— 学术诚信优先，它给的是讲解、步骤引导和校验，不给答案。
- **不绕付费墙** —— 知网等收费数据库只做合规检索，不提供任何绕过访问。
- **不装商业软件** —— 如 MATLAB（商业授权、几十 GB）：检测到就用，没有则降级用 Octave 跑 `.m` 兼容语法。
- **不操控正在运行的 Office 窗口** —— 只做文件级读写（`.docx` / `.xlsx` / `.pptx`），不碰你打开着的 Word 窗口。
- **不静默改系统** —— 不写系统级配置、不用管理员权限、不悄悄改你的设置，一律装到你的用户目录；需要系统弹窗确认的（如 macOS 装 Xcode 命令行工具）会引导你自己点。

## 快速开始

### ① 我想一句话就装（推荐）

1. 先确保你**已经装好某个 AI 助手，并且接入了可用的 API**
2. 把本仓库地址粘进对话框，再补一句用途，例如：`https://github.com/tyiiiyt01/agent-starter-kit 我要写毕业论文`
3. 助手会自己探测环境、匹配场景、打印清单；**你回复确认**它才动手，装完再跑一遍自检，告诉你哪些能力现在可用

> 你不需要懂命令行，它会引导你。最后它还会问：**要不要给当前项目生成一个 `AGENTS.md`** —— 建议答应，这是新手最该配的一项，能让 AI 记住你的项目约定，省得每次重复交代。

**它会在仓库里读这几个文件来干活**（你的助手自己去读，你不用管）：

| 文件 | 干什么的 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 行为约束 —— 它被允许做什么、禁止做什么 |
| [`INSTALL.md`](INSTALL.md) | 执行手册，Step 0 → Step 6 |
| [`llms.txt`](llms.txt) | 文件索引 —— 一页看清整个仓库该看哪些文件 |
| [`hosts.json`](hosts.json) · [`presets.json`](presets.json) | 宿主适配表 · 场景预设 |

> 想核对它会做什么，打开上面任意一个文件都能自己看 —— 全是明文，没有隐藏逻辑。

### ② 我想自己挑

直接用包名点名（包名见下节「八个能力包」），例如：`用 agent-starter-kit 帮我装 code 和 study 两个包`；想加社区技能也行：`帮我加上 anthropics-skills`。

> 匹配不上用途时，默认只装 `code`（最小可用），并告诉你以后可以随时加。

## 支持哪些宿主

| 宿主 | 技能目录 | MCP 配置 | 核实状态 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `claude mcp add --scope user` | ✅ 已核实 |
| Cursor | `~/.cursor/skills/` | `~/.cursor/mcp.json` | ✅ 已核实 |
| Trae（国际版） | `~/.trae/skills/` | `<配置目录>/User/mcp.json` | ✅ 已核实 |
| Trae CN（国内版） | `~/.trae-cn/skills/` | `<配置目录>/User/mcp.json` | ⚠️ 部分核实 |
| Reasonix | 工作区内的 `.reasonix/skills/`（如 `~/.reasonix/global-workspace/.reasonix/skills/`） | `~/.reasonix/config.toml` 的 `[[plugins]]` 段 | ✅ 已核实路径（工作区制） |
| Codex CLI | `~/.codex/skills/` | `~/.codex/config.toml` | ⚠️ 未核实 |
| **其他** | — | — | 由 AI 现场推断 + 自检复核 |

> **Reasonix 是工作区制**：技能装在**工作区内部**的 `.reasonix/skills/`，不同工作区各有独立目录，所以安装时会问你「当前用哪个工作区」。MCP 配置写在 `~/.reasonix/config.toml` 的 `[[plugins]]` 数组表里。
>
> 标 ⚠️ 的宿主：路径可能未完全准确。**装的时候 AI 会先让你确认一次真实路径**，装完由自检复核，猜错了会被抓出来 —— 不会静默写错。

## 场景预设

你不用说包名 —— 只要说一句「我要写毕业论文」，AI 就知道该装哪些：

| 你说 | 装什么 |
|---|---|
| 我要写毕业论文 | `research` `writing` |
| 我要参加数学建模竞赛 | `math-modeling` `code` `writing` |
| 我要上专业课 / 备考 | `study` `code` |
| 我在公司上班 | `office` `office-work` |
| 我搞学生工作 / 做宣传物料 | `design` `office` |
| 我要做科研 / 发小论文 | `research` `writing` `math-modeling` |
| 理工科课程作业 | `code` `study` `writing` |
| 全都要 | 八个包全装 |

## 八个能力包 · 十七个技能

| 包 | 面向 | 技能 |
|---|---|---|
| `code` | 写代码 | `python-workflow`（Python 跑通闭环 + matplotlib 中文字体）· `cpp-workflow`（C++ 编译 + Octave 降级跑 `.m`） |
| `research` | 查文献与调研 | `paper-research`（检索 + PDF 精读 + GB/T 7714）· `cn-literature`（中文文献合规检索）· `citation-management`（Zotero + BibTeX）· `web-research`（网页抓取与数据调研） |
| `math-modeling` | 数模竞赛 | `math-modeling`（审题→建模→求解→灵敏度→写作，含求解器选型表） |
| `writing` | 写论文 | `thesis-format`（套学校模板排版）· `academic-figures`（600dpi / 矢量 / 中文字体）· `lab-report`（误差传递 + 拟合） |
| `office` | 文档与数据 | `office-docs`（docx/xlsx/pptx/pdf 文件级读写）· `data-analysis`（pandas 清洗）· `doc-batch`（docxtpl 批量生成） |
| `office-work` | 办公协作 | `meeting-notes`（会议转写纪要）· `email-calendar`（邮件日程） |
| `study` | 学习 | `study-tutor`（专业课讲解 + 习题引导 + OCR→LaTeX） |
| `design` | 设计素材 | `design-material`（图片批处理、海报物料、二维码、中文字体） |

**Office 能力全部用纯 Python 库实现**（python-docx / openpyxl / python-pptx / pypdf / docxtpl），不依赖 Office 客户端，也不装第三方 Office MCP —— 少一层运行时，少一个失败点。

## MCP 要克制

这条和「装得越多越好」相反。实测数据：**3 个 MCP 就能吃掉 200k 上下文里的 143k tokens（72%）**，7 个 MCP 首轮烧 67,300 tokens。**MCP 装多了，agent 会明显变笨。**

所以本套件的设计是：

- 每个包**只挂它真正需要的少数几个** MCP，不搞「必装十大 MCP」
- 每个包标记一个 `essential`，用 `--minimal-mcp` 可以只留这一个
- 如果你觉得 AI 反应变慢、记不住前面说的话 —— 大概率是 MCP 吃掉了上下文，试试 `--minimal-mcp`

## 社区高星技能

以下为可选加装。除了自带的 17 个技能，`community-skills.json` 还收录了一份社区高星技能清单，你可以按需加装：

| 技能 | Star | 说明 |
|---|---|---|
| `anthropics-skills` | ~180k | Anthropic 官方 docx / pptx / xlsx / pdf 四件套 |
| `obra/superpowers` | ~296k | 工程方法论元技能（偏重，适合常写代码的人） |
| `ui-ux-pro-max-skill` | ~133k | UI / 设计 |
| `ppt-master` | ~61k | 从零生成整套设计 PPT |
| `cloudflare/security-audit-skill` | ~28k | 安全审查 |
| `MathModeling-skills` | ~1.06k | 数模分阶段流程 |

其中 `anthropics-skills` 和 `ppt-master` 是**默认就装**的 —— 它们补的是基础能力的短板：

- **`anthropics-skills`**（官方四件套）补的是"复杂文档"：Word 的修订/批注/目录、设计级 PPTX，比本套件自写的技能更可靠
- **`ppt-master`** 补的是"设计"：`python-pptx` 只能摆结构（文本框、图片、位置），**做不出设计**；要「精美 PPT」得靠它

其余的默认不装 —— 技能和 MCP 一样，不是越多越好。想要更强的能力时，直接对助手说 `帮我加上 superpowers`（它会先告诉你许可证风险）；想自己动手则运行：

```bash
python3 scripts/apply.py --packs code --with-community all          # 全部 13 个
python3 scripts/apply.py --packs code --with-community superpowers  # 点名
python3 scripts/apply.py --packs code --no-community-defaults       # 连默认那两个也不要
```

> ⚠️ 这些都是第三方仓库，**许可证各不相同**（有 MIT，也有再分发受限的）。清单里的 `license_risk` 字段标了风险，安装时会提示。

## 依赖分档

这一节重要，别跳过。技能要跑得动，得有关键工具。这套东西按体积分了三档，**默认只装轻量的**：

| 档 | 例子 | 体积 | 策略 |
|---|---|---|---|
| `light` | pandoc · poppler · markitdown · tectonic · scipy | 几十 MB | 默认自动装 |
| `medium` | pdf2zh（含翻译模型）· scikit-learn | 100MB–1GB | 需 `--tier medium` |
| `heavy` | LibreOffice（≈700MB） | >1GB | **永不自动装**，只检测 + 给引导 |

### 「装了却用不了」的解药

很多东西**装上了但不在 PATH**，命令调不到 —— 这是这套配置最常见的失败模式。例如 macOS 上的 LibreOffice 位于 `/Applications/LibreOffice.app/Contents/MacOS/soffice`、pandoc 官方单文件安装器不写 PATH、TinyTeX 的链接丢在 `/usr/local/bin` —— 这些目录常常不在 PATH。

所以本套件会自动检测这些**已知位置**，命中就建一个转发脚本（shim）修好，并且自检会**真的执行一遍**来确认可用 —— 不是只看文件在不在。

### 还做了两件事减少对大件的依赖

1. **PDF 处理优先用 `PyMuPDF`**（纯 pip，免 sudo，无需装 poppler 二进制），只有真需要 poppler 命令行时才装它
2. **LaTeX 编译优先用 `tectonic`**（单个二进制约 50MB，按需下载宏包），而不是 TinyTeX / MacTeX（超过 1GB）

## 国内网络

这块决定安装成败。直连 GitHub Releases 经常掉到 **30 KB/s**，几百 MB 的东西直接卡死。本套件内置了多路加速：

- **GitHub**：自动回退 `直连 → gh-proxy.com → ghfast.top → ghproxy.net → hub.gitmirror.com`
- **生成镜像配置文件** `~/.agent-starter-kit/mirrors.env`，`source` 一下就生效：

| 变量 | 值 | 为什么 |
|---|---|---|
| `PIP_INDEX_URL` | 清华 PyPI 镜像 | pip 直连国内很慢 |
| `HF_ENDPOINT` | `https://hf-mirror.com` | **最关键** —— 语音转写 / PDF 翻译类工具要先下模型，不配这个下不动 |
| `NPM_CONFIG_REGISTRY` | `https://registry.npmmirror.com` | npm 同理 |
| `PYTHONUTF8` | `1` | 避免 Windows 中文乱码 |

> ⚠️ 公益镜像有掉线、限速的风险，**不要用于私有仓库**。镜像失效很快，所以我们内置多路回退，而不是写死一个。

## 安全与边界

> ⚠️ **动手前请先读这一段。** 本套件的核心承诺是「**看得见、由你拍板、可撤回**」。

- **装什么、装成什么样，是完全确定的** —— 技能文件逐字节一致，你机器上的结果和别人的一样
- **装之前会先给你看清单**，你确认才动手；`scripts/apply.py --dry-run` 可以先预演一遍什么都不写
- **可查看、可卸载**：`uninstall.md` 给卸载指引，只删本套件装过的条目
- 全程**不碰系统级配置**，不写入需要管理员 / root 权限的目录（一律装到用户目录）
- **不碰你的 API Key、账号与登录信息**
- ⚠️ **不绕付费墙**：不提供 CNKI 等收费库的绕过访问，只做合规检索
- ⚠️ **不代写作业**：学术诚信优先，「做题能力」= 讲解 + 步骤引导 + 校验，不给答案

## 常见问题 FAQ

**Q：我需要懂命令行吗？**
不需要。你只负责把仓库地址粘进对话框、回一句用途、确认清单；探测、安装、验证都由助手完成，它会一步步引导你。

**Q：它会装什么东西到我机器上？**
三类，都会在动手前列成清单让你确认：① 技能文件（就是一批 Markdown，放进你助手的技能目录）；② MCP 配置（合并写进你助手的配置文件，或走宿主自带命令注册）；③ 依赖（Python 包 + 命令行工具，默认只装几十 MB 的轻量档）。本套件会记一份账本 `~/.agent-starter-kit/state.json`，装过什么一目了然。

**Q：装坏了怎么办？**
按 [`uninstall.md`](uninstall.md) 卸载。它只删账本里记录过的条目，绝不碰你自己配的 MCP、技能和文件。注意：Python 包和命令行工具**默认不自动卸**（因为可能被你的其它项目用着），会列出来交给你自己决定。

**Q：会不会很慢 / 我要下多少东西？**
默认只装 `light` 档，通常几十 MB。`medium` 档（100MB–1GB）需要显式加 `--tier medium`；`heavy` 档（如 LibreOffice，约 700MB）**永不自动装**，只做检测并给你安装引导。

**Q：我没有 API Key、还没接入 API，能用吗？**
不能。**已装好某个 AI 助手并接入可用 API 是硬前置** —— 整套流程都是由你的助手来执行的。另外 Python 3.8+ 是唯一的硬性环境要求（Windows 上还会避开「微软商店 stub」陷阱）。

**Q：能只装一部分吗？**
能。要么直接点名包（「帮我装 code 和 study」），要么说一句用途让它按场景预设匹配，要么只说「就装代码相关的」。匹配不上时它默认只装 `code`，并告诉你以后随时能加。

**Q：为什么有些东西明明装了却用不了？**
大多数是 **PATH 问题** —— 程序装在磁盘上，但那个目录不在 PATH，命令调不到（如 macOS 的 LibreOffice、pandoc 单文件安装器）。本套件会自动检测已知位置并建转发脚本（shim）修好，自检也会真的执行一遍确认。如果仍调不到，跑一次 `apply.py`（幂等，不会重复装）重建 shim 即可。

## 更新

本套件的安装是**幂等**的：重复跑不会重复装，只会补齐缺的、更新旧的。

- **更新到最新版**：把仓库地址**再粘一次**给助手，让它重跑一遍即可。它会重新拉取最新代码，再对当前环境做一次「差量安装」。
- **锁定版本**（想要可复现的行为时推荐）：

  ```bash
  git clone --branch v0.1.0 --depth 1 https://github.com/tyiiiyt01/agent-starter-kit
  ```

  当前已发布 `v0.1.0`。`--branch v0.1.0` 把行为固定在那一版，不再随 `main` 漂移；`--depth 1` 只取这一版。
  变更记录见 [CHANGELOG.md](CHANGELOG.md)，为什么建议锁版本见 [SECURITY.md](SECURITY.md) 第 3.4 节。
- **只是想补装某个包 / 技能**：直接说「再帮我装 `design` 包」或「加上 `anthropics-skills`」，不用整套重来。

## 出问题了怎么办

| 症状 | 先试这个 |
|---|---|
| 命令「装了却调不到」 | 让助手跑一次 `apply.py`（幂等）重建 shim；或检查该工具的目录是否在 PATH |
| AI 变慢、记不住前文 | 大概率是 MCP 吃上下文，让助手用 `--minimal-mcp` 只保留 `essential` |
| 国内下载卡在几 KB/s | 用 `~/.agent-starter-kit/mirrors.env` 里的镜像，或让助手加 GitHub 加速前缀重试 |
| 大件依赖下载超时 | 不要死等 —— 让助手直接跳过该项，改用替代方案（如 poppler → PyMuPDF） |
| 技能没生效 | 让助手跑 `scripts/doctor.py` 逐项自检，它会真的执行一遍来验证 |
| 想彻底回退 | 见下方「卸载」，按账本逐条移除 |

> 实在卡住时，把**原始报错原文**发给助手，比描述「它不工作」有用得多。

## 卸载

一句话：**让助手读 [`uninstall.md`](uninstall.md) 执行卸载**（例如「按 uninstall.md 把 agent-starter-kit 卸掉」）。

要点：

- **以账本为准**：只删 `~/.agent-starter-kit/state.json` 里记录过的技能、MCP 条目与 shim
- **只删自己装过的**：你在别处配的 MCP、技能和文件，一个都不动
- **依赖默认不卸**：Python 包与命令行工具会列出来，由你自己决定（避免弄坏无关项目）
- 卸载前它会先打印一份清单，**等你确认**才动手

## 目录结构

```
agent-starter-kit/
├── README.md             ← 你正在看的
├── AGENTS.md             ← 助手的行为约束（它会自动读这个文件）
├── INSTALL.md            ← 执行手册（Step 0–6），助手照这个走
├── llms.txt              ← 文件索引，方便助手一页看懂整个仓库
├── uninstall.md          ← 卸载指引
├── SECURITY.md           ← 安全披露政策与本项目的风险边界
├── CHANGELOG.md          ← 版本变更记录
├── LICENSE               ← Apache-2.0
├── requirements.txt      ← 安装引擎自身的依赖（tomli-w）
├── hosts.json            ← 宿主适配表，加新宿主只改这里
├── presets.json          ← 场景预设（"我要写论文" → 装哪些包）
├── community-skills.json ← 社区高星技能清单（可选安装，带 star 与许可证）
├── templates/
│   ├── AGENTS.md.template            ← 给你自己的项目用的 AGENTS.md 模板
│   ├── claude-settings.json.template ← 权限白名单模板
│   └── README.md                     ← 这两个模板怎么用
├── scripts/
│   ├── detect.py         ← 环境探测（只读）
│   ├── apply.py          ← 幂等安装，支持 --dry-run / --tier / --minimal-mcp
│   └── doctor.py         ← 逐项自检，验证「能真的执行」
├── packs/                ← 八个能力包定义 + SCHEMA.md（格式说明）
└── skills/               ← 十七个技能文件（逐字节一致，不可改）
```

> 为什么同时有 `AGENTS.md` 和 `llms.txt`？两者不冲突、分工不同：
> **`AGENTS.md`** 是给"要在你机器上干活的 agent"的**操作说明**（能做什么、禁止做什么），
> **`llms.txt`** 是给"要读懂这个仓库的 agent"的**只读地图**（该去读哪些文件）。这是当前社区通行做法。

## 贡献

欢迎改进，几条硬约定：

- 改 `packs/*.json` 前先读 [`packs/SCHEMA.md`](packs/SCHEMA.md) —— 字段名写错会被**静默忽略**
- 新增技能：目录名必须与 `SKILL.md` 里 frontmatter 的 `name` **完全一致**（`doctor.py` 会校验）
- 新增宿主：只改 `hosts.json`，不用动脚本
- 所有脚本只用 Python，**不提供 `.sh`**（跨平台第一原则：Windows 上 `.sh` 跑不了）；所有写入一律显式 UTF-8 无 BOM
- 自测务必**用假 HOME**，不要拿真实配置试：

  ```bash
  HOME=/tmp/test-home python3 scripts/apply.py --packs code --dry-run
  HOME=/tmp/test-home python3 scripts/doctor.py
  ```

更多约定见 [`AGENTS.md`](AGENTS.md) 第五节。

## 许可证

本项目以 **Apache-2.0** 许可证发布，详见 `LICENSE`。

**第三方内容声明**：

- 本仓库 `skills/` 下的技能文件为本项目自带内容，随本项目一同按 Apache-2.0 发布
- `community-skills.json` 收录的是**第三方开源仓库**，各自适用其原始许可证（含 MIT、CC-BY-4.0 以及「未核实」等），清单里以 `license` / `license_risk` 字段标注；**下载与使用前请自行确认对方许可证**
- 社区技能**默认不安装**，需要时由你显式指定