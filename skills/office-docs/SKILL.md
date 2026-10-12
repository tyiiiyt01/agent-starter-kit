---
name: office-docs
description: 用 Python 库对 Word/Excel/PPT/PDF 做文件级读写（python-docx、openpyxl、python-pptx、pypdf），包括生成、修改、提取文本与表格。当用户要生成或改写 .docx/.xlsx/.pptx、提取 Word/PDF 内容、批量填表，或想用脚本处理办公文档时使用。不驱动正在运行的 Office 窗口。
---

# 办公文档处理（文件级）

## 边界（先讲清楚）

- 本技能**只读写磁盘上的文件**（`.docx` / `.xlsx` / `.pptx` / `.pdf`），生成或修改后由用户自己打开查看
- **不驱动正在运行的 Word/Excel/PPT 窗口**（不通过 COM / AppleScript 操作已打开的文档），那需要客户端联动，本套件不提供
- 旧格式 `.doc` / `.xls` / `.ppt`（97-2003 二进制格式）**这些库读不了**，先让用户用 Office 另存为新格式

## 0. 依赖

```bash
python3 -m pip install python-docx openpyxl python-pptx pypdf
```

缺哪个装哪个。库名与导入名不同，别记混：

- Word → 包 `python-docx`，`import docx`
- Excel → 包 `openpyxl`
- PPT → 包 `python-pptx`，`import pptx`
- PDF → 包 `pypdf`

## 1. Word（.docx）

读：

```python
import docx
d = docx.Document("in.docx")
for p in d.paragraphs:
    print(p.style.name, p.text)
for t in d.tables:
    for row in t.rows:
        print([c.text for c in row.cells])
```

写 / 改：

```python
d = docx.Document()                 # 新建
d.add_heading("标题", level=1)
d.add_paragraph("正文段落")
d.add_paragraph("要点一", style="List Bullet")
t = d.add_table(rows=2, cols=3); t.style = "Table Grid"
t.cell(0, 0).text = "表头"
d.save("out.docx")
```

注意：

- 打开已有文档做**内容替换**时，`add_*` 是追加到末尾；要在中间插内容需操作底层 XML，较复杂，先确认用户到底要什么
- 一段文字常分散在多个 run 里，整段替换要处理 `p.runs`；直接改 `p.text` 会丢格式
- 图片：`d.add_picture("a.png", width=docx.shared.Inches(4))`

## 2. Excel（.xlsx）

读：

```python
import openpyxl
wb = openpyxl.load_workbook("in.xlsx", data_only=True)   # data_only=True 取值不算公式
ws = wb.active
for row in ws.iter_rows(values_only=True):
    print(row)
```

写：

```python
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sheet1"
ws.append(["姓名", "分数"])
ws.append(["张三", 90])
ws["B2"].number_format = "0.0"
ws.column_dimensions["A"].width = 12
wb.save("out.xlsx")
```

注意：

- `data_only=True` 读的是**上次 Excel 保存时缓存的值**；如果文件从没被 Excel 打开过，公式结果是 `None` —— 这时改读公式文本用 `data_only=False`
- 用 openpyxl 写入不会自动算公式，结果是打开 Excel 后才计算
- 大文件用 `read_only=True` 只读模式更省内存

## 3. PPT（.pptx）

读：

```python
from pptx import Presentation
prs = Presentation("in.pptx")
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(i, shape.text)
```

写：

```python
prs = Presentation()                # 默认 4:3；传模板路径可套用你的模板
layout = prs.slide_layouts[1]       # 版式索引因模板而异
slide = prs.slides.add_slide(layout)
slide.shapes.title.text = "第一页标题"
slide.placeholders[1].text = "正文"
prs.save("out.pptx")
```

注意：版式索引随模板变化，**先打印 `prs.slide_layouts` 里的名字确认**，不要硬编码下标。

## 4. PDF（以读为主）

```python
from pypdf import PdfReader, PdfWriter
r = PdfReader("in.pdf")
print(len(r.pages), r.metadata)
text = r.pages[0].extract_text()
w = PdfWriter(); w.append(r); w.write("merged.pdf")
```

注意：

- `extract_text()` 对**扫描版 PDF 返回空**（没有文本层），需要 OCR —— 先确认是不是扫描件
- pypdf 提取复杂排版 / 表格效果一般；要精确提表格优先考虑专门的表格提取方案，或让用户提供原始数据
- **新建 PDF 不是 pypdf 的强项**；需要排版生成 PDF 时，可先出 HTML / Markdown，再让用户或工具转换，不要硬凑

## 5. 交付前自检

- [ ] 生成的文件用户能正常打开
- [ ] 输入与输出路径都明确告知；**默认写到新文件名**，不覆盖用户原文件
- [ ] 明确告诉用户「这是文件级操作，需你自己打开确认」
- [ ] 涉及中文 / 编码的地方已检查（写 xlsx 一般无需特殊处理；生成 PDF 涉及中文字体要先确认字体可用）