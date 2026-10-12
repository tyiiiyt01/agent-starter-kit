# packs/*.json 数据格式

`scripts/apply.py` 和 `scripts/doctor.py` 只认这份格式。**字段名写错会被静默忽略**，改完务必跑自检。

## 顶层字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 必须与文件名一致（`code.json` → `"code"`） |
| `display` | ✅ | 中文显示名，用于清单展示 |
| `for` | ✅ | 面向谁（一句话） |
| `skills` | ✅ | `skills/` 下的**目录名**数组，必须与真实目录一一对应 |
| `mcp` | ✅ | MCP server 数组，没有就写 `[]` |
| `pythonDeps` | 可选 | Python 包数组，没有就写 `[]` |
| `cliDeps` | 可选 | 命令行工具数组，没有就写 `[]` |
| `manual` | ✅ | 需要用户自己动手的事项，字符串数组，没有就写 `[]` |

## `mcp[]`

```json
{
  "name": "arxiv",
  "command": "uvx",
  "args": ["arxiv-mcp-server"],
  "env": { "SOME_KEY": "值" },
  "why": "一句话说明这个东西干什么用",
  "optional": true
}
```

- `args` 里可用 `{{HOME}}` 占位符，写入前会被替换成用户主目录
- `optional: true` 表示失败也不影响整体
- ⚠️ **只用核实过真实存在的 server**。写错包名会让用户在装的时候失败，比不装更糟

## `pythonDeps[]`

```json
{
  "pip": "scikit-learn",
  "import": "sklearn",
  "tier": "light",
  "why": "分类/回归/聚类，数模常用"
}
```

- `pip` 是 pip 安装名，`import` 是**导入名** —— 两者常常不同（`scikit-learn` → `sklearn`、`Pillow` → `PIL`）。`doctor.py` 用 `import` 名验证
- `tier`：`light`（<100MB，默认装）/ `medium`（100MB–1GB，需 `--tier medium`）/ `heavy`（>1GB，永不自动装）

## `cliDeps[]`

```json
{
  "name": "pandoc",
  "bins": ["pandoc"],
  "tier": "light",
  "why": "文档格式转换（docx/md/tex/pdf 互转）",
  "probe": ["pandoc", "--version"],
  "knownPaths": {
    "darwin": ["/opt/homebrew/bin/pandoc", "/usr/local/bin/pandoc"],
    "win32": ["%LOCALAPPDATA%/Pandoc/pandoc.exe", "%ProgramFiles%/Pandoc/pandoc.exe"],
    "linux": ["/usr/bin/pandoc"]
  },
  "install": {
    "darwin": "brew install pandoc",
    "win32": "winget install --id JohnMacFarlane.Pandoc -e",
    "linux": "sudo apt-get install -y pandoc"
  },
  "fallback": "没有 pandoc 时改用 markitdown 或纯 Python 库完成同类任务"
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `bins` | ✅ | 在 PATH 里找哪些可执行文件名。多个名字都算命中（如 poppler 的 `pdftotext`/`pdftoppm`） |
| `knownPaths` | 强烈建议 | **工具装了但不在 PATH 时的已知位置** —— 这是「下载了却用不了」的解药。命中后会自动建 shim |
| `probe` | 可选 | 验证能真的执行（默认 `[bins[0], "--version"]`） |
| `install` | ✅ | 按 OS 给安装命令。**只允许简单命令，不要用管道 `\|`**（脚本用 `shlex.split` 执行，管道会失败） |
| `fallback` | ✅ | 没这个工具时怎么办。**必须写**，否则 doctor 报错时用户不知道下一步 |
| `shim` | 可选 | 默认 `true`。设为 `false` 表示不建 shim（例如工具本身就要求用户改 PATH） |

### 关于 tier

| tier | 策略 |
|---|---|
| `light` | 默认自动安装。几十 MB，失败可容忍 |
| `medium` | 需要显式 `--tier medium` 才装。上百 MB |
| `heavy` | **永不自动安装**。只检测 + 给引导（LibreOffice ≈700MB、MacTeX >1GB） |

## 写作硬性要求

1. **不许编造包名、命令、URL。** 不确定的写进 `manual` 里当引导，不要塞进 `install`
2. **体积要标对**。把 GB 级的东西标成 `light` 会让小白在下载时卡死半小时
3. **`fallback` 必填有意义的内容**。写「无」等于没写 —— 要写清降级方案
4. 每个 `skills` 声明的目录必须真实存在，否则 doctor 会报「源缺失」