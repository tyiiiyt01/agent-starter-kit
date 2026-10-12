#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 office-docs 技能用的 3 个中文 .docx 模板（可复现、可审计）。

用法:
    python3 scripts/make_templates.py                # 输出到 templates/docx/
    python3 scripts/make_templates.py --out /tmp/x   # 输出到指定目录（幂等，覆盖同名文件）

输出:
    templates/docx/report-zh.docx    通用中文报告（实验报告 / 课程报告）
    templates/docx/gongwen-zh.docx   党政机关公文（GB/T 9704—2012）
    templates/docx/thesis-zh.docx    学位论文（各校共性要求）

为什么用脚本生成模板，而不是直接提交 .docx 二进制:
    1. 可审计 —— 每个中文字体槽位、每条三线表边框、每个域都能在代码里读到，
       而不是埋进一个打不开的二进制包里；改了什么，git diff 一清二楚。
    2. 可改 —— 要调字号/版心/页边距，改下面的常量重跑即可，不用装 Word 手工调。
    3. 可复现 —— 任何人 clone 后一条命令就得到一致的模板，不依赖某台机器上的 Word。

技术要点（与 skills/office-docs/SKILL.md 对应）:
    · 中文字体必须写 w:rFonts 的四槽位 ascii/hAnsi/eastAsia/cs —— 只设 font.name 中文会回落
    · 格式一律做成**样式**（doc.styles），正文只引用样式名，不逐段硬编码
    · 首行缩进 2 字符 = w:ind/@w:firstLineChars="200"（python-docx 无 API，手写 XML）
    · 页码 = PAGE 域（fldChar begin / instrText PAGE / end），python-docx 无 API，手写 XML
    · 三线表 = 手写边框 XML（python-docx 没有边框 API；内置 Table Grid 是全框线，不合规）
    · docxtpl 占位符一行写完（{{ }} / {%tr %}），不能中途改格式，否则会被 Word 拆进多个 run

依赖: python-docx（**仅运行本脚本需要**，装法 `pip install python-docx`）。
      它不在 requirements.txt 里 —— 那份是【安装引擎自身】的依赖（apply.py 跑起来需要的），
      本脚本属维护者工具，两者不要混。用户侧要的是 docxtpl + python-docx，
      已由 office / writing 能力包的 pythonDeps 声明，装包时自动装上。
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Length, Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "templates" / "docx"

# ---------------------------------------------------------------------------
# 字体常量。西文统一 Times New Roman（中文文档惯例）；中文按用途分槽位。
# ⚠️ 仿宋_GB2312 / 楷体_GB2312 不是系统标配字体，缺失的机器会回落 —— 见 templates/docx/README.md
# ---------------------------------------------------------------------------
WEST = "Times New Roman"
SONG = "宋体"
HEI = "黑体"
KAI = "楷体_GB2312"
FANGSONG = "仿宋_GB2312"

# 字号别名（磅）：二号 22 / 小二 18 / 三号 16 / 小三 15 / 四号 14 / 小四 12 / 五号 10.5


# ---------------------------------------------------------------------------
# 底层 XML / 字体槽位
# ---------------------------------------------------------------------------
def set_run_fonts(rpr, ascii_font: str = WEST, cjk_font: str = SONG) -> None:
    """把 w:rFonts 四槽位一次设对：西文 / 西文 High-ANSI / 中文 / 复杂文种。

    ⚠️ 中文有**独立槽位** w:eastAsia；只设 font.name 只影响 ascii/hAnsi，
       不设 w:eastAsia 中文必然回落成默认字体。这里同时 pop 掉主题字体绑定，
       否则内置样式（Heading N 等）会走主题字体覆盖我们的设置。
    """
    rf = rpr.get_or_add_rFonts()
    rf.set(qn("w:ascii"), ascii_font)
    rf.set(qn("w:hAnsi"), ascii_font)
    rf.set(qn("w:eastAsia"), cjk_font)
    rf.set(qn("w:cs"), ascii_font)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rf.attrib.pop(qn(a), None)


def set_indent(pPr, first_line_chars: int | None = None, first_line_pt: float | None = None) -> None:
    """写 w:ind。w:firstLineChars 单位是 1/100 字符（200 = 2 字符）；w:firstLine 单位 twips。"""
    ind = pPr.get_or_add_ind()
    if first_line_chars is not None:
        ind.set(qn("w:firstLineChars"), str(first_line_chars))
    if first_line_pt is not None:
        ind.set(qn("w:firstLine"), str(int(round(first_line_pt * 20))))  # 磅 → twips


def clear_indent(par) -> None:
    """清掉某段继承来的首行缩进（用于页眉/页码/居中元素，防 Normal 的缩进带歪它们）。"""
    set_indent(par._p.get_or_add_pPr(), first_line_chars=0, first_line_pt=0)


def add_page_field(par, cjk: str = SONG, ascii_font: str = WEST, size: Pt = Pt(10.5)) -> None:
    """在段落里插入 PAGE 域作为页码。python-docx 无域 API，手写三段 fldChar XML。"""
    run = par.add_run()
    run.font.size = size
    set_run_fonts(run._r.get_or_add_rPr(), ascii_font, cjk)
    r = run._r
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, end):
        r.append(el)


def add_toc_field(doc, levels: str = "1-3") -> None:
    """插入 Word 目录域（TOC）。

    ⚠️ 域写入后**不会自动更新** —— 打开文档后要把光标放进目录区按 F9（或右键"更新域"）。
       所以域里先放一段占位说明文字，供用户看到提示。
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_indent(p)

    def _field_run(fld_type: str) -> OxmlElement:
        run = p.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), fld_type)
        run._r.append(el)
        return run._r

    _field_run("begin")
    instr_run = p.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f' TOC \\o "{levels}" \\h \\z \\u '   # \o 取 1-3 级标题，\h 超链接，\z 隐藏页码
    instr_run._r.append(instr)
    _field_run("separate")
    ph = p.add_run("（目录占位：在 Word 里把光标放到此处，按 F9 或右键“更新域”生成目录）")
    ph.font.size = Pt(10.5)
    set_run_fonts(ph._r.get_or_add_rPr(), WEST, SONG)
    _field_run("end")


# ---------------------------------------------------------------------------
# 样式定义
# ---------------------------------------------------------------------------
def configure_normal(doc, cjk: str = SONG, size: Pt = Pt(12), line=1.5,
                     first_line_pt: float = 24.0) -> None:
    """Normal = 正文：宋体小四、1.5 倍行距、首行缩进 2 字符。"""
    st = doc.styles["Normal"]
    st.font.size = size
    set_run_fonts(st.element.get_or_add_rPr(), WEST, cjk)
    pf = st.paragraph_format
    _apply_line(pf, line)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    set_indent(st.element.get_or_add_pPr(), first_line_chars=200, first_line_pt=first_line_pt)
    # 页眉/页脚样式默认 basedOn Normal，会把首行缩进带过去 → 显式清零
    for nm in ("Header", "Footer"):
        try:
            set_indent(doc.styles[nm].element.get_or_add_pPr(), first_line_chars=0, first_line_pt=0)
        except KeyError:
            pass


def _apply_line(pf, line) -> None:
    """line 为 float → 倍数行距；为 Length（Pt(...)）→ 固定值行距（公文每页 22 行的做法）。"""
    if isinstance(line, Length):
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = line
    else:
        pf.line_spacing = line


def configure_heading(doc, name: str, size: Pt, cjk: str = HEI, bold: bool = True, line=1.5) -> None:
    """改造内置 Heading N：中文字体四槽位 + 黑色（默认是主题蓝）+ 无首行缩进（Normal 有缩进，必须清掉）。"""
    st = doc.styles[name]
    st.font.size = size
    st.font.bold = bold
    st.font.italic = False
    st.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    set_run_fonts(st.element.get_or_add_rPr(), WEST, cjk)
    pf = st.paragraph_format
    _apply_line(pf, line)
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_indent(st.element.get_or_add_pPr(), first_line_chars=0, first_line_pt=0)


def define_style(doc, name: str, cjk: str = SONG, ascii_font: str = WEST, size: Pt = Pt(12),
                 bold: bool = False, align=None, line=1.5, space: float = 0.0):
    """定义自定义段落样式（基于 Normal）。所有自定义样式一律无首行缩进。"""
    st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = doc.styles["Normal"]
    st.font.size = size
    st.font.bold = bold
    set_run_fonts(st.element.get_or_add_rPr(), ascii_font, cjk)
    pf = st.paragraph_format
    _apply_line(pf, line)
    pf.space_before = Pt(space)
    pf.space_after = Pt(space)
    if align is not None:
        pf.alignment = align
    set_indent(st.element.get_or_add_pPr(), first_line_chars=0, first_line_pt=0)
    return st


def define_three_line_table_style(doc, name: str = "三线表"):
    """自定义表格样式「三线表」。

    ⚠️ python-docx 对表格样式的支持很有限：CT_Style 没有 get_or_add_tblPr，
       这里直接手写 w:tblPr/w:tblBorders 挂到样式元素上（w:name 之后，符合 schema 顺序）。
       更重要的是：表格**样式**无法表达"只在表头行下画细线"这种按区域的规则，
       所以三线表的实际框线一律在生成时手写（见 three_line_table()）。
       这个样式的作用是：让「三线表」在 Word 样式库里存在、可见、可改，并把默认框线清成无。
    """
    st = doc.styles.add_style(name, WD_STYLE_TYPE.TABLE)
    tblPr = OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)
    st.element.append(tblPr)
    return st


# ---------------------------------------------------------------------------
# 三线表 / 表格
# ---------------------------------------------------------------------------
def three_line_table(tbl) -> None:
    """中文学术三线表：顶线粗(1.5pt)、表头下线细(0.75pt)、底线粗(1.5pt)，无竖线。w:sz 单位 1/8 pt。

    与 SKILL.md 逐行版本的**关键差别**：数据行是 docxtpl 循环行，模板里只有 1 行样本，
    渲染后行数不定 —— "最后一行画底线"不能逐行写死（否则每个数据行下都有一条粗线）。
    所以底线改用**表格级** w:tblBorders/w:bottom，Word 会把它画在渲染后真正的最后一行上，
    insideH/insideV/left/right 一律 nil 保证无内部横线与竖线。表头下线只作用于固定的表头行。
    """
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, val, sz in (("top", "single", "12"), ("bottom", "single", "12"),
                          ("left", "nil", None), ("right", "nil", None),
                          ("insideH", "nil", None), ("insideV", "nil", None)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        if sz:
            el.set(qn("w:sz"), sz)
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "auto")
        borders.append(el)
    tblPr.insert_element_before(borders, "w:shd", "w:tblLayout", "w:tblCellMar",
                                "w:tblLook", "w:tblCaption", "w:tblDescription")
    for cell in tbl.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tb = OxmlElement("w:tcBorders")
        for edge, val, sz in (("top", "single", "12"), ("bottom", "single", "6"),
                              ("left", "nil", None), ("right", "nil", None)):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), val)
            if sz:
                el.set(qn("w:sz"), sz)
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), "auto")
            tb.append(el)
        tcPr.insert_element_before(tb, "w:shd", "w:noWrap", "w:tcMar", "w:textDirection",
                                   "w:tcFitText", "w:vAlign", "w:hideMark")
    # 数据行**不写** tcBorders —— 让表格级边框生效，底线才会落在真正的最后一行


def _set_cell(doc, cell, text: str, bold: bool = False) -> None:
    p = cell.paragraphs[0]
    p.style = doc.styles["表格文字"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)   # 单一 run：占位符一行写完，避免被拆进多个 run 导致 docxtpl 渲染失败
    run.font.bold = bold


def add_three_line_table(doc, headers: list[str], sample_cells: list[str]):
    """加一张带 docxtpl 行循环的三线表。控件行（{%tr %}）渲染时会被整行删除。"""
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.style = doc.styles["三线表"]
    tbl.autofit = True
    for i, h in enumerate(headers):
        _set_cell(doc, tbl.rows[0].cells[i], h, bold=True)      # 表头
    _set_cell(doc, tbl.add_row().cells[0], "{%tr for row in rows %}")   # 循环开始（渲染时删行）
    data = tbl.add_row()
    for i, c in enumerate(sample_cells):
        _set_cell(doc, data.cells[i], c)                        # 数据样本行（按 rows 重复）
    _set_cell(doc, tbl.add_row().cells[0], "{%tr endfor %}")     # 循环结束（渲染时删行）
    three_line_table(tbl)
    return tbl


# ---------------------------------------------------------------------------
# 页面 / 页眉页脚
# ---------------------------------------------------------------------------
def setup_page(doc, top, bottom, left, right) -> None:
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)   # A4
    sec.top_margin, sec.bottom_margin = top, bottom
    sec.left_margin, sec.right_margin = left, right


def setup_header(doc, text: str, size: Pt = Pt(10.5)) -> None:
    sec = doc.sections[0]
    hdr = sec.header
    hdr.is_linked_to_previous = False
    p = hdr.paragraphs[0]
    p.text = text                       # p.text setter → 单一 run，占位符不会被拆
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    clear_indent(p)
    for r in p.runs:
        r.font.size = size
        set_run_fonts(r._r.get_or_add_rPr(), WEST, SONG)


def setup_footer_page(doc, cjk: str = SONG, ascii_font: str = WEST, size: Pt = Pt(10.5)) -> None:
    sec = doc.sections[0]
    ftr = sec.footer
    ftr.is_linked_to_previous = False
    p = ftr.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    clear_indent(p)
    add_page_field(p, cjk=cjk, ascii_font=ascii_font, size=size)


# ---------------------------------------------------------------------------
# 样式集合：三套模板共用 + 各自差异
# ---------------------------------------------------------------------------
def define_common_styles(doc) -> None:
    define_style(doc, "文档标题", cjk=HEI, size=Pt(18), bold=True,
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.5, space=6)
    define_style(doc, "目录标题", cjk=HEI, size=Pt(16), bold=True,
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.5, space=12)
    define_style(doc, "署名", cjk=SONG, size=Pt(12),
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.5)
    define_style(doc, "图注", cjk=SONG, size=Pt(10.5),
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.0, space=3)
    define_style(doc, "表注", cjk=SONG, size=Pt(10.5),
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.0, space=3)
    define_style(doc, "表格文字", cjk=SONG, size=Pt(10.5),
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=1.0)
    define_style(doc, "顶格", cjk=SONG, size=Pt(12), align=WD_ALIGN_PARAGRAPH.LEFT, line=1.5)
    define_style(doc, "落款", cjk=SONG, size=Pt(12), align=WD_ALIGN_PARAGRAPH.RIGHT, line=1.5)
    define_three_line_table_style(doc)


# ---------------------------------------------------------------------------
# 三套模板
# ---------------------------------------------------------------------------
def build_report(doc) -> None:
    """通用中文报告：A4，上下 2.54cm / 左右 3.17cm；宋体小四 1.5 倍行距首行缩进 2 字符；标题黑体；页眉 + 页码。"""
    configure_normal(doc, cjk=SONG, size=Pt(12), line=1.5, first_line_pt=24)
    configure_heading(doc, "Heading 1", Pt(16), cjk=HEI)   # 16 三号
    configure_heading(doc, "Heading 2", Pt(15), cjk=HEI)   # 15 小三
    configure_heading(doc, "Heading 3", Pt(14), cjk=HEI)   # 14 四号
    configure_heading(doc, "Heading 4", Pt(12), cjk=HEI)   # 12 小四
    define_common_styles(doc)
    setup_page(doc, Cm(2.54), Cm(2.54), Cm(3.17), Cm(3.17))
    setup_header(doc, "{{ header }}")
    setup_footer_page(doc)

    doc.add_paragraph("{{ title }}", style="文档标题")
    doc.add_paragraph("作者：{{ author }}　学号：{{ student_id }}　日期：{{ date }}", style="署名")
    doc.add_paragraph("摘要：{{ abstract }}")
    doc.add_paragraph("关键词：{{ keywords }}")
    doc.add_paragraph("1　正文", style="Heading 1")
    doc.add_paragraph("{{ body }}")
    doc.add_paragraph("1.1　数据表", style="Heading 2")
    doc.add_paragraph("表 1　{{ table_caption }}", style="表注")
    add_three_line_table(doc, ["序号", "直径 d / mm", "时间 t / s"],
                         ["{{ row.no }}", "{{ row.d }}", "{{ row.t }}"])
    doc.add_paragraph("{{ table_note }}", style="表注")
    img = doc.add_paragraph("{{ image }}")     # docxtpl InlineImage 占位
    img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    clear_indent(img)
    doc.add_paragraph("图 1　{{ figure_caption }}", style="图注")
    doc.add_paragraph("2　结论", style="Heading 1")
    doc.add_paragraph("{{ conclusion }}")


def build_gongwen(doc) -> None:
    """党政机关公文（GB/T 9704—2012）：A4；天头(上)37mm、订口(左)28mm；正文仿宋_GB2312 三号；
    一级标题黑体、二级楷体；页码 4 号半角宋体（无页眉）。"""
    # 版心 156×225mm：上 37 + 下 35 = 72；左 28 + 右 26 = 54 → 210-54=156、297-72=225 ✓
    configure_normal(doc, cjk=FANGSONG, size=Pt(16), line=Pt(29), first_line_pt=32)
    configure_heading(doc, "Heading 1", Pt(16), cjk=HEI, line=Pt(29))
    configure_heading(doc, "Heading 2", Pt(16), cjk=KAI, line=Pt(29))
    configure_heading(doc, "Heading 3", Pt(16), cjk=FANGSONG, line=Pt(29))
    configure_heading(doc, "Heading 4", Pt(16), cjk=FANGSONG, bold=False, line=Pt(29))
    define_common_styles(doc)
    define_style(doc, "公文标题", cjk=SONG, size=Pt(22), bold=True,
                 align=WD_ALIGN_PARAGRAPH.CENTER, line=Pt(29), space=6)   # 近似"二号小标宋"
    setup_page(doc, Mm(37), Mm(35), Mm(28), Mm(26))
    setup_footer_page(doc, cjk=SONG, ascii_font=SONG, size=Pt(14))        # 4 号半角宋体

    doc.add_paragraph("{{ title }}", style="公文标题")
    doc.add_paragraph("{{ recipient }}", style="顶格")     # 主送机关，顶格
    doc.add_paragraph("{{ body }}")                        # 正文：仿宋三号，首行缩进 2 字符
    doc.add_paragraph("附件：{{ attachment_caption }}", style="表注")
    add_three_line_table(doc, ["序号", "事项", "备注"],
                         ["{{ row.no }}", "{{ row.item }}", "{{ row.note }}"])
    doc.add_paragraph("{{ issuer }}", style="落款")
    doc.add_paragraph("{{ date }}", style="落款")


def build_thesis(doc) -> None:
    """学位论文（各校共性要求）：A4，上下 2.54cm / 左右 3.17cm；宋体小四 1.5 倍行距首行缩进 2 字符；
    标题黑体（各级字号递减）；页眉 + 页码 + 目录占位页。"""
    configure_normal(doc, cjk=SONG, size=Pt(12), line=1.5, first_line_pt=24)
    configure_heading(doc, "Heading 1", Pt(16), cjk=HEI)
    configure_heading(doc, "Heading 2", Pt(15), cjk=HEI)
    configure_heading(doc, "Heading 3", Pt(14), cjk=HEI)
    configure_heading(doc, "Heading 4", Pt(12), cjk=HEI)
    define_common_styles(doc)
    setup_page(doc, Cm(2.54), Cm(2.54), Cm(3.17), Cm(3.17))
    setup_header(doc, "{{ header }}")
    setup_footer_page(doc)

    doc.add_paragraph("{{ title }}", style="文档标题")
    doc.add_paragraph("作者：{{ author }}　学号：{{ student_id }}　导师：{{ advisor }}　日期：{{ date }}",
                      style="署名")
    doc.add_paragraph("摘　要", style="Heading 1")
    doc.add_paragraph("{{ abstract }}")
    doc.add_paragraph("关键词：{{ keywords }}")
    doc.add_page_break()
    doc.add_paragraph("目　录", style="目录标题")
    add_toc_field(doc)
    doc.add_page_break()
    doc.add_paragraph("第 1 章　绪论", style="Heading 1")
    doc.add_paragraph("{{ intro }}")
    doc.add_paragraph("1.1　研究背景", style="Heading 2")
    doc.add_paragraph("{{ background }}")
    doc.add_paragraph("表 1　{{ table_caption }}", style="表注")
    add_three_line_table(doc, ["序号", "指标", "数值"],
                         ["{{ row.no }}", "{{ row.item }}", "{{ row.value }}"])
    doc.add_paragraph("{{ table_note }}", style="表注")
    doc.add_paragraph("参考文献", style="Heading 1")
    doc.add_paragraph("{{ references }}")


# ---------------------------------------------------------------------------
def normalize_zip(path: Path) -> None:
    """把 .docx 的 zip 元数据规范成固定值，让重复生成得到【逐字节相同】的文件。

    为什么需要这一步：python-docx 写出的 zip 里，每个条目的时间戳是"当前时间"。
    于是即使内容完全一样，两次生成的字节也不同 —— 提交到 git 后，任何人重新
    跑一次这个脚本都会产生一堆无意义的 diff，模板就失去了"可复现"的意义。

    做法：读回所有条目，用固定的 date_time 与固定的压缩方式重新打包，
    并按名称排序保证顺序稳定。
    """
    FIXED = (1980, 1, 1, 0, 0, 0)   # zip 时间戳的最小合法值
    with zipfile.ZipFile(path) as src:
        items = sorted(src.namelist())
        blobs = {n: src.read(n) for n in items}
    tmp = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for name in items:
            info = zipfile.ZipInfo(name, date_time=FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16   # 固定权限位，避免随 umask 变化
            dst.writestr(info, blobs[name])
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 office-docs 技能用的中文 .docx 模板")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="输出目录（默认 templates/docx/）")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    builders = [
        ("report-zh.docx", build_report),
        ("gongwen-zh.docx", build_gongwen),
        ("thesis-zh.docx", build_thesis),
    ]
    print(f"输出目录: {out}")
    for fname, build in builders:
        doc = Document()
        build(doc)
        path = out / fname
        doc.save(str(path))      # 覆盖同名文件
        normalize_zip(path)      # 再规范 zip 元数据 → 真正幂等（字节级）
        print(f"  ✅ {fname:16} {path.stat().st_size:>7} bytes")
    print("完成。每个模板的占位符清单与用法见 templates/docx/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())