# -*- coding: utf-8 -*-
"""替换参考文献中三条虚构条目为可查证的文献。"""
from pathlib import Path
from docx import Document

DOC = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版.docx")
OUT = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版_v2.docx")

NEW = {
    13: "[13] 赵礼寿, 杨佚琳, 王梦颖. 加强网络文学管理，提高网络文学精品产出率[J]. 出版广角, 2023(13).",
    14: "[14] 霍春阳. Vue.js设计与实现[M]. 北京: 人民邮电出版社, 2022.",
    15: "[15] RFC 6585. Additional HTTP Status Codes[S]. Internet Engineering Task Force, 2012.",
}


def main():
    doc = Document(str(DOC))
    changed = 0
    for para in doc.paragraphs:
        text = para.text.strip()
        for idx, new_text in NEW.items():
            if text.startswith(f"[{idx}]"):
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = new_text
                else:
                    para.text = new_text
                changed += 1
                break
    try:
        doc.save(str(DOC))
    except PermissionError:
        doc.save(str(OUT))
        print("原文件被占用，已另存为：", OUT.name)
    print(f"已替换 {changed} 条参考文献")


if __name__ == "__main__":
    main()