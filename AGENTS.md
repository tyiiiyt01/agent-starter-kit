# AGENTS.md

本文件面向 **AI agent**。人类读者请看 [README.md](README.md)。

---

## 一、如果用户把本仓库地址发给了你

说明他希望你**在他的机器上**完成安装。你是执行者，不是读者。

### 执行顺序

1. **取回仓库到临时目录**
   - 有 git：`git clone --depth 1 https://github.com/tyiiiyt01/agent-starter-kit`（macOS/Linux 用 `/tmp/agent-starter-kit`，Windows 用 `%TEMP%\agent-starter-kit`）
   - 国内直连慢就加加速前缀：`git clone --depth 1 https://gh-proxy.com/https://github.com/tyiiiyt01/agent-starter-kit`
   - 没有 git：用网页抓取逐个取回文件，至少要有 `INSTALL.md`、`hosts.json`、`presets.json`、`scripts/` 全部内容
     - raw 地址示例：`https://raw.githubusercontent.com/tyiiiyt01/agent-starter-kit/main/INSTALL.md`
   - **缺文件就如实告诉用户**，不要凭印象拼凑

2. **完整阅读 [`INSTALL.md`](INSTALL.md)** —— 那是执行手册（Step 0–6）。本文件只给约束，不给步骤。

3. **严格按 `INSTALL.md` 的分支逻辑走。**

4. **做完别急着结束** —— `INSTALL.md` 的 Step 6 是给用户项目配 `AGENTS.md`，这是新手最该配、也最容易被漏的一步。要主动问用户一句。

## 二、你被允许自行判断的（"怎么做"）

- 探测宿主真实路径，包括 `hosts.json` 里没收录的宿主 —— 照同类推一个出来，推完让用户确认一次
- 选择合适的包管理器和安装方式
- 补装缺失的前置依赖
- 按操作系统差异调整命令
- 从 `presets.json` 的 `trigger` 匹配用户原话，决定装哪些包

## 三、你必须遵守的（"做什么"和"算不算成功"锁死）

- ❌ 静默修改任何系统级配置
- ❌ 写入需要管理员 / root 权限的目录（一律装到用户目录）
- ❌ 在用户明确回复确认之前执行任何安装动作
- ❌ 改动 `skills/` 里技能文件的**内容** —— 必须与原文件逐字节一致，否则你的安装和别人的不一样，出问题无法复现
- ❌ 跳过最后的 `doctor.py` 验证
- ❌ 主动给用户加装 MCP。MCP 极吃上下文（实测 3 个就能占掉 200k 上下文的 72%），装多了 agent 会变笨
- ❌ 承诺做不到的事（装 MATLAB、绕付费墙、驱动正在运行的 Word 窗口、代写作业）
- ❌ **绕过 `apply.py` 的两个安全守卫**。它们会以退出码 3 / 4 中止：
  - **退出码 3** = 宿主路径未经核实。必须问用户真实路径，然后带 `--skill-dir`（技能）或 `--force-unverified`（MCP）重跑
  - **退出码 4** = 工作区制宿主有多个候选技能目录（如 Reasonix 的多个工作区）。必须问用户当前用哪个，然后 `--skill-dir` 指定
  - 这两个守卫存在的原因是「装到哪个位置」不可逆，**不能只靠你自觉**。停下来问一句是正确行为，不是故障

## 四、两种特殊情况的处理

| 情况 | 怎么做 |
|---|---|
| **环境探测发现 Python 缺失** | 停下来，把 `INSTALL.md` 的「Step 0 前置检查」给用户看，等装好再继续。**Python 是唯一硬前置** |
| **用户在国内网络下卡住** | 跳到 `INSTALL.md` 的「附：国内网络加速」—— 那里有 GitHub 多路回退和 `mirrors.env` 的用法 |
| **大件依赖下载超时** | **直接放弃这一项，不要死等**。跳过并在报告里给装法和替代方案 |

---

## 五、如果你是在这个仓库里工作（贡献者场景）

- 改 `packs/*.json` 前先读 [`packs/SCHEMA.md`](packs/SCHEMA.md) —— 字段名写错会被**静默忽略**
- 新增技能：目录名必须与 `SKILL.md` 里 frontmatter 的 `name` **完全一致**（`doctor.py` 会校验）
- 新增宿主：只改 [`hosts.json`](hosts.json)，不要改脚本
- 改完必须自测：
  ```bash
  python3 -c "import ast,json,glob; [ast.parse(open(f,encoding='utf-8').read()) for f in glob.glob('scripts/*.py')]; [json.load(open(f,encoding='utf-8')) for f in ['hosts.json','presets.json','community-skills.json']+glob.glob('packs/*.json')]"
  HOME=/tmp/test-home python3 scripts/apply.py --packs code --dry-run
  HOME=/tmp/test-home python3 scripts/doctor.py
  ```
  ⚠️ **用假 HOME 测试**，不要拿真实用户配置试
- 本项目所有脚本只用 Python，**不提供 `.sh`** —— 这是跨平台第一原则（Windows 上 `.sh` 跑不了）
- 所有文件写入一律显式 UTF-8 无 BOM（Windows 默认 GBK 会导致中文乱码与 JSON 解析失败）