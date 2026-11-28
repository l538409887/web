from pathlib import Path
from docx import Document

DOC = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版.docx")
ALT = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版_v3.docx")

NEW = ("章节管理页采用左右分栏：左侧列出章节序号、标题、审核状态与删除入口，"
       "右侧为写作区，上方填写章节名（留空时按序号自动命名为「第N章」），下方为正文编辑区。"
       "写作区底部提供「暂存草稿」与「提交审核」两个动作：草稿不校验敏感词、不进入审核队列、"
       "前台不可见，适合分次写作；确认无误后再提交审核。本章节支持单章新增、编辑与逻辑删除；")

doc = Document(str(DOC))
hit = False
for p in doc.paragraphs:
    if p.text.strip().startswith("章节管理页显示章节的审核状态"):
        for r in p.runs:
            r.text = ""
        if p.runs:
            p.runs[0].text = NEW
        else:
            p.text = NEW
        hit = True
        break

try:
    doc.save(str(DOC))
    print("已更新:", hit)
except PermissionError:
    doc.save(str(ALT))
    print("原文件被占用，另存为:", ALT.name, "| 更新:", hit)