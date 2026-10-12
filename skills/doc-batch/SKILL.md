---
name: doc-batch
description: 用 docxtpl + Jinja2 在 Word 模板里批量填数据、从 Excel 逐行渲染批量出文件，并做批量格式转换与合并（pandoc、soffice、pypdf）。当用户要批量生成文档、套模板批量填表、批量转 PDF 或合并拆分文件时使用。
---

# 批量文档生成与格式转换

## 0. 先问清楚

1. **要生成什么**：一批同结构的 Word？还是把现有文件批量转格式？
2. **数据从哪来**：Excel / CSV？每行一条记录？
3. **模板是谁给的**：用户已有 Word 模板，还是要现做？
4. **命名规则**：输出文件按什么规则（如「合同_张三_20261012.docx」）？

## 1. 环境准备

```bash
python3 -m pip install docxtpl openpyxl pandas pypdf
```

`docxtpl` 渲染 Word；`openpyxl` / `pandas` 读数据；`pypdf` 合并拆分 PDF。

## 2. 核心：docxtpl 模板渲染

原理：在 Word 模板里写 **Jinja2 占位符**，Python 侧用数据填充。pip 包名就是 `docxtpl`。

**模板里这样写**：

```
姓名：{{ 姓名 }}
日期：{{ 日期 }}
{%tr for item in items %}
{{ item.名称 }}    {{ item.数量 }}    {{ item.金额 }}
{%tr endfor %}
```

- `{{ 变量 }}` 做单值替换
- `{%tr ... %}` 是 docxtpl 的**整行循环**标签（tr = table row），放在表格行里，能把该行按数据列表复制

**Python 侧**：

```python
from docxtpl import DocxTemplate

tpl = DocxTemplate("模板.docx")
context = {
    "姓名": "张三",
    "日期": "2026-10-12",
    "items": [
        {"名称": "打印纸", "数量": 3, "金额": "45.00"},
        {"名称": "墨盒", "数量": 1, "金额": "180.00"},
    ],
}
tpl.render(context)
tpl.save("输出_张三.docx")
```

要点：

- 中文变量名可用，但要**与模板里完全一致**（含空格）
- 表格行用 `{%tr for %}` / `{%tr endfor %}`；段落循环用 `{%p %}` 或 `{% for %}`
- 占位符若被 Word 拆进多个 run，会渲染失败 —— **在模板里一次输入完整 `{{ 变量 }}`**，不要中途改格式

## 3. 批量：从 Excel 逐行渲染

```python
import pandas as pd
from docxtpl import DocxTemplate
from pathlib import Path

df = pd.read_excel("名单.xlsx")
out = Path("输出"); out.mkdir(exist_ok=True)
ok, fail = [], []
for i, row in df.iterrows():
    try:
        tpl = DocxTemplate("模板.docx")     # 每条数据都要重新加载模板
        tpl.render(row.to_dict())            # 一行数据 = 一次渲染
        name = f"{row['姓名']}.docx"
        tpl.save(out / name)
        ok.append(name)
    except Exception as e:
        fail.append((i, str(e)))             # 单条失败不中断整批
        continue
print(f"成功 {len(ok)} 条，失败 {len(fail)} 条")
for i, e in fail:
    print("失败行", i, e)
```

要点：

- **每条数据都要 `DocxTemplate(...)` 重新加载**：模板对象渲染一次后不能复用
- `df.iterrows()` 直观但慢；数据量大可改 `df.to_dict("records")` 遍历
- 某条渲染失败（缺字段等）**记下继续**，别让整批挂掉；最后把失败清单交给用户

## 4. 批量格式转换

**pandoc（通用）**：

```bash
pandoc a.docx -o a.pdf
```

⚠️ **pandoc 转 PDF 需要 LaTeX 引擎**（如 TeX Live / MiKTeX）。没装引擎时这步会失败，**先确认引擎是否存在**，否则改用下面的 soffice。

**soffice（LibreOffice 无头模式）**：

```bash
soffice --headless --convert-to pdf --outdir ./out *.docx
```

⚠️ 两个关键坑：

1. **macOS 上 `soffice` 不在 PATH**：`/Applications/LibreOffice.app/Contents/MacOS/soffice`；**Windows** 是 `C:\Program Files\LibreOffice\program\soffice.exe`
2. **无头模式不能并发**：一次只跑一个实例，多文件要**串行**执行；**首次运行很慢**（要初始化配置），别以为卡死了

## 5. 批量合并 / 拆分 / 加水印（pypdf）

```python
from pypdf import PdfReader, PdfWriter
w = PdfWriter()                          # 合并
for f in ["a.pdf", "b.pdf", "c.pdf"]:
    w.append(f)
w.write("merged.pdf")
r = PdfReader("in.pdf")                 # 拆分：每页存一个文件
for i, page in enumerate(r.pages):
    w = PdfWriter(); w.add_page(page); w.write(f"page_{i+1}.pdf")
```

- 加水印：把水印 PDF 页与目标页用 `page.merge_page(watermark)` 叠加
- 旋转：`page.rotate(90)`
- 只对**有文本层的 PDF** 有效；扫描件是图片，合并没问题、提取文本要 OCR

## 6. 命名规范与目录组织

批量最容易乱的地方。开始前**先定规则**，别生成一堆 `输出(1).docx`：

- 文件名用**业务主键**：`合同_张三_20261012.docx`，而非 `1.docx`
- 文件名里避免空格和 `/ \ : * ? " < > |`
- 输出统一放**独立目录**（如 `./out/`），**不覆盖用户原文件**，并打印「输入 → 输出」对照清单

## 7. 常见坑自检

- [ ] ⚠️ **先用 1-2 条数据试跑**，确认模板占位符、循环都对，再全量跑
- [ ] 模板里的 `{{ }}` 是完整一次输入的，没被 Word 拆成多个 run
- [ ] 循环表格行用了 `{%tr %}`
- [ ] 每条数据重新加载了模板对象
- [ ] 失败条目已记录且未中断整批
- [ ] macOS 路径 / soffice 串行 / 首跑慢 都已处理
- [ ] 输出写在独立目录，未覆盖原文件