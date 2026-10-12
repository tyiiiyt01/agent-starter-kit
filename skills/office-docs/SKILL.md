---
name: office-docs
description: 用脚本生成/改写"打开即合规、不用再手动调格式"的 Word、Excel、PPT、PDF：以样式/模板优先路线做中文字体四槽位、三线表、公文版心、页眉页码与目录，交付前用 LibreOffice 渲染成图目检中文与排版。当用户要产出可直接交给老师/领导的 .docx/.xlsx/.pptx，或要求套用公文（GB/T 9704）/学位论文/期刊排版规范时使用。
---

# 办公文档（Word / Excel / PPT / PDF）

**能做到**：脚本产出**打开即合格、不用再手动调格式**的 `.docx` / `.xlsx` / `.pptx` / `.pdf` —— 中文字体对槽位、行距缩进合规、表格是规范三线表、页眉页码正确、公文版心对得上、目录能生成。
**做不到**：设计级排版（海报 / 封面 / 精美 PPT）、程序内嵌中文字体、Word 原生公式与自动更新域、红头印章等位图元素。

一句话：**它是"排版规范化"工具，不是"设计"工具** —— 交出去能被直接收下的规范文档没问题；"好看"要靠现成模板，不是靠它从零画。

⚠️ 本文所有配方都在 macOS + Python 3.13 实测（python-docx 1.2.0 / openpyxl 3.1.5）。凡标「先确认」的，动笔前务必先在环境里验证。

## 0. 先看这里：能做什么 / 不能做什么（人话总结）

- 要**格式合规、可直接交**：走本文的**样式优先 + 模板优先**路线，能做到。
- 要**字体万无一失**：程序改不了字体嵌入，**最稳是交付 PDF**（PDF 自控字形，不受对方机器缺字体影响）。
- 要**精美设计**：本技能做不到，用现成模板填内容，或另装设计类技能。
- 要**原生公式 / 自动更新的目录**：做不到全自动，见第 7 节边界表。

## 1. 核心路线：样式优先，不是逐段硬编码

**唯一可靠路线 = 先在 `styles.xml` 里把样式定义对，内容只引用样式名。** 逐段落、逐 run 设字体有三个必踩的坑：

1. `doc.add_heading(...)` 返回的 run，其 `rPr` 是 `None` → 直接设中文字体会崩：`AttributeError: 'NoneType' object has no attribute 'rFonts'`（只有设过字体属性后 `rPr` 才存在）。
2. 三线表要手写 `w:tcBorders` XML（python-docx 没有边框 API）；`Table Grid` 给的是**全框线**，不符合中文学术规范。
3. Word 的目录 / 交叉引用是**域（field）**，程序写完不会自动更新（要打开后按 F9）。

**解法**：样式定义一次、全文引用 —— 绕开坑 1（不用逐 run 设），格式也天然一致、可维护。下面的 `set_run_fonts` 是关键零件，它把 `w:rFonts` **四个槽位**一次写全：

```python
from docx.oxml.ns import qn

def set_run_fonts(rpr, ascii_font="Times New Roman", cjk_font="宋体"):
    """把 w:rFonts 四槽位一次设对：西文/高ANSI/中文/复杂文种。rpr 可来自 style 或 run。"""
    rf = rpr.get_or_add_rFonts()
    rf.set(qn("w:ascii"), ascii_font)      # 西文
    rf.set(qn("w:hAnsi"), ascii_font)      # 西文 High ANSI
    rf.set(qn("w:eastAsia"), cjk_font)     # 中文（最关键，不设必然回落）
    rf.set(qn("w:cs"), ascii_font)         # 复杂文种 complex script
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rf.attrib.pop(qn(a), None)         # 清掉主题字体绑定，否则内置样式可能不生效
```

⚠️ **为什么必须四个都设**：Word 对中文有**独立字体槽位**。只设 `font.name` 只影响 `w:ascii`/`w:hAnsi`，**`w:eastAsia` 不设则中文回落成默认字体** —— 学校要求"宋体正文 + 黑体标题"时直接不合格。
⚠️ **内置标题样式默认走主题字体**（`w:asciiTheme` 等），所以上面那行 `pop` 是必要的。

## 2. Word：达到"直接可用"

### 2.1 定义样式（推荐做法）

```python
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt

def define_style(doc, name, cjk="宋体", ascii_="Times New Roman",
                 size=Pt(12), bold=False, line=1.5, indent_ch=2):
    st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.font.name = ascii_; st.font.size = size; st.font.bold = bold
    set_run_fonts(st.element.get_or_add_rPr(), ascii_, cjk)
    pf = st.paragraph_format
    pf.line_spacing = line
    pf.first_line_indent = size * indent_ch    # 首行缩进 2 字符（≈2×字号）
    return st

define_style(doc, "正文",   cjk="宋体", size=Pt(12), line=1.5)
define_style(doc, "标题1",  cjk="黑体", size=Pt(16), bold=True, line=1.5, indent_ch=0)

doc.add_paragraph("摘要正文……", style="正文")   # 内容只引用样式名，不逐段设字体
doc.add_paragraph("1 引言",      style="标题1")
```

若一定要用内置 `Heading N`：`set_run_fonts(doc.styles["Heading 1"].element.get_or_add_rPr(), "Times New Roman", "黑体")`，并确认主题属性已被清掉。

### 2.2 页面设置（A4 / 公文版心）

```python
from docx.shared import Cm, Mm
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)          # A4
# 普通学位论文：上下 2.54cm、左右 3.17cm（左留装订线）
sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.left_margin = sec.right_margin = Cm(3.17)
# 党政机关公文（GB/T 9704）：天头(上)37±1mm、订口(左)28±1mm，版心 156×225mm
# 由版心反推：下 ≈35mm、右 ≈26mm
sec.top_margin, sec.left_margin   = Mm(37), Mm(28)
sec.bottom_margin, sec.right_margin = Mm(35), Mm(26)
```

### 2.3 三线表（XML 配方，必须手写）

```python
from docx.oxml import OxmlElement

def three_line_table(tbl):
    """中文学术三线表：顶线粗、表头下线细、底线粗，无竖线。w:sz 单位为 1/8 pt。"""
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
                    el.set(qn("w:sz"), "12" if i == 0 else "6")   # 顶/底线 1.5pt，表头线 0.75pt
                borders.append(el)
            tcPr.append(borders)
```

### 2.4 页眉页脚 / 页码

```python
# 页码/页眉是"域"，需按需设置
hdr = sec.header; hdr.is_linked_to_previous = False
hdr.paragraphs[0].text = "某某大学本科毕业论文"
ftr = sec.footer; ftr.is_linked_to_previous = False
# 首页不显示 / 奇偶页不同页眉：需显式开开关，否则设置不生效
sec.different_first_page_header_footer = True                     # 首页页眉页脚独立
doc.settings.odd_and_even_pages_header_footer = True              # 奇偶页不同页眉
```

页码本身是 `PAGE` 域，需插 XML；生成后提醒用户在 Word 里确认（见第 7 节）。

### 2.5 公文格式硬指标（GB/T 9704—2012）

- 版心：天头(上) 37±1mm、订口(左) 28±1mm、版心 **156×225mm**
- 每页 **22 行 × 每行 28 字**
- 正文：**3 号仿宋_GB2312**（≈16pt）
- 标题层级：一级**黑体**、二级**楷体**、三/四级**仿宋**
- 页码：**4 号半角宋体**
- ⚠️ 坑：**仿宋_GB2312 不是系统标配字体**，缺字体的机器会回落 —— 交付 PDF 或预处理嵌入。

### 2.6 学位论文共性要求（各校细则不同）

- 正文**宋体小四**（12pt）、标题**黑体**、**1.5 倍行距**、**首行缩进 2 字符**
- 页眉页脚常**奇偶页不同**；**自动目录**；图表**交叉引用**；参考文献 **GB/T 7714**
- 各校有独立模板 → **让用户提供学校模板**，走模板路线最省事。

## 3. 交付前的渲染-目检循环（最有价值的一步）

程序**无法自证**"中文字体有没有回落""排版对不对"。**唯一可靠办法是渲染出来看**：

```bash
# 首次需安装（macOS）：brew install --cask libreoffice ; brew install poppler
soffice --headless -env:UserInstallation=file:///tmp/lo_profile \
  --convert-to pdf --outdir /tmp/render out.docx
pdftoppm -png -r 100 /tmp/render/out.pdf /tmp/render/page
# 然后让 AI 看图确认：中文字体是否正常？有无方框/回落？标题层级对不对？表格线对不对？
```

- macOS 上 `soffice` 可能不在 PATH，用全路径 `/Applications/LibreOffice.app/Contents/MacOS/soffice`。
- 换机器/换字体后**必须重跑**这一段。
- 无法看图的环境：至少用 `pdftotext /tmp/render/out.pdf - | head` 抽取文本，确认**内容完整、无乱码**。
- **要"字体万无一失"就直接交付 PDF**：PDF 自控字形，不受对方机器缺字体影响（Word 改 PDF 用上面的 `soffice` 转换即可）。
- 读已有 PDF 用 `pypdf`（`PdfReader`/`PdfWriter`）；⚠️ `extract_text()` 对**扫描版返回空**（无文本层），需先确认是否扫描件。

## 4. Excel：新建用 XlsxWriter / 改已有用 openpyxl

- **新建报表（带格式/图表/条件格式）→ `XlsxWriter`**（BSD-2 许可）：格式、图表、条件格式能力比 openpyxl 更强。**只能新建**，不能改已有模板。
- **读取或修改已有文件 → `openpyxl`**：`load_workbook(path)` 原样保留公式、条件格式、图表。
- 导入名：`import xlsxwriter` / `import openpyxl`。
- 常用（openpyxl）：`Font(bold=True, color="FFFFFF")` + `PatternFill("solid", fgColor="02743B")` 做表头；`CellIsRule(...)` 挂 `ws.conditional_formatting.add("E2:E5", rule)`；`LineChart()` + `Reference(...)` + `ws.add_chart(ch, "H2")`。
- 写完一律 `load_workbook` **重开验证**：公式文本在、条件格式组数对、图表对象在。
- ⚠️ 环境里未装 `XlsxWriter` 时先 `python3 -m pip install XlsxWriter`，别默认它已存在。

## 5. PPT：模板优先填充，不要从零画

- 用 `python-pptx`（`import pptx`）或 `PptxGenJS`（MIT 许可）往**现成模板/版式里填内容**，别从零摆框。
- 版式索引随模板变化：先打印 `prs.slide_layouts` 的**名字**确认，别硬编码下标。
- ⚠️ **`Marp` / `Slidev` 导出的 pptx 是图片、不可编辑** —— 中文商务/汇报场景要可编辑 pptx 时**不要用它们**。

## 6. 中文插图：matplotlib

```python
import matplotlib; matplotlib.use("Agg")   # 无显示器环境
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC", "Source Han Sans SC",      # Linux / 通用
    "PingFang SC", "Heiti SC", "Arial Unicode MS", # macOS
    "Microsoft YaHei", "SimHei",                   # Windows
]
plt.rcParams["axes.unicode_minus"] = False          # 否则负号显示成方框
fig.savefig("fig.png", dpi=600, bbox_inches="tight")   # 学术要求 ≥600 dpi
doc.add_paragraph().add_run().add_picture("fig.png", width=Cm(11))  # 图必须挂在 run 上
```

- ⚠️ `Document` 对象**没有** `add_run()`；必须 `doc.add_paragraph().add_run().add_picture(...)`。
- 没配到字体**不报错**，会静默退回成方框 —— **必须渲染看图确认**。
- 提前验证字体是否命中：`matplotlib.font_manager.findfont("SimHei", fallback_to_default=False)`（找不到会抛异常）。

## 7. 能力边界（诚实表）

| 做不到 | 原因 | 替代 |
|---|---|---|
| **程序内嵌中文字体** | python-docx / docx(npm) 都不支持 `w:embedRegular` | 模板里预先勾"将字体嵌入文件"；或**直接交付 PDF** |
| Word **原生公式（OMML）** | 无 API | LaTeX 生成图片插入，或手工敲 |
| **目录/交叉引用自动更新** | 是 Word **域（field）**，需打开后按 **F9** | 生成后提醒用户更新；或用 pandoc `--toc` |
| **公文红头/印章** | 是位图图形 | 用模板预置 |
| **页眉奇偶页不同** | 需分节 + 显式开关 | 设 `different_first_page_header_footer`、`odd_and_even_pages_header_footer` |
| 各校/各刊**个性化细则** | 无法穷举 | 让用户提供学校模板，走模板路线 |
| **设计级排版**（海报/封面/精美 PPT） | 库只做结构 | 用现成模板，或另装设计类技能 |
| `.doc` / `.xls` 旧格式 | 库不支持 | 先 `soffice --headless --convert-to` 转新格式 |

## 8. 常见坑清单

- **`._element.rPr` 是 `None` 导致崩溃**：run 的 `rPr` 只有设过字体属性才存在 → 用样式，或先设 `font.name`（见第 1、2.1 节）。
- **只设 `font.name` 中文回落**：中文必须写 `w:eastAsia`，四槽位一次设全（见 `set_run_fonts`）。
- **内置样式主题字体覆盖你的设置**：记得 `pop` 掉 `w:asciiTheme` 等（见第 1 节）。
- **`Table Grid` 不符合三线表规范**：它给全框线，要手写 `tcBorders`（见 2.3）。
- **目录/交叉引用不更新**：是域，不是文本；生成后要按 F9。
- **只改 `p.text` 丢格式**：一段文字常分散在多个 run，整段替换会丢格式，要逐 run 处理。
- **`add_*` 只追加到末尾**：想在中间插入得操作底层 XML，先确认用户到底要什么。
- **matplotlib 负号成方框**：`axes.unicode_minus = False`。
- **中文方框/缺字**：字体名写错或该机没装 → `findfont(..., fallback_to_default=False)` 提前验证。
- **改完没渲染目检就交付**：最危险的坑 —— 无方框、无回落的确认只能靠第 3 节的渲染-目检。
- **交付默认写新文件名**：不覆盖用户原文件，并明确告知输入/输出路径。