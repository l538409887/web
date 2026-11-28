# -*- coding: utf-8 -*-
"""重建第1-3章：删除旧正文，写入对齐实际系统的新内容，并重建目录。"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

sys.path.insert(0, str(Path(__file__).parent))
from thesis_ch12 import CH12  # noqa: E402
from thesis_ch3 import CH3  # noqa: E402

ROOT = Path(r"E:\基于python的轻量化web小说平台")
DOC = ROOT / "基于Python的连载电子书籍系统论文_完整版.docx"
FIG = Path(r"E:\基于python的轻量化web小说平台\毕设内容\docs\figures")


def h1(doc, text):
    return doc.add_heading(text, level=1)


def h2(doc, text):
    return doc.add_heading(text, level=2)


def h3(doc, text):
    return doc.add_heading(text, level=3)


def para(doc, text, style="Normal"):
    return doc.add_paragraph(text, style=style)


def caption(doc, text):
    p = doc.add_paragraph(text, style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def figure(doc, filename, cap):
    path = FIG / filename
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if path.exists():
        p.add_run().add_picture(str(path), width=Cm(15.0))
    else:
        p.add_run(f"【图缺失：{filename}】")
    cap_p = caption(doc, cap)
    return [p, cap_p]


def table(doc, cap, header, rows):
    cap_p = caption(doc, cap)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, text in enumerate(header):
        cell = t.rows[0].cells[c]
        cell.text = str(text)
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for data in rows:
        cells = t.add_row().cells
        for c, text in enumerate(data):
            if c >= len(cells):
                break
            cells[c].text = "" if text is None else str(text)
            for p in cells[c].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    return [cap_p, t]


def render(doc, blocks):
    """把内容块渲染到文档末尾，返回新元素列表。"""
    made = []
    for block in blocks:
        kind = block[0]
        if kind == "h1":
            made.append(h1(doc, block[1]))
        elif kind == "h2":
            made.append(h2(doc, block[1]))
        elif kind == "h3":
            made.append(h3(doc, block[1]))
        elif kind == "p":
            made.append(para(doc, block[1]))
        elif kind == "items":
            for text in block[1]:
                made.append(para(doc, text, style="List Number"))
        elif kind == "fig":
            made.extend(figure(doc, block[1], block[2]))
        elif kind == "table":
            made.extend(table(doc, block[1], block[2], block[3]))
        else:
            raise ValueError(kind)
    return made


def extract_old_figures(doc):
    """把旧第3章中的三张架构图另存为新文件，供重建时复用。"""
    saved = []
    i = 0
    while i < 3:
        try:
            shape = doc.inline_shapes[i]
        except (IndexError, KeyError):
            break
        i += 1
        try:
            blip = shape._inline.graphic.graphicData.pic.blipFill.blip
            rid = blip.embed
            blob = doc.part.related_parts[rid].blob
            target = FIG / f"fig3_{i}.png"
            target.write_bytes(blob)
            saved.append(target)
        except Exception as exc:  # noqa: BLE001
            print(f"  图{i} 提取失败：{exc}")
    return saved


def find_h1(doc, prefix):
    for p in doc.paragraphs:
        if p.style.name == "Heading 1" and p.text.strip().startswith(prefix):
            return p
    return None


def delete_between(doc, start_el, end_el):
    body = doc.element.body
    children = list(body.iterchildren())
    if start_el not in children or end_el not in children:
        return 0
    i, j = children.index(start_el), children.index(end_el)
    removed = 0
    for el in children[i:j]:
        body.remove(el)
        removed += 1
    return removed


def insert_before(doc, anchor_el, elements):
    for el in elements:
        anchor_el.addprevious(el)


def build_toc(doc):
    """把旧的文字目录替换为可更新的域目录。"""
    toc_head = None
    for p in doc.paragraphs:
        if p.text.strip().replace(" ", "") in ("目录", "目 录"):
            toc_head = p
            break
    if toc_head is None:
        print("  [跳过] 找不到目录标题")
        return

    # 删除目录标题之后的全部段落，直到第一个 Heading 1
    body = doc.element.body
    children = list(body.iterchildren())
    start_i = children.index(toc_head._element)
    end_i = None
    for k in range(start_i + 1, len(children)):
        el = children[k]
        if el.tag.endswith("}p"):
            from docx.text.paragraph import Paragraph

            p = Paragraph(el, doc)
            if p.style.name == "Heading 1":
                end_i = k
                break
    if end_i is None:
        return
    for el in children[start_i + 1 : end_i]:
        body.remove(el)

    # 插入 TOC 域
    p = OxmlElement("w:p")
    r1 = OxmlElement("w:r")
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    r1.append(fld1)

    r2 = OxmlElement("w:r")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r' TOC \o "1-3" \h \z \u '
    r2.append(instr)

    r3 = OxmlElement("w:r")
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "separate")
    r3.append(fld2)

    r4 = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "（在此处右键选择“更新域”生成目录）"
    r4.append(t)

    r5 = OxmlElement("w:r")
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "end")
    r5.append(fld3)

    for r in (r1, r2, r3, r4, r5):
        p.append(r)

    toc_head._element.addnext(p)
    print("  [完成] 目录已替换为域，可在 Word 中更新")


def main():
    doc = Document(str(DOC))
    print("载入：", len(doc.paragraphs), "段，", len(doc.tables), "表")

    saved = extract_old_figures(doc)
    print("  复用旧架构图：", [p.name for p in saved])

    first_h1 = find_h1(doc, "1 绪论")
    ch4_h1 = find_h1(doc, "4 系统实现")
    if first_h1 is None or ch4_h1 is None:
        raise SystemExit("定位章节失败")

    removed = delete_between(doc, first_h1._element, ch4_h1._element)
    print(f"  删除旧第1-3章元素：{removed}")

    blocks = CH12 + CH3
    made = render(doc, blocks)
    print(f"  生成新内容元素：{len(made)}")

    # 移动到第4章之前，保持顺序
    anchor = ch4_h1._element
    for el in made:
        target = el._element if hasattr(el, "_element") else el
        anchor.addprevious(target)

    build_toc(doc)

    doc.save(str(DOC))
    print("已保存：", DOC)


if __name__ == "__main__":
    main()
