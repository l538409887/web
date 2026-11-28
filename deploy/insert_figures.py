# -*- coding: utf-8 -*-
"""把登录、注册、阅读设置三张截图插入第4章，并重排图号。"""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

DOC = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版.docx")
FIG = Path(r"E:\基于python的轻量化web小说平台\毕设内容\docs\figures")


def find_para(doc, prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    return None


def add_after(doc, anchor_el, kind, filename=None, text=None, width=15.0):
    """在指定元素之后插入图片段或题注段，返回新段落元素。"""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph

    if kind == "pic":
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(FIG / filename), width=Cm(width))
        anchor_el.addnext(p._element)
        return p._element
    else:
        p = doc.add_paragraph(text, style="Caption")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        anchor_el.addnext(p._element)
        return p._element


def renumber_ch4(doc):
    """把第4章内所有 图4-x 题注按文档顺序重新编号。"""
    n = 0
    for p in doc.paragraphs:
        if p.style.name != "Caption":
            continue
        text = p.text.strip()
        if not text.startswith("图4-"):
            continue
        n += 1
        # 取题注正文（"标题"部分）
        parts = text.split(" ", 1)
        title = parts[1] if len(parts) > 1 else ""
        new_text = f"图4-{n} {title}"
        for run in p.runs:
            run.text = ""
        if p.runs:
            p.runs[0].text = new_text
        else:
            p.text = new_text
    return n


def main():
    doc = Document(str(DOC))

    # ---- 1. 认证小节：登录、注册 ----
    anchor = find_para(doc, "鉴权通过FastAPI的依赖注入实现")
    if anchor is None:
        raise SystemExit("找不到 4.2 鉴权段落")

    el = anchor._element
    el = add_after(doc, el, "pic", filename="fig19_login.png")
    el = add_after(doc, el, "cap", text="图4-X 登录界面")
    el = add_after(doc, el, "pic", filename="fig18_register.png")
    el = add_after(doc, el, "cap", text="图4-X 注册界面")

    # 补一句正文说明
    ref = doc.add_paragraph("登录与注册界面如图4-X与图4-X所示，登录页同时提供演示账号提示，便于答辩演示。")
    el.addnext(ref._element)

    # ---- 2. 阅读器小节：阅读设置 ----
    anchor2 = find_para(doc, "每个段落右侧显示该段的间贴数量")
    if anchor2 is None:
        raise SystemExit("找不到 4.5 间贴段落")

    el2 = anchor2._element
    el2 = add_after(doc, el2, "pic", filename="fig17_reader_settings.png")
    el2 = add_after(doc, el2, "cap", text="图4-X 阅读设置界面")

    # ---- 3. 重排图号 ----
    total = renumber_ch4(doc)
    print(f"  第4章图题注共 {total} 个，已重排")

    # ---- 4. 修正正文中的占位引用：按最终编号替换 ----
    mapping = [
        ("如图4-X与图4-X所示", "如图4-1与图4-2所示"),
    ]
    for p in doc.paragraphs:
        for old, new in mapping:
            if old in p.text:
                for run in p.runs:
                    if old in run.text:
                        run.text = run.text.replace(old, new)

    doc.save(str(DOC))
    print("已保存：", DOC)


if __name__ == "__main__":
    main()
