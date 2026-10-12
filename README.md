# agent-starter-kit — 给大学生和办公人群的 AI 助手一键配置包

> 🤖 **如果你是 AI 助手**：用户把本仓库地址发给你，是希望你在他的机器上完成安装。
> 请先读 [`AGENTS.md`](AGENTS.md)（行为约束），再按 [`INSTALL.md`](INSTALL.md)（执行手册）操作。
>
> 👤 人类读者直接往下看即可 —— 你不需要懂命令行。

---

## 这是什么

帮你把手上那个 AI 助手（Claude Code / Cursor / Trae / Reasonix / Codex…）**一次配置到位**，装上大学生和办公人群真正用得上的能力：

- **编程**：Python、C++、MATLAB 代码的编写与运行闭环
- **文献**：检索、PDF 精读、参考文献格式、翻译
- **数据**：清洗、分析、画图（含中文字体配置）
- **办公**：Word / Excel / PPT / PDF 文件级读写
- **学习**：专业课讲解总结、习题引导

## 怎么用

1. 先确保你已经装好某个 AI 助手，并且**接入了可用的 API**
2. 把本仓库地址**粘贴到对话框**，然后发送
3. 你的助手会自己读、自己探测环境、自己装
4. 中途它会给你一份「即将安装什么」的清单，**你回复确认**它才会动手
5. 装完它会跑一遍自检，告诉你哪些能力现在可用

> 你不需要懂命令行。它会引导你。

最后一步它还会问你：**要不要给当前项目生成一个 `AGENTS.md`**。建议答应 —— 这是新手最该配的一项，能让 AI 记住你的项目约定，省得每次重复交代。

## 支持哪些宿主

| 宿主 | 技能目录 | MCP 配置 | 核实状态 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `claude mcp add --scope user` | ✅ 已核实 |
| Cursor | `~/.cursor/skills/` | `~/.cursor/mcp.json` | ✅ 已核实 |
| Trae（国际版） | `~/.trae/skills/` | `<配置目录>/User/mcp.json` | ✅ 已核实 |
| Trae CN（国内版） | `~/.trae-cn/skills/` | `<配置目录>/User/mcp.json` | ⚠️ 部分核实 |
| Reasonix | `~/.reasonix/skills/` | `~/.reasonix/config.toml` | ⚠️ 部分核实 |
| Codex CLI | `~/.codex/skills/` | `~/.codex/config.toml` | ⚠️ 未核实 |
| **其他** | — | — | 由 AI 现场推断 + 自检复核 |

标 ⚠️ 的宿主：路径可能未完全准确。**装的时候 AI 会先让你确认一次真实路径**，装完由自检复核，猜错了会被抓出来 —— 不会静默写错。

## 场景预设（你不用说包名）

你只要说一句"我要写毕业论文"，AI 就知道该装哪些：

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

匹配不上时默认只装 `code`（最小可用），并告诉你以后可以随时加。

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

## MCP 要克制（这条和"装得越多越好"相反）

实测数据：**3 个 MCP 就能吃掉 200k 上下文里的 143k tokens（72%）**，7 个 MCP 首轮烧 67,300 tokens。**MCP 装多了，agent 会明显变笨。**

所以本套件的设计是：

- 每个包**只挂它真正需要的少数几个** MCP，不搞"必装十大 MCP"
- 每个包标记一个 `essential`，用 `--minimal-mcp` 可以只留这一个
- 如果你觉得 AI 反应变慢、记不住前面说的话 —— 大概率是 MCP 吃掉了上下文，试试 `--minimal-mcp`

## 社区高星技能（可选）

除了自带的 17 个技能，`community-skills.json` 还收录了一份社区高星技能清单，你可以按需加装：

| 技能 | Star | 说明 |
|---|---|---|
| `anthropics-skills` | ~180k | Anthropic 官方 docx / pptx / xlsx / pdf 四件套 |
| `obra/superpowers` | ~296k | 工程方法论元技能（偏重，适合常写代码的人） |
| `ui-ux-pro-max-skill` | ~133k | UI / 设计 |
| `ppt-master` | ~61k | 从零生成整套设计 PPT |
| `cloudflare/security-audit-skill` | ~28k | 安全审查 |
| `MathModeling-skills` | ~1.06k | 数模分阶段流程 |

**默认不装** —— 技能和 MCP 一样，不是越多越好。想要更强的能力时，让 AI 帮你装（它会先告诉你许可证风险）：

```
帮我加上 anthropics-skills
```

如果你想自己动手：

```bash
python3 scripts/apply.py --packs research --with-community anthropics-skills
python3 scripts/apply.py --packs code --with-community all
```

> ⚠️ 这些都是第三方仓库，**许可证各不相同**（有 MIT，也有再分发受限的）。清单里的 `license_risk` 字段标了风险，安装时会提示。

## 依赖分档（重要）

技能要跑得动，得有关键工具。这套东西按体积分了三档，**默认只装轻量的**：

| 档 | 例子 | 体积 | 策略 |
|---|---|---|---|
| `light` | pandoc · poppler · markitdown · tectonic · scipy | 几十 MB | 默认自动装 |
| `medium` | pdf2zh（含翻译模型）· scikit-learn | 100MB–1GB | 需 `--tier medium` |
| `heavy` | LibreOffice（≈700MB） | >1GB | **永不自动装**，只检测 + 给引导 |

### 「装了却用不了」的解药

很多东西**装上了但不在 PATH**，命令调不到 —— 这是这套配置最常见的失败模式。例如：

- LibreOffice 在 macOS 上位于 `/Applications/LibreOffice.app/Contents/MacOS/soffice`，根本不在 PATH
- pandoc 官方单文件安装器不写 PATH
- TinyTeX 装完把链接丢到 `/usr/local/bin`，那个目录常常不在 PATH

所以本套件会自动检测这些**已知位置**，命中就建一个转发脚本（shim）修好，并且自检会**真的执行一遍**来确认可用 —— 不是只看文件在不在。

### 还做了两件事减少对大件的依赖

1. **PDF 处理优先用 `PyMuPDF`**（纯 pip，免 sudo，无需装 poppler 二进制），只有真需要 poppler 命令行时才装它
2. **LaTeX 编译优先用 `tectonic`**（单个二进制约 50MB，按需下载宏包），而不是 TinyTeX / MacTeX（超过 1GB）

## 国内网络（这块决定安装成败）

直连 GitHub Releases 经常掉到 **30 KB/s**，几百 MB 的东西直接卡死。本套件内置了多路加速：

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

- **装什么、装成什么样，是完全确定的** —— 技能文件逐字节一致，你机器上的结果和别人的一样
- **装之前会先给你看清单**，你确认才动手
- **可查看、可卸载**：`scripts/apply.py --dry-run` 预演，`uninstall.md` 给卸载指引
- 全程**不碰系统级配置**，不写入需要管理员权限的目录
- ⚠️ **不绕付费墙**：不提供 CNKI 等收费库的绕过访问，只做合规检索

## 已知边界（做不到的事）

| 做不到 | 原因 | 替代方案 |
|---|---|---|
| 安装 MATLAB | 商业授权 + 数十 GB | 检测到就用；没有则降级用 Octave 跑 `.m` 兼容语法 |
| 静默装 C++ 编译器 | macOS 装 Xcode CLT 会弹系统确认框 | 引导你点确认 |
| 驱动正在运行的 Word 窗口 | 需要客户端联动 | 只做文件级读写（.docx/.xlsx/.pptx） |
| 代写作业 | 学术诚信 | 「做题能力」= 讲解 + 步骤引导 + 校验，不给答案 |

## 目录结构

```
agent-starter-kit/
├── README.md             ← 你正在看的（给人看）
├── AGENTS.md             ← 给 AI 看：行为约束与入口（agent 会自动读这个文件）
├── INSTALL.md            ← 给 AI 看：执行手册（六个 Step）
├── uninstall.md          ← 给 AI 看：卸载指引
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

## 给想改代码的人

- 改 `packs/*.json` 前先读 [packs/SCHEMA.md](packs/SCHEMA.md) —— 字段名写错会被**静默忽略**
- 新增技能：目录名必须与 `SKILL.md` 里 frontmatter 的 `name` 完全一致
- 新增宿主：只改 `hosts.json`，不用动脚本
- 自测务必**用假 HOME**，不要拿真实配置试：
  ```bash
  HOME=/tmp/test-home python3 scripts/apply.py --packs code --dry-run
  HOME=/tmp/test-home python3 scripts/doctor.py
  ```

更多约定见 [AGENTS.md](AGENTS.md) 第五节。