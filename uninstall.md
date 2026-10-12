# uninstall.md —— 卸载指引（给 AI 执行）

> **这份文件是给 AI 执行者看的，不是给人看的。**
> 目标：把 agent-starter-kit **装过的**东西干净移除，且**只动它装过的**。
>
> 铁律：**只删 `state.json` 里记录过的条目。绝不碰用户自己配置的 MCP server、技能或任何其它文件。**

---

## 前置：先读账本

一切以账本为准，不要凭记忆猜：

```bash
python3 -c "import json,os;print(json.dumps(json.load(open(os.path.expanduser('~/.agent-starter-kit/state.json'))),ensure_ascii=False,indent=2))"
```

`state.json` 的结构（由 `scripts/apply.py` 写入）：

```json
{
  "skills": [ { "host": "claude-code", "skill": "python-workflow", "path": "/Users/x/.claude/skills/python-workflow" } ],
  "mcp":    [ { "host": "cursor", "server": "filesystem", "path": "/Users/x/.cursor/mcp.json" },
              { "host": "claude-code", "server": "arxiv", "via": "cli" } ],
  "hosts":  [ "claude-code", "cursor" ],
  "packs":  [ "code", "research" ],
  "pythonDeps": [ { "pip": "pandas", "import": "pandas", "why": "数据处理" } ],
  "cliDeps":    [ { "name": "pandoc", "bin": "pandoc", "method": "brew install pandoc", "why": "格式转换" } ],
  "shims":      [ { "name": "soffice", "bin": "soffice", "target": "/Applications/LibreOffice.app/Contents/MacOS/soffice", "shim": "/Users/x/.agent-starter-kit/bin/soffice" } ]
}
```

- `skills[*].path` → 要删的技能目录（**精确路径**）
- `mcp[*]` 有两种形态：
  - 有 `path` → 该 MCP 条目被合并写进了这个 JSON / TOML 文件
  - 有 `via: "cli"` → 该 MCP 条目是用宿主命令行注册的（如 Claude Code）
- `pythonDeps` / `cliDeps` → **本套件安装过的依赖。默认不卸**（见 Step 4）
- `shims[*]` → 本套件为「装了但不在 PATH」的工具建的转发脚本，可以安全删除

**账本不存在** → 说明本套件没装过东西。直接告诉用户「没有需要卸载的内容」，结束，**不要做任何删除**。

---

## Step 1 — 打印卸载清单，等用户确认 ⛔ 硬门槛

```
即将卸载以下内容（仅限本套件装过的）：

【技能目录】将删除
  - /Users/x/.claude/skills/python-workflow
  - /Users/x/.claude/skills/cpp-workflow

【MCP 条目】将移除
  - cursor / filesystem        （从 ~/.cursor/mcp.json 里删掉这一个条目）
  - claude-code / arxiv        （claude mcp remove arxiv）

【不会动】
  - 你自己配置的其它 MCP server
  - 你的 API Key、账号、其它技能和配置

回答「确认」我就开始卸载。
```

**停下来等用户明确回复。没确认不动手。**

---

## Step 2 — 删技能目录

只删账本里 `skills[*].path` 列出的目录：

```bash
python3 - <<'PY'
import json, os, shutil
state = json.load(open(os.path.expanduser("~/.agent-starter-kit/state.json")))
for item in state.get("skills", []):
    p = item["path"]
    if os.path.isdir(p):
        shutil.rmtree(p)
        print("已删除", p)
    else:
        print("跳过（不存在）", p)
PY
```

**不要**用「清空整个 skills 目录」这类粗暴做法 —— 用户可能自己往里面放过技能，只删清单里点名的目录。

---

## Step 3 — 移除 MCP 条目（逐条，只删自己那条）

### 3a. `via: "cli"` 的（Claude Code）

用宿主自己的命令移除，**不要**去手改 `~/.claude.json`：

```bash
claude mcp remove arxiv      # 名字替换成账本里记录的 server
```

对账本里每条 `{"host": "claude-code", "server": "<name>", "via": "cli"}` 执行一次。

### 3b. 有 `path` 的（JSON 宿主：Cursor / Trae / Trae CN 等）

从配置文件里**只删掉账本记录的那几个 server 名**，保留文件里其它一切：

```bash
python3 - <<'PY'
import json, os
state = json.load(open(os.path.expanduser("~/.agent-starter-kit/state.json")))
targets = {}
for item in state.get("mcp", []):
    if item.get("path"):
        targets.setdefault(item["path"], set()).add(item["server"])

for path, names in targets.items():
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        print("跳过（文件不存在）", path); continue
    data = json.load(open(path, encoding="utf-8"))
    servers = data.get("mcpServers", {})
    for n in names:
        if n in servers:
            del servers[n]
            print(f"已移除 {n} <- {path}")
        else:
            print(f"跳过（文件里没有 {n}）{path}")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
```

> ⚠️ **只删名字在 `state.json` 里出现过的条目。** 文件里其它 server 是用户自己的，一个都不能动。
> 若某宿主的 MCP 配置是 TOML（Reasonix / Codex），同理只删对应的 `[mcp_servers.<name>]` 小节，别整段重写。

---

## Step 4 — 依赖与 shim（保守策略：默认只删 shim，不卸依赖）

### 4a. shim —— 可以安全删除

shim 是本套件建的转发脚本，删掉不会有副作用：

```bash
python3 - <<'PY'
import json, os
state = json.load(open(os.path.expanduser("~/.agent-starter-kit/state.json")))
for s in state.get("shims", []):
    p = s.get("shim")
    if p and os.path.isfile(p):
        os.remove(p)
        print("已删除 shim", p)
PY
```

### 4b. Python 包与命令行工具 —— **默认不卸，只列出来让用户自己决定**

⚠️ **不要自动卸载。** 原因：这些包和工具很可能被用户的其他项目、其他工具在用。`pip uninstall pandas` 或 `brew uninstall pandoc` 可能弄坏与本套件无关的东西 —— 这比留着它们危险得多。

正确做法是**列出来，交给用户判断**：

```
以下依赖是本套件安装的。它们可能被你的其它项目用着，
所以默认保留，只列给你看：

【Python 包】卸法：pip uninstall <包名>
  - pandas    （数据处理）
  - docxtpl   （模板批量生成文档）

【命令行工具】卸法见括号
  - pandoc    （brew uninstall pandoc / winget uninstall JohnMacFarlane.Pandoc）
  - tectonic  （brew uninstall tectonic）

要卸哪些告诉我，或者你自己执行上面的命令。
```

清单来源：

```bash
python3 - <<'PY'
import json, os
state = json.load(open(os.path.expanduser("~/.agent-starter-kit/state.json")))
print("Python 包：")
for d in state.get("pythonDeps", []):
    print(f"  {d['pip']:<20}{d.get('why','')}")
print("命令行工具：")
for d in state.get("cliDeps", []):
    print(f"  {d['name']:<14}{d.get('why','')}   装法: {d.get('method','')}")
PY
```

如果用户明确要求卸载某个依赖，**逐条确认后再动手**，不要批量执行。

---

## Step 5 — 清掉账本与生成的配置文件

确认前面都完成后：

```bash
rm -f ~/.agent-starter-kit/state.json
rm -f ~/.agent-starter-kit/mirrors.env
rmdir ~/.agent-starter-kit/bin 2>/dev/null || true
rm -rf ~/.agent-starter-kit/tmp 2>/dev/null || true
rmdir ~/.agent-starter-kit 2>/dev/null || true
```

- `mirrors.env` 是本套件生成的**国内网络加速环境变量**（PyPI/清华、HF 镜像、npm 镜像）。删掉它之前提醒用户：**如果 `~/.zshrc` / `~/.bashrc` 里 source 过它，记得把那行也删掉**，否则每次开终端都会报文件不存在
- `tmp/` 是克隆社区技能时的临时目录，正常已在安装后清理
- （删的只是本套件的账本目录，不含任何用户数据。）

### 关于 `mirrors.env` 要特别说明

这个文件不删也**没有坏处**（只是几个镜像地址的环境变量）。如果用户觉得镜像是好事，可以保留 —— 但要在报告里说清楚它在哪、怎么关掉：

```bash
# 查看
cat ~/.agent-starter-kit/mirrors.env
# 关闭：从 shell 配置里删掉 source 那一行即可
```

---

## 保留什么（不要删）

- **用户的 API Key、Token、账号登录信息** —— 本套件从不碰这些，卸载也不动
- **用户自己配置的 MCP server / 技能 / 配置文件里的其它内容** —— 只做「点名删除账本里的条目」
- 用户自己的项目文件、文档

---

## 验收

卸载后复查：

```bash
claude mcp list 2>/dev/null   # 应看不到本套件注册的 server
python3 -c "import os;p=os.path.expanduser('~/.agent-starter-kit/state.json');print('账本已清除' if not os.path.exists(p) else '账本仍在')"
```

逐项对照 Step 1 的清单，确认每一项都处理了，把结果如实报告给用户。