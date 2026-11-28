# -*- coding: utf-8 -*-
"""在中文摘要与关键词之后插入英文摘要。"""
from pathlib import Path
from docx import Document

DOC = Path(r"E:\基于python的轻量化web小说平台\基于Python的连载电子书籍系统论文_完整版.docx")

ABSTRACT_EN = [
    "Traditional online literature sites mostly adopt a centralized content production model, in which readers "
    "can only read passively and lack paragraph-level interaction and a complete creation loop. Lightweight "
    "platforms aimed at individual authors and small operation teams often compromise on content governance, "
    "paid-content protection and back-office review. To address this contradiction, this thesis designs and "
    "implements a lightweight web novel platform based on Python, covering the whole chain of reading, writing, "
    "reviewing and operating with low technical complexity.",

    "The system adopts a front-end and back-end separated B/S architecture. The front end is a single-page "
    "application built with Vue 3 and Element Plus; the back end provides RESTful APIs with Python and FastAPI; "
    "data is persisted in MySQL 8.0, with 23 tables and 83 API paths. Three roles—reader, author and "
    "administrator—are defined, and functions include home aggregation, book details, chapter reading, bookshelf "
    "and reading progress, book reviews, paragraph comments, watermelon tipping, author following, paid reading "
    "and a personal center for readers; work management, chapter import and segmentation, review submission and "
    "shelf application for authors; and book and chapter review, paragraph-comment moderation, report handling, "
    "sensitive-word management, comment management, user management, notices and order management for administrators.",

    "Several key designs are proposed. A two-stage state machine separates content review from shelf review, and "
    "front-end visibility is consolidated into a hybrid attribute of the model. Chapters are reviewed before "
    "publication while paragraph comments are published before review, according to their different timeliness. "
    "Paid chapters are controlled by the server and embedded with zero-width watermark, combined with no-store "
    "caching, account-level rate limiting and read auditing. Content is filtered by two-level sensitive words with "
    "separator stripping to prevent bypassing; APIs are protected by class-based token-bucket rate limiting and "
    "script-client identification; weekly and monthly rankings are supported by daily statistics. The system is "
    "accompanied by 65 automated test cases and two deployment configurations.",

    "Test results show that the core business processes work correctly and all 61 interface test cases pass. "
    "Unauthorized access, unpaid reading, sensitive-word bypassing and high-frequency crawling are correctly "
    "intercepted. The work provides a reference for the lightweight implementation of small and medium-sized "
    "online literature platforms.",
]

KEYWORDS_EN = ("Key words: lightweight platform; FastAPI; Vue.js; MySQL; content review; "
               "paid reading; paragraph comment; rate limiting")


def main():
    doc = Document(str(DOC))

    anchor = None
    for p in doc.paragraphs:
        if p.text.strip().startswith("关键词"):
            anchor = p
            break
    if anchor is None:
        raise SystemExit("找不到关键词段落")

    # 在关键词之后插入：空段、Abstract 标题、正文、Key words
    made = []
    made.append(doc.add_heading("Abstract", level=1))
    for text in ABSTRACT_EN:
        made.append(doc.add_paragraph(text, style="Normal"))
    made.append(doc.add_paragraph(KEYWORDS_EN, style="Normal"))

    prev = anchor._element
    for el in made:
        prev.addnext(el._element)
        prev = el._element

    doc.save(str(DOC))
    print("已插入英文摘要，段落数：", len(doc.paragraphs))


if __name__ == "__main__":
    main()