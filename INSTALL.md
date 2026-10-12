# INSTALL.md —— AI 执行手册

> **这份文件是给 AI 执行者看的，不是给人看的。**
> 人类读者请回到 [README.md](README.md)。
>
> **约束在 [AGENTS.md](AGENTS.md)，步骤在这里。** 先读那份确认你不能做什么，再按本文执行。
>
> 你的任务：在这台机器上完成安装。**按顺序执行，每个决策点都不要跳。**
> 核心原则：**「做什么」和「算不算成功」完全确定；「怎么做」你可以现场适配。**

---

## Step 0 — 前置检查（不可跳过）

**先确认 Python 3 可用。** 这是唯一的硬前置，因为后面所有脚本都是 Python。

```bash
python3 -V      # macOS / Linux
py -3 -V        # Windows 优先试这个
python -V       # Windows 次选
```

### Windows 专属陷阱

如果在 Windows 上运行 `python` **没有报错、也没有输出版本号，而是弹出微软商店** ——
那是占位程序（stub），**不是真实 Python**。判据：`where python` 的路径里含 `WindowsApps`。

遇到这种情况，停下来，把下面这段给用户：

> 你这台电脑还没有真正的 Python。装一个就行，两种方式任选：
> - 打开 PowerShell，运行：`winget install Python.Python.3.12`
> - 或者去 https://www.python.org/downloads/ 下载，**安装时务必勾选 "Add python.exe to PATH"**
>
> 装完告诉我一声，我继续。

### macOS 专属

`python3` 由 Xcode Command Line Tools 提供。如果运行报错或弹出安装框：

> 运行 `xcode-select --install`，在弹出的窗口点「安装」，装完告诉我。

**Python 就绪前不要往下走。** 其余依赖（git / node / uv / 编译器）缺失都**不阻断**安装，只在最后报告里说明。

---

## Step 1 — 探测环境

**顺便把安装器自己的依赖装上**（很小，只有一个包，但装上才体验完整）：

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple   # 国内
```

不装也能跑 —— 只是 Reasonix / Codex 这类 **TOML 宿主**的 MCP 会降级成「给你一段配置让你手动粘贴」。
如果你的 `hosts.found` 里有这两个宿主，建议装上。

然后探测：

```bash
python3 scripts/detect.py --json
```

读它的 JSON 输出，重点关注：

| 字段 | 用途 |
|---|---|
| `os` | `darwin` / `windows` / `linux`，决定后面命令分支 |
| `hosts.found` | **已装的宿主**，这是你要投放技能的目标 |
| `hosts.found[*].verified` | `true` 可直接用；`false` 或 `"partial"` **必须先让用户确认路径** |
| `hosts.found[*].skills_dir_exists` | `false` 表示目录还不存在，需要创建（正常） |
| `hosts.found[*].mcp_file_exists` | `false` 表示该宿主还没配过 MCP，需要新建（正常） |
| `toolchain` | `node` / `git` / `uv` / `clang++` / `g++` / `cl` / `matlab` / `octave` |
| `skills_candidates` | **只在工作区制宿主出现**。候选技能目录列表，见下 |
| `skills_ambiguous` | `true` 表示有多个候选，**必须让用户选**，不许自己猜 |
| `mcp_shape` | `array` 表示该宿主的 MCP 配置是数组表（如 Reasonix 的 `[[plugins]]`） |

### 工作区制宿主（如 Reasonix）：必须先问用户

某些宿主的技能目录**在工作区内部**，而工作区名不固定 —— 例如 Reasonix 是 `~/.reasonix/<工作区>/.reasonix/skills/`。

`detect.py` 会把这些候选全列在 `skills_candidates` 里。**如果 `skills_ambiguous` 为 `true`：**

1. **不要按修改时间猜**（脚本也被设计成不会猜 —— 它会直接中止）
2. 问用户：
   > 你有 N 个 Reasonix 工作区：A、B、C。技能要装进**当前在用的**那个 —— 是哪个？
3. 拿到答案后，用 `--skill-dir <该工作区的 .reasonix/skills 路径>` 指定

> 为什么不让脚本自动挑？挑错了用户在自己工作区里根本看不到技能，而脚本还以为装成功了。宁可停下来问一句。

**`hosts.found` 为空怎么办？** 一个宿主都没检出。不要直接失败 —— 依次问用户：

> 没自动找到你的 AI 助手。你用的是哪一个？
> Claude Code / Cursor / Trae / Trae CN / Reasonix / Codex / 其他（请说名字）

用户给出名字后，去 `hosts.json` 找对应的 `skills` 与 `mcp.file`。**找不到的宿主**，按这套逻辑现场推：

1. 搜同族宿主：Trae CN 之于 Trae、国内版之于国际版，通常只差目录名后缀（`-cn` / ` CN`）
2. 用关键词在用户目录下搜：`find ~ -maxdepth 3 -iname "*<宿主名>*" -type d`
3. 问用户一步操作就能读到真实路径 —— 多数宿主在「设置 → MCP」里有「打开配置文件」按钮
4. **推出来的路径写进去之前，必须让用户确认一次**

### 未核实路径的处理（重要）

对 `verified` 不是 `true` 的宿主，**禁止静默写入**。这样问：

> 我需要确认一下 **<宿主名>** 的技能目录和 MCP 配置路径。
> 请打开 <宿主名> 的 <confirm_hint 里的操作>，把显示的路径发我。
> 如果你不确定，我先按推测路径 `<推测路径>` 来装，装完自检会验证对不对 —— 要这样吗？

---

## Step 2 — 定能力包（用场景预设，别让用户挑包名）

**先读 `presets.json`**，它是"用户说一句话 → 该装哪些包"的映射表。

做法：拿用户的**原话**去匹配 `presets.*.trigger` 里的说法，命中就用对应的 `packs`。

| 用户说 | 装 | 依据 |
|---|---|---|
| 毕业论文 / 写论文 / 文献综述 / 开题 | `research` `writing` | presets.thesis |
| 数学建模 / 数模 / 国赛 / 美赛 | `math-modeling` `code` `writing` | presets.math-modeling |
| 上专业课 / 复习 / 考试 / 做题 / 考研 | `study` `code` | presets.coursework |
| 上班 / 办公 / 报表 / 会议 / 周报 | `office` `office-work` | presets.office |
| 科研 / 发论文 / 投期刊 / 做实验 | `research` `writing` `math-modeling` | presets.research |
| C++ / 编程 / 实验报告 / 课程设计 | `code` `study` `writing` | presets.engineering |
| 都要 / 全套 | 八个全装 | presets.all |

**规则：**

- **匹配不上就装 `code`**（`presets.default`），并告诉用户「以后想加随时说」
- 用户说"帮我装好"但没说用途时，**问一句「你主要用来做什么？」比装全套更合适** —— 全套装得慢、依赖也更容易失败
- 用户点名要某个包时，**以用户说的为准**，覆盖预设建议
- ⚠️ **不要自作主张装全部**。包越多失败面越大，安装时间越长

### 依赖档位怎么定

| 档 | 内容 | 什么时候加 `--tier medium` |
|---|---|---|
| `light`（默认） | pandoc · poppler · markitdown · tectonic · numpy/pandas 等 | 不用管，默认就装 |
| `medium` | scikit-learn · scipy · pdf2zh 等 | 数模/统计/翻译类需求可以加 |
| `heavy` | LibreOffice（≈700MB） | **永远不加**，靠检测 + 引导 |

判断原则：**用户需要跑建模/统计/翻译 → 可以 `--tier medium`；只是想读写文档 → 保持默认**。
LibreOffice 这类重装项，检测到就用，没有就给引导，**不要让用户在下载上卡半小时**。

### MCP 要克制 —— 这是新手第一坑

调研里的硬数据：**3 个 MCP 就能吃掉 200k 上下文里的 143k tokens（72%）**，7 个 MCP 首轮就烧 67,300 tokens。**MCP 装多了 agent 会变笨。**

所以：

- **默认不要加 `--minimal-mcp`**（默认就是装的完整集合，每个包已经控制得很克制）
- 但**如果用户抱怨"反应变慢""记不住前面说的"**，就是上下文被吃掉了 —— 这时用：
  ```bash
  python3 scripts/apply.py --packs <包> --minimal-mcp
  ```
  它只装每个包标记为 `essential` 的那一个 MCP
- ⚠️ 反过来，**不要主动给用户加装 MCP**。用户说"能不能再强一点"时，先问具体想做什么，再判断是否真需要新 MCP

### 社区高星技能

`community-skills.json` 里有一份社区高星技能清单（带 star 数、许可证和坑的说明）。

**其中两个是默认装的**（在清单里标了 `default: true`）：

| 默认装的 | 为什么默认 |
|---|---|
| `anthropics-skills` | Anthropic 官方四件套（docx/pptx/xlsx/pdf）。补的是**复杂文档**能力 —— Word 修订/批注/目录、设计级 PPTX，比自写的 `office-docs` 更可靠 |
| `ppt-master` | 补的是**设计**能力。`python-pptx` 只能摆结构，做不出设计；要"精美 PPT"得靠它 |

**其余的默认不装** —— 技能也不是越多越好。用户主动说"我听说有个 xx skill"或想要更强能力时：

```bash
python3 scripts/apply.py --packs <包> --with-community all              # 全部 13 个
python3 scripts/apply.py --packs <包> --with-community superpowers      # 点名加装
python3 scripts/apply.py --packs <包> --no-community-defaults           # 连默认那两个也不要
```

⚠️ 装之前**把许可证风险念给用户听**（清单里有 `license_risk` 字段，AGPL 之类的再分发受限，要说明）。

⚠️ 默认装的两个需要**从 GitHub 克隆**（`ppt-master` 仓库较大）。国内网络下会走 `--gh-proxy auto` 的多路回退；如果全部镜像都不通，`apply.py` 会如实报告失败并继续装其他东西，**不会卡住整个流程**。用户不想要这个下载也可以加 `--no-community-defaults`。

---

## Step 3 — 打印清单，等用户确认 ⛔ 硬门槛

先跑预演，拿到确定性清单：

```bash
python3 scripts/apply.py --packs <选定的包> --dry-run          # 常规
python3 scripts/apply.py --packs <选定的包> --tier medium --dry-run   # 需要建模/统计/翻译时
```

预演会分四块列出：**技能文件 · MCP 配置 · Python 依赖 · 命令行工具**。把结果**原样呈现给用户**：

```
即将执行以下操作：

【技能文件】投放到 <skills_dir>
  + thesis-format
  + academic-figures

【MCP 配置】写入 <mcp_file>
  + arxiv           检索 arXiv 上的论文预印本

【Python 依赖】装到 <python 路径>
  + SciencePlots    学术图表样式
  + uncertainties   误差传递

【命令行工具】
  ✓ pandoc          已在 PATH，无需处理
  + tectonic        LaTeX 编译（约 50MB）
  · soffice         不装（heavy 档）—— 检测到就用，没有则给引导

【需要你自己动手的】
  ! ...

不会做任何系统级修改，不需要管理员权限。
回答「确认」我就开始装。
```

**然后停下来，等用户明确回复。** 用户说「确认 / 好 / 装吧 / OK / yes」都算。
用户没回复、或回复的是别的内容 —— **不要装**，先回应他的问题。

⚠️ 如果清单里出现 `·` 开头的「不装」项（medium / heavy 档），**要跟用户说一句**：「这几项体积较大默认不装，需要的话告诉我」。不要让他以为全装上了。

---

## Step 4 — 执行安装

用户确认后：

```bash
python3 scripts/apply.py --packs <选定的包>                       # 常规
python3 scripts/apply.py --packs <选定的包> --tier medium          # 需要建模/统计/翻译时
python3 scripts/apply.py --packs <选定的包> --no-cli --no-python-deps   # 只投技能和 MCP，不碰依赖
python3 scripts/apply.py --packs <选定的包> --skill-dir <路径>     # 工作区制宿主必须指定（见 Step 1）
python3 scripts/apply.py --packs <选定的包> --force-unverified     # 用户确认过未核实宿主的路径后
```

### ⛔ 两个脚本会主动拦住你 —— 这是设计，不是故障

| 退出码 | 触发条件 | 你要做什么 |
|---|---|---|
| `3` | 目标宿主 `verified` 不是 `true`，且你没给 `--skill-dir` 或 `--force-unverified` | **停下问用户真实路径**，拿到答案后带上对应参数重跑。**不要绕过它** |
| `4` | 工作区制宿主有多个候选技能目录 | 问用户当前用哪个工作区，然后用 `--skill-dir` 指定 |

这两个守卫的存在理由是：**"装到哪个位置"是不可逆操作，不能只靠 agent 自觉。** 以前只写在文档里，现在由脚本强制。

> 用户只想看看会做什么？加 `--dry-run` —— 它不写任何东西，所以不会被这两个守卫拦住。

特性说明（你不用实现，脚本已保证）：

- **幂等**：重复运行不报错、不重复装、不覆盖用户已有配置
- **增量**：写 JSON 时是**合并**，不是覆盖 —— 用户自己配的 MCP server 会被保留
- **可回滚**：装了什么记在 `state.json`，供卸载使用
- **CLI 优先**：`strategy=cli` 的宿主（Claude Code）走命令行写入，**绝不手写覆盖 `~/.claude.json`**
- **失败不中断**：单个依赖或 MCP 失败不会导致整体退出，会记入报告
- **PATH shim**：装了但不在 PATH 的工具会自动建转发脚本修好

### 关于 PATH shim

安装输出里如果出现 `已建 shim`，说明那个工具**本来就装了、只是 PATH 里没有** —— 这是零成本修复，不是新下载。

⚠️ **shim 目录必须进 PATH 才生效。** 如果 shim 目录（`~/.agent-starter-kit/bin`）不在用户的 PATH 里，要告诉用户加一行：

- macOS / Linux：在 `~/.zshrc` 或 `~/.bashrc` 末尾加
  `export PATH="$HOME/.agent-starter-kit/bin:$PATH"`
- Windows：把 `%USERPROFILE%\.agent-starter-kit\bin` 加入用户环境变量 `Path`

自检会复核这一条，shim 不生效时报出来。

如果脚本报出**权限错误**：说明试图写入不该写的目录。停下来告诉用户，不要自己去提权。

---

## Step 5 — 验证（不可跳过）

```bash
python3 scripts/doctor.py
```

逐项复核并给用户一份结论。**报告格式：**

```
安装完成 —— 自检结果

✅ Python 环境            Python 3.13.5
✅ git                    git 2.54.0
✅ node                   v22.14.0
✅ 技能投放（1 个宿主）     thesis-format / academic-figures 等 3 个全部就位
✅ MCP: arxiv             已注册

Python 依赖
✅ pandas                 import pandas 正常
✅ SciencePlots           import scienceplots 正常

命令行工具（已验证能真的执行）
✅ pandoc                 pandoc 3.1.11
⚠️ tectonic (light)       未安装。装法: brew install tectonic｜替代: 用 pandoc + 已有 LaTeX 或输出 docx
✅ soffice (未在 PATH)    已安装但调不到 → 已建 shim 修复

⚠️ shim 目录不在 PATH      ~/.agent-starter-kit/bin 不在 PATH 里，1 个 shim 不生效。
                          需加一行：export PATH="$HOME/.agent-starter-kit/bin:$PATH"

现在你可以直接用了。试试说：「帮我读这篇 PDF 并总结」
```

**自检不通过的项目，必须明说，不要含糊过去。** 判定标准：

| 情况 | 算不算失败 |
|---|---|
| `Python` 失败 | ❌ 整体失败，必须先解决 |
| 技能投放全部失败 | ❌ 整体失败（宿主路径不对） |
| MCP 失败 | ⚠️ 单项失败，报告并给重试命令 |
| Python 包 / CLI 工具缺失 | ⚠️ 降级，**不影响基本使用** —— 但要把「替代方案」一起告诉用户 |
| shim 目录不在 PATH | ⚠️ 给一行命令让用户加 |

⚠️ **每个缺失的工具都有 fallback**（`packs/*.json` 的 `fallback` 字段写着）。缺工具时说"这个能力用不了"是错的 —— 要说"这个能力会走替代方案"。doctor 的输出里已经带了替代方案，照它念。

---

## Step 6 — 配置用户的项目（新手最该配、但最容易被漏的一步）

装完技能只是"有了工具"。调研显示：**新手配置 AI agent 时共识度最高的必配项，是一个项目说明文件**（`AGENTS.md` / `CLAUDE.md`）。Claude Code、Cursor、Trae 官方都认这个文件名，`agents.md` 官方站称已有 6 万多个项目采用。

**做完 Step 5 后，主动问用户一句：**

> 还有一件事建议做 —— 给你的项目写一个 `AGENTS.md`，
> 告诉 AI 这个项目是干什么的、有哪些约定。这样它每次都不用你重复交代。
> 要我现在帮你生成吗？

用户同意后：

1. 读 `templates/AGENTS.md.template`（60 行以内的结构模板）
2. **探测用户当前目录**：技术栈、目录结构、构建/测试命令、已有约定
3. 生成定制化的 `AGENTS.md` 写到项目根目录
4. ⚠️ **不要写长**。主流建议 60–100 行，上限别超 200 行。新手最常犯的错就是写得又长又空

### 顺带配权限白名单（Claude Code 用户）

如果宿主是 Claude Code，读 `templates/claude-settings.json.template`，帮用户生成 `.claude/settings.json`：

- `permissions.allow` 里放安全的高频命令（`git status`、`git diff`、跑测试等）
- `permissions.deny` 里**必须屏蔽密钥文件**（`Read(./.env)`、`Read(./.env.*)`）
- 关键规则：**deny 优先级高于 allow**

> ⚠️ **不要建议用户用 `--dangerously-skip-permissions`。** 官方推荐的做法就是白名单，跳过全部权限是新手误删文件的头号原因。

`templates/README.md` 里说明了这两个模板的用法，以及为什么 statusline / hooks 属于进阶项。

---

## 附：国内网络加速（这块决定安装成败）

国内直连 GitHub Releases 经常掉到 **30 KB/s**，几百 MB 的东西能卡到超时。`apply.py` 已经内置了加速能力，你要做的是**告诉用户这些开关存在**。

### GitHub 加速

```bash
# 自动多路回退（直连 → gh-proxy → ghfast → ghproxy → gitmirror）
python3 scripts/apply.py --packs <包> --gh-proxy auto     # 默认就是 auto

# 指定单个镜像
python3 scripts/apply.py --packs <包> --gh-proxy https://gh-proxy.com/
```

手动下载时用这个套路（`-C -` 断点续传，`--retry` 自动重试）：

```bash
curl -L -C - --retry 10 --retry-delay 3 -o file.zip \
  https://gh-proxy.com/https://github.com/owner/repo/releases/download/v1.0/file.zip
```

> ⚠️ 公益镜像有掉线、限速、注入广告的风险，**不要用于私有仓库**。镜像失效很快，所以脚本内置了多路回退 —— 别硬编码单一镜像。

### 其他镜像（`apply.py` 会自动生成配置文件）

安装完成后会写出 `~/.agent-starter-kit/mirrors.env`：

```bash
source ~/.agent-starter-kit/mirrors.env
```

里面是这四个：

| 变量 | 值 | 为什么需要 |
|---|---|---|
| `PIP_INDEX_URL` / `UV_DEFAULT_INDEX` | 清华 PyPI 镜像 | pip 直连国内很慢 |
| `HF_ENDPOINT` | `https://hf-mirror.com` | **最关键** —— pdf2zh / faster-whisper / docling 首次运行要下模型，不配这个在国内基本下不动 |
| `NPM_CONFIG_REGISTRY` | `https://registry.npmmirror.com` | npm 同理 |
| `PYTHONUTF8` | `1` | 避免 Windows 上中文编码问题 |

---

## 附：平台专属坑（照着检查，别想当然）

### macOS

| 坑 | 现象 | 对策 |
|---|---|---|
| **`unzip` 破坏签名** | 手动装 .app 后报「已损坏，无法打开」 | 用 **`ditto -x -k xxx.zip 目标目录`**，别用 `unzip` |
| **App Translocation** | app 放在 `~/Downloads` 且带 quarantine 时，会从只读随机路径运行，无法自更新 | 放到 `/Applications`（或用户可写的固定目录）并 `xattr -dr com.apple.quarantine <路径>` |
| **架构选错** | M 系列机器装了 x86 二进制，直接崩 | 认准 `arm64` 版本；旧 Intel 机器才用 `x86_64` |
| **系统 Python 不能装包** | `/usr/bin/python3` 是 Xcode CLT 自带的 | 用 venv 或 `pip install --user`，别往系统 Python 装 |
| **soffice 报 User installation 错误** | 默认要写 `~/Library/Application Support/LibreOffice` | 必须加 `-env:UserInstallation=file:///tmp/lo_profile` |

### Windows

| 坑 | 现象 | 对策 |
|---|---|---|
| **微软商店 stub** | 敲 `python` 打开商店，不报错也不执行 | 关掉「应用执行别名」，或去 python.org 装并勾选 Add to PATH |
| **PATH 改完不生效** | 新装的工具当前终端找不到 | 要**重开终端**（或重开宿主程序） |
| **长路径 260 限制** | 深层 node_modules 报错 | `git config --global core.longpaths true` + 打开系统长路径支持 |
| **PowerShell 执行策略** | `.ps1` 被拦 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| **Defender 误杀** | 刚下载的工具被隔离 | 加排除项；别关整个 Defender |
| **GBK 编码** | 中文乱码、JSON 解析失败 | 设 `PYTHONUTF8=1`（mirrors.env 里已有） |

### 两个平台共有

权限、UTF-8 编码、CRLF/LF 换行符。

---

## 平台差异对照（照着走，别想当然）

| 事项 | Windows | macOS |
|---|---|---|
| Python 命令 | `py -3` 优先，其次 `python` | `python3` |
| 路径展开 | `%USERPROFILE%` / `%APPDATA%` | `~` |
| 装技能的方式 | **复制**（`shutil.copytree`） | **复制**（不要 `ln -s`） |
| 符号链接 | 需管理员或开发者模式 → **禁用** | 可用，但为一致性也禁用 |
| 环境变量 | `setx` 或用户级环境 | shell rc 文件 |
| 文件编码 | **必须显式 `encoding="utf-8"`** | 同左（保持一致） |
| 换行符 | 无所谓，但别用 `.sh` | 同左 |
| Shell 脚本 | ❌ `.sh` 跑不了，`.ps1` 默认被策略拦 | ✅ 可用 |
| C++ 编译器 | `g++`(MinGW-w64) 或 `cl`(MSVC Build Tools) | `clang++`，靠 `xcode-select --install` |
| 安装位置 | 一律用户目录，**别碰 `C:\Program Files`** | 一律用户目录 |

> **结论：所有脚本只用 Python 写，不提供 `.sh`。** 这是跨平台的第一原则。

---

## 失败处理

| 症状 | 处理 |
|---|---|
| `python3: command not found` | 回 Step 0，走前置安装引导 |
| 弹出微软商店 | 命中 Windows stub 陷阱，回 Step 0 |
| 技能目录写不进去 | 报告给用户，**不要提权** |
| 某个 MCP 装不上（多为网络） | 记录下来继续装其他的，最后单独报告并给重试命令 |
| Python 包装失败 | 多为网络或镜像源问题。记下来，最后报告时给出该包的 `fallback` 方案；**不要反复重试** |
| CLI 工具下载卡住 / 超时 | **立刻放弃这一项，不要死等** —— 大件工具在国内网络下经常卡死。跳过它，报告里给出装法和替代方案 |
| shim 建了但命令还是调不到 | 说明 shim 目录不在 PATH，给 Step 4 的那行 export 命令 |
| 工具"装了但找不到" | 这正是 shim 要解决的问题。让用户跑一次 `apply.py`（幂等，不会重复装），会自动建 shim |
| 宿主路径推测错误 | 用 Step 1 的 `confirm_hint` 让用户读真实路径，改 `hosts.json` 后重跑 |
| 用户中途说「停」 | **立刻停止**，已装的部分保留，告诉他怎么卸载（见 `uninstall.md`） |

### 一条硬规矩：不要为了"装全"而死等

依赖的分档设计就是为了这个。**light 档失败就跳过，medium/heavy 根本不装。** 宁可报告"这一项没装上，替代方案是 X"，也不要让用户对着一个卡住的下载进度条等二十分钟 —— 那会让整个"一键配置"体验崩掉。

---

## 完成后告诉用户什么

三件事，别多：

1. **现在能用了** —— 给一句可直接复制的试用示例
2. **哪些没配好** —— 自检里 ❌ 和 ⚠️ 的项，附一句怎么解决
3. **想加能力随时说** —— 提示他可以说「我要写论文」来追加 `research` 包