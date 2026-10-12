# 更新日志（Changelog）

本文件记录 **agent-starter-kit** 的所有重要变更。

格式遵循 [Keep a Changelog 1.1.0](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循[语义化版本 SemVer](https://semver.org/lang/zh-CN/)。

## 为什么这个项目需要一份 CHANGELOG

这个项目有点特别：**它会直接在用户的机器上执行安装**（装技能、注册 MCP、装依赖、写配置）。

- 大多数用户是让 AI **从 `main` 克隆**一次就装上，而 `main` **随时会更新** —— 也就是说，两次安装之间，它"会做什么"可能已经变了。
- 因此需要一份可对照的变更记录，让用户能回答：**「我这个版本，到底会在我机器上做什么？」**

配套建议：想拿到稳定、可复现的行为，请**锁定版本**而不是一直追 `main`：

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/tyiiiyt01/agent-starter-kit
```

这样你就能用下面 `[0.1.0]` 这一节的记录，对照你手上那一版的实际行为。

---

## [Unreleased]

### Added

- **`ppt-master` 与 `anthropics-skills` 改为默认安装** —— 补的是基础能力的两个短板：前者做设计级 PPT（`python-pptx` 只能摆结构），后者是官方文档四件套，处理复杂 Word 修订/批注/目录与设计级 PPTX 更可靠。不想要可加 `--no-community-defaults`
  - ⚠️ 实测 `ppt-master` 技能目录约 **78 MB**（社区资料里常写 18M，偏小），默认装意味着一次较大的克隆
- `apply.py --no-community-defaults`：关掉默认社区技能
- `doctor.py` 新增社区技能校验：按账本逐条复核，能抓出"装完被删""克隆不完整""SKILL.md 缺失"（此前只管能力包自带的技能，社区技能装失败不会报）
- README 重写介绍部分：用人话解释「技能 / MCP / 依赖」三个术语，新增「它到底做了什么」（具体人类场景 + 诚实边界）与「它不做什么」，合并原先重复的边界说明
- `skills/office-docs` 扩充到 197 行，补入实测配方与踩坑：`rPr` 为 `None` 导致的崩溃、`w:eastAsia` 字体槽位、三线表 XML、A4 页面设置、Excel 条件格式/图表、能力边界表

### Fixed

- `skills/office-docs` 两处照抄即报错的示例：`PPt` 应为 `Pt`；`doc.add_run().add_picture(...)` 应为 `doc.add_paragraph().add_run().add_picture(...)`

---

## [0.1.0] - 2026-10-12

首个发布。面向大学生与办公人群，把 Claude Code / Cursor / Trae / Trae CN / Reasonix / Codex 等 AI 助手**一次配置到位**。

### Added

**能力包与技能**

- 八个能力包：`code`、`research`、`math-modeling`、`writing`、`office`、`office-work`、`study`、`design`（定义见 `packs/*.json`）
- 十七个技能文件（`skills/` 下，逐字节一致、内容不可改）
- Office 能力全部用纯 Python 库实现（python-docx / openpyxl / python-pptx / pypdf / docxtpl），不依赖 Office 客户端，也不装第三方 Office MCP

**宿主适配（`hosts.json`）**

- 收录 6 个宿主：Claude Code（已核实）、Cursor（已核实）、Trae 国际版（已核实）、Trae CN（部分核实）、Reasonix（部分核实）、Codex CLI（未核实）
- 未核实的宿主不静默写入：安装前会让用户确认真实路径，装完由自检复核
- 新增宿主只需改 `hosts.json`，不用动脚本

**安装引擎（`scripts/`）**

- `detect.py` —— 环境探测（只读）
- `apply.py` —— 幂等安装，支持 `--dry-run` / `--tier` / `--minimal-mcp` / `--with-community` / `--gh-proxy` 等开关
- `doctor.py` —— 逐项自检，**真的执行一遍**来验证工具可用，而不是只看文件在不在
- 写 JSON 配置时为**增量合并**，保留用户自己配置的 MCP server
- 全程**幂等、可回滚**：装了什么记录在 `~/.agent-starter-kit/state.json`，供卸载使用
- `strategy=cli` 的宿主（Claude Code）走宿主命令行写入，不手写覆盖 `~/.claude.json`

**场景预设（`presets.json`）**

- 8 个预设 + 默认值：用户说"我要写毕业论文"即可自动匹配到对应能力包，无需自选包名；匹配不上时默认只装 `code`（最小可用）

**依赖分档与 PATH 修复**

- 依赖按体积分三档：`light`（默认装）、`medium`（需 `--tier medium`）、`heavy`（永不自动装，只检测 + 引导）
- 自动检测工具的已知安装位置，命中就建转发脚本（shim）修复"装了却不在 PATH"的问题

**国内网络加速**

- `apply.py` 内置 GitHub 多路回退（直连 → gh-proxy → ghfast → ghproxy → gitmirror）
- 安装后生成 `~/.agent-starter-kit/mirrors.env`，含 `PIP_INDEX_URL`、`HF_ENDPOINT`、`NPM_CONFIG_REGISTRY`、`PYTHONUTF8`

**社区技能与模板**

- `community-skills.json` —— 社区高星技能**索引**（含 star 量级、许可证、`license_risk`），默认不装，需 `--with-community` 显式启用
- `templates/` —— `AGENTS.md.template`（给自己的项目用的说明模板）与 `claude-settings.json.template`（权限白名单模板）
- `uninstall.md` —— 卸载指引，只删账本里记录过的条目，不碰用户自己配置的内容
- `packs/SCHEMA.md` —— 能力包定义的格式说明

**文档**

- 文档按读者拆成三份：`README.md`（面向人）· `AGENTS.md`（助手的行为约束）· `INSTALL.md`（助手的执行手册，Step 0–6）

<!--
下一个版本请在此处新增一节，例如：

## [0.2.0] - YYYY-MM-DD

### Added
### Changed
### Fixed
### Removed

并在文件末尾更新链接。
-->

[Unreleased]: https://github.com/tyiiiyt01/agent-starter-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/tyiiiyt01/agent-starter-kit/releases/tag/v0.1.0