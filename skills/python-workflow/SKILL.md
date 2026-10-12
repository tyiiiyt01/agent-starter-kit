---
name: python-workflow
description: 帮用户把 Python 代码从「写完」跑到「跑通」：选对解释器、运行脚本、读 traceback 定位错误、修完再跑，并解决 matplotlib 中文显示成方框的问题。当用户要运行或调试 Python 脚本、遇到 Traceback 报错、pip 装不上包，或画图时中文变方框时使用。
---

# Python 工作流

四步闭环，缺一步都不算完成：**写 → 跑 → 读报错 → 修 → 再跑**。
不要只把代码丢给用户就结束，要实际运行、拿到真实输出或 traceback，再据此修改。

## 0. 先确认用的是哪个解释器

依赖「装了却没用上」是最常见的原因。先固定解释器：

- macOS / Linux：用 `python3 -V`，命令统一用 `python3`，别用 `python`
- Windows：优先 `py -3 -V`；若弹出微软商店说明是占位程序（stub），不是真 Python
- 有虚拟环境就优先用它：`python3 -m venv .venv` 后调用 `.venv/bin/python`（Windows：`.venv\Scripts\python.exe`）

装依赖时用解释器显式调用，避免装到别的环境：

```bash
python3 -m pip install <包名>
```

报 `No module named xxx` 时，先 `python3 -m pip show <包名>` 确认装没装、装在哪个路径。

## 1. 运行脚本

```bash
python3 script.py                    # 普通运行
python3 -u script.py                 # 需要实时看输出时（关缓冲）
python3 -m pytest -q                 # 跑测试
python3 -X faulthandler script.py    # 崩溃（段错误）时定位
```

运行前确认工作目录正确：脚本里的相对路径是相对**当前工作目录**，不是脚本文件所在目录。

## 2. 读 traceback（关键步骤）

Python 的 traceback 从下往上看：

1. **最后一行** = 异常类型 + 消息，先看这个
2. **往上找第一个属于用户代码的帧**（文件名是用户自己写的那行），错误多半在那
3. 库内部的帧通常不用改，看它被哪一行调用

常见异常对照：

| 异常 | 多半原因 | 动作 |
|---|---|---|
| `ModuleNotFoundError` | 包没装或装错环境 | `python3 -m pip install <包>` |
| `ImportError: cannot import name` | 版本不对或名字写错 | `pip show` 看版本，核对 API 名 |
| `FileNotFoundError` | 路径或工作目录不对 | 打印 `os.getcwd()`，改用绝对路径 |
| `IndentationError` / `SyntaxError` | 缩进或语法 | 看报错指向的行号与上一行 |
| `KeyError` / `IndexError` | 键或下标不存在 | 打印容器内容确认 |
| `UnicodeDecodeError` | 文件编码不是 UTF-8 | 读文件显式加 `encoding="utf-8"` 或 `errors="replace"` |
| `TypeError: ... not callable` | 变量名覆盖了函数 | 检查同名变量 |

读文件一律显式指定编码，避免 Windows 默认 GBK 出错：

```python
with open(path, encoding="utf-8") as f:
    text = f.read()
```

## 3. 修完必须重跑

改完再跑一次，把真实输出贴出来。修到「能跑出预期结果」为止，不要改完就说「应该好了」。

## 4. matplotlib 中文方框问题（中文用户第一大坑）

不配置时中文会显示成一屏方框（tofu）。在**任何绘图之前**加下面几行：

```python
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC", "Source Han Sans SC",          # Linux / 通用
    "PingFang SC", "Heiti SC", "Arial Unicode MS",     # macOS
    "Microsoft YaHei", "SimHei",                       # Windows
]
plt.rcParams["axes.unicode_minus"] = False   # 负号也变方框时加这行
```

要点：

- `font.sans-serif` 是**候选列表**，matplotlib 会用第一个系统里存在的字体，多写几个没坏处。
- 找不到字体时**不报错**，只会静默退回、继续显示方框 —— 所以必须实际看一眼图。
- 验证本机有哪些中文字体：

```python
from matplotlib import font_manager
names = sorted({f.name for f in font_manager.fontManager.ttflist})
print([n for n in names if any(k in n for k in ("Hei", "Song", "YaHei", "CJK", "PingFang", "Han"))])
```

把打印出来的名字填到 `font.sans-serif` 列表最前面。

- 无窗口环境（服务器 / 无显示器）先切后端，否则报错或卡住：

```python
matplotlib.use("Agg")   # 必须放在 import pyplot 之前
```

- 保存图片时同样生效：`plt.savefig("out.png", dpi=150, bbox_inches="tight")`。

## 5. 交付前自检清单

- [ ] 脚本在本机跑通，输出已给用户看过
- [ ] 报错已定位到具体行并解释了原因
- [ ] 装了新依赖，并说明装到了哪个环境
- [ ] 有中文的图，且已确认没有方框