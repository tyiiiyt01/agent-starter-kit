---
name: office-docs
description: 用 Python 库对 Word/Excel/PPT/PDF 做文件级读写与生成（python-docx、openpyxl、python-pptx、pypdf），含中文字体、三线表、页面设置、公式与条件格式、中文图表等实测配方，并明确列出能力边界。当用户要生成或改写 .docx/.xlsx/.pptx、提取 Word/PDF 内容、批量填表或要求中文排版规范时使用。
---

# 办公文档处理（文件级）

**能做**：用脚本在磁盘上生成 / 改写 / 读取 `.docx` / `.xlsx` / `.pptx` / `.pdf`，输出结构规范、中文正常、公式与图表保留，用户可以打开直接交。
**不能做**：Word 原生公式（OMML）、目录自动更新、设计级排版（海报 / 精美 PPT / 封面），也不驱动正在运行的 Office 窗口。

一句话：**它能生成"能打开、结构规范、中文正常、可以直接交"的文档；但不会替你做出"设计精美"的文档。**

以下配方均在 macOS + Python 3.13 下**实测通过**（python-docx 1.2.0 / openpyxl 3.1.5 / matplotlib 3.11.1 / Pillow 12.3.0）。

## 0. 依赖

```bash
python3 -m pip install python-docx openpyxl python-pptx pypdf
```

库名与导入名不同，别记混：Word → `python-docx`（`import docx`）；Excel → `openpyxl`；PPT → `python-pptx`（`import pptx`）；PDF → `pypdf`。

## 1. 实测结论速览

| 格式 | 结果 | 验证方式 |
|---|---|---|
| `.docx` 181KB | 成功 | macOS 原生 `textutil -convert txt -stdout x.docx` 能读出中文、标题、表格内容 |
| `.xlsx` 7KB | 成功 | `load_workbook` 重开，公式 `=C2*0.3+D2*0.7` 保留，条件格式 1 组，图表 1 个 |
| `.pptx` 173KB | 成功 | `Presentation` 重开，2 页 16:9，中文正常 |

结论：生成的**都是合法可重开的文件**，不是"看着像"。验证一律用**重开 + 取值**，不要只看文件大小。

## 2. Word（.docx）

读 / 写基础：
```python
import docx
d = docx.Document("in.docx")                  # 读
for p in d.paragraphs: print(p.style.name, p.text)
for t in d.tables:
    for row in t.rows: print([c.text for c in row.cells])

d = docx.Document()                           # 新建
d.add_heading("标题", level=1); d.add_paragraph("正文段落")
d.add_paragraph("要点一", style="List Bullet")
t = d.add_table(rows=2, cols=3); t.cell(0, 0).text = "表头"
d.save("out.docx")
```

### 2.1 ⚠️ 中文字体：必须先设 `font.name`，否则**崩溃**

直接对 `add_heading` 返回的 run 访问 `rPr` 会报错：
```python
# ❌ 这样写会报错
doc.add_heading("一、实验目的", level=2).runs[0]._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
# AttributeError: 'NoneType' object has no attribute 'rFonts'
```
原因：run 的 `rPr`（run properties）元素只有在**设置过字体属性后**才会被创建，直接访问 `._element.rPr` 得到 `None`。

正确做法（实测通过）：先设 `run.font.name`（这会创建 `rPr` / `rFonts`），再补 `eastAsia`：
```python
from docx.oxml.ns import qn

def cjk(run, ascii_font="Times New Roman", cjk_font="宋体", size=12, bold=False):
    """安全地给 run 设置中文字体。必须先设 font.name，否则 rPr 不存在会崩。"""
    run.font.name = ascii_font      # 这一步会创建 rPr / rFonts
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cjk_font)
    return run
```
⚠️ **为什么必须设 `w:eastAsia`**：Word 对中文有独立的字体槽位（eastAsia）。只设 `font.name` 只影响西文（ascii/hAnsi），**中文会回落成默认字体**，在学校要求"宋体正文 + 黑体标题"时直接不合格。

### 2.2 三线表：python-docx 没有 API，要手写 XML

中文学术规范的三线表是「顶线粗、表头下线细、底线粗，无竖线」。`table.style = "Table Grid"` 会给**全框线**，不符合规范，且 python-docx 没有现成 API 改边框。实测可用做法：
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def three_line_table(tbl):
    """把表格改成中文学术规范的三线表：只保留顶线、表头下线、底线。"""
    for i, row in enumerate(tbl.rows):
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                el = OxmlElement(f"w:{edge}")
                on = (edge == "top" and i == 0) or \
                     (edge == "bottom" and i in (0, len(tbl.rows) - 1))
                el.set(qn("w:val"), "single" if on else "nil")
                if on:
                    el.set(qn("w:sz"), "12" if i == 0 else "6")   # 顶/底线 12，表头线 6
                borders.append(el)
            tcPr.append(borders)
```

中文论文页面设置（A4 + 装订线）：
```python
from docx.shared import Cm
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)      # A4
sec.top_margin = sec.bottom_margin = Cm(2.54)            # 上下 2.54
sec.left_margin = sec.right_margin = Cm(3.17)            # 左右 3.17（留装订线）
```

## 3. Excel（.xlsx）

读 / 写与实用配方（实测通过）：
```python
import openpyxl
wb = openpyxl.load_workbook("in.xlsx", data_only=True)   # 读；data_only=True 取值不算公式
ws = wb.active
for row in ws.iter_rows(values_only=True): print(row)

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sheet1"
ws.append(["姓名", "平时", "期末", "总分"])
ws["E2"] = "=C2*0.3+D2*0.7"                  # 公式直接写字符串，openpyxl 原样保留
ws.column_dimensions["B"].width = 12          # 列宽要显式设
```
- **表头样式**：`Font(bold=True, color="FFFFFF")` + `PatternFill("solid", fgColor="02743B")`
- **条件格式**：`CellIsRule(operator="lessThan", formula=["60"], fill=..., font=...)`，用 `ws.conditional_formatting.add("E2:E5", rule)` 挂上去
- **图表**：`LineChart()` + `Reference(ws, min_col=5, min_row=1, max_row=5)` + `ws.add_chart(ch, "H2")`
- 写完用 `load_workbook` **重开验证**：公式文本在、条件格式组数对、图表对象在

## 4. PPT（.pptx）

结构生成（实测通过）：
```python
from pptx import Presentation
from pptx.util import Inches, Pt
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)   # 16:9
blank = prs.slide_layouts[6]                                      # 空白版式最可控
s = prs.slides.add_slide(blank)
tb = s.shapes.add_textbox(Inches(1), Inches(2.6), Inches(11.3), Inches(1.6))
r = tb.text_frame.paragraphs[0].add_run()
r.text = "标题"
r.font.name = "微软雅黑"; r.font.size = Pt(44)
s.shapes.add_picture("fig.png", Inches(7.6), Inches(2.0), width=Inches(5.0))
prs.save("out.pptx")
```
⚠️ **局限**：`python-pptx` 只能摆**结构**（文本框、图片、位置），**做不出设计**。版式索引随模板变化，先打印 `prs.slide_layouts` 的**名字**确认，别硬编码下标。要"精美 PPT"必须另装 `ppt-master`（见第 6 节）。

## 5. 中文插图：matplotlib

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Songti SC", "Heiti SC", "Arial Unicode MS"]  # macOS 可用
plt.rcParams["axes.unicode_minus"] = False               # 否则负号显示成方框
fig.savefig("fig.png", dpi=600, bbox_inches="tight")     # 学术要求 ≥600 dpi
# 插入 docx：必须先有段落，再由段落的 run 承载图片
doc.add_paragraph().add_run().add_picture("fig.png", width=Cm(11))
```
⚠️ `Document` 对象**没有** `add_run()` 方法 —— 写成 `doc.add_run().add_picture(...)` 会报 `AttributeError`。
图片必须挂在**段落里的 run** 上：`doc.add_paragraph().add_run().add_picture(...)`。
字体名跨平台不同：macOS 常见 `Songti SC`（宋体）、`Heiti SC`（黑体）、`Arial Unicode MS`、`PingFang SC`；Windows 常见 `SimSun`（宋体）、`SimHei`（黑体）、`Microsoft YaHei`（微软雅黑）。建议配成**候选列表**让 matplotlib 自动挑，并提前验证字体是否命中：
```python
import matplotlib.font_manager as fm
fm.findfont("SimHei", fallback_to_default=False)   # 找不到会抛异常，用来提前发现
```

## 6. 能力边界（做不到的要讲清）

| 做不到 | 原因 | 怎么办 |
|---|---|---|
| Word **原生公式（OMML）** | python-docx 没有公式 API，只能插入图片或用纯文本近似 | 复杂公式用 LaTeX 生成图片插入，或手工在 Word 里敲 |
| Word **目录自动更新** | 目录是域（field），需要 Word 打开后按 F9 更新 | 生成完提醒用户手动更新；或用 pandoc 的 `--toc` |
| **设计级排版**（海报、精美 PPT、封面设计） | python-docx / python-pptx 只能做结构，没有设计能力 | 明确说清这是"结构正确、能用"级别；设计型输出要另装 `ppt-master`（默认会装）或 `anthropics-skills` |
| **驱动正在运行的 Office 窗口** | 需要进程联动 | 只做文件级读写 |
| `.doc`（旧格式）、`.xls`（旧格式） | 库不支持 | 先用 LibreOffice `soffice --headless --convert-to` 转成新格式 |

## 7. PDF（以读为主）

```python
from pypdf import PdfReader, PdfWriter
r = PdfReader("in.pdf"); print(len(r.pages), r.metadata)
w = PdfWriter(); w.append(r); w.write("merged.pdf")
```
- `extract_text()` 对**扫描版 PDF 返回空**（没有文本层），需要 OCR —— 先确认是不是扫描件
- 提取复杂排版 / 表格效果一般；**新建 PDF 不是 pypdf 的强项**，要排版生成 PDF 先出 HTML / Markdown 再转换

## 8. 常见坑

- **`._element.rPr` 是 `None` 导致崩溃**：run 的 `rPr` 只有设过字体属性才存在，必须先 `run.font.name = ...` 再改 `rFonts`（见 2.1）
- **只设 `font.name` 中文会回落**：中文要写 `w:eastAsia` 槽位，否则"宋体 + 黑体"要求不达标（见 2.1）
- **`Table Grid` 不符合三线表规范**：它给全框线，学术表格要手写 `tcBorders`（见 2.2）
- **matplotlib 负号显示成方框**：`axes.unicode_minus` 要设 `False`
- **中文方框 / 缺字**：字体名写错或该平台没装，用 `fm.findfont(..., fallback_to_default=False)` 提前验证
- **打开已有文档替换内容**：`add_*` 只会追加到末尾；要中间插入得操作底层 XML，先确认用户到底要什么
- **整段替换丢格式**：一段文字常分散在多个 run 里；直接改 `p.text` 会丢格式，要逐 run 处理
- **`.doc` / `.xls` 读不了**：这些库不支持旧二进制格式，先转换

## 9. 交付前自检

- [ ] 生成的文件**重开验证**过（docx 用 textutil，xlsx 用 `load_workbook`，pptx 用 `Presentation`）
- [ ] 中文正常（无方框、字体槽位对）
- [ ] 输入与输出路径都明确告知；**默认写新文件名**，不覆盖用户原文件
- [ ] 明确告诉用户「这是文件级操作，你自己打开确认」，并说清哪些做不到（公式、目录、设计）