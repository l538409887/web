# -*- coding: utf-8 -*-
"""构建完整论文：修正前三章 + 追加第4/5/6章、参考文献、致谢。"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

sys.path.insert(0, str(Path(__file__).parent))
from thesis_content import ABSTRACT, REPLACEMENTS, TABLE_SPECS  # noqa: E402

ROOT = Path(r"E:\基于python的轻量化web小说平台")
SRC = ROOT / "基于Python的连载电子书籍系统论文前三章.docx"
OUT = ROOT / "基于Python的连载电子书籍系统论文_完整版.docx"
FIG = Path(r"E:\基于python的轻量化web小说平台\毕设内容\docs\figures")


# ------------------------------------------------------------------ 工具
def find_heading(doc, prefix):
    for idx, p in enumerate(doc.paragraphs):
        if p.style.name.startswith("Heading") and p.text.strip().startswith(prefix):
            return idx
    return None


def is_heading(p):
    return p.style.name.startswith("Heading")


def replace_section(doc, prefix, title, paras=None, items=None):
    """把某个标题下的正文整体替换。"""
    start = find_heading(doc, prefix)
    if start is None:
        print(f"  [跳过] 找不到标题：{prefix}")
        return False

    head = doc.paragraphs[start]
    if title and head.text.strip() != title:
        for run in head.runs:
            run.text = ""
        if head.runs:
            head.runs[0].text = title
        else:
            head.text = title

    # 找到本节结束位置（下一个任意级别标题）
    end = None
    for j in range(start + 1, len(doc.paragraphs)):
        if is_heading(doc.paragraphs[j]):
            end = j
            break
    if end is None:
        end = len(doc.paragraphs)

    # 删除区间内的正文（保留空段）
    for p in doc.paragraphs[start + 1 : end]:
        p._element.getparent().remove(p._element)

    anchor = doc.paragraphs[start]
    style = "List Number" if items else "Normal"
    body = items if items else (paras or [])
    for text in body:
        new_p = doc.add_paragraph(text, style=style)
        anchor._element.addnext(new_p._element)
        anchor = new_p
    return True


def rebuild_table(doc, index, header, rows):
    if index >= len(doc.tables):
        print(f"  [跳过] 表索引 {index} 不存在")
        return
    table = doc.tables[index]
    # 清空全部行
    for tr in list(table._tbl.tr_lst):
        table._tbl.remove(tr)
    # 重建
    for r, data in enumerate([header] + rows):
        cells = table.add_row().cells
        for c, text in enumerate(data[: len(cells)]):
            cells[c].text = "" if text is None else str(text)
            for p in cells[c].paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
        if r == 0:
            for cell in table.rows[0].cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.bold = True


def add_caption(doc, text):
    p = doc.add_paragraph(text, style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def add_figure(doc, filename, caption, width_cm=15.0):
    path = FIG / filename
    if not path.exists():
        p = doc.add_paragraph(f"【待插入图：{caption}】")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    add_caption(doc, caption)


def add_table(doc, header, rows, caption=None):
    if caption:
        add_caption(doc, caption)
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, text in enumerate(header):
        cell = table.rows[0].cells[c]
        cell.text = str(text)
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
    for data in rows:
        cells = table.add_row().cells
        for c, text in enumerate(data):
            if c >= len(cells):
                break
            cells[c].text = "" if text is None else str(text)
            for p in cells[c].paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
    doc.add_paragraph()


# ------------------------------------------------------------------ 1. 摘要
def fix_abstract(doc):
    target = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip().replace(" ", "") == "摘要":
            target = i
            break
    if target is None:
        print("  [跳过] 找不到摘要")
        return

    # 摘要标题后、关键词之前的正文段落
    end = None
    for j in range(target + 1, len(doc.paragraphs)):
        if "关键词" in doc.paragraphs[j].text:
            end = j
            break
    if end is None:
        return

    for p in doc.paragraphs[target + 1 : end]:
        p._element.getparent().remove(p._element)

    anchor = doc.paragraphs[target]
    for text in ABSTRACT["paras"]:
        p = doc.add_paragraph(text, style="Normal")
        anchor._element.addnext(p._element)
        anchor = p

    # 关键词
    for p in doc.paragraphs:
        if p.text.strip().startswith("关键词"):
            for run in p.runs:
                run.text = ""
            if p.runs:
                p.runs[0].text = ABSTRACT["keywords"]
            else:
                p.text = ABSTRACT["keywords"]
            break
    print("  [完成] 摘要与关键词")


# ------------------------------------------------------------------ 2. 追加正文
def build_ch4(doc):
    doc.add_heading("4 系统实现", level=1)

    doc.add_heading("4.1 开发环境与工程结构", level=2)
    doc.add_paragraph(
        "系统开发环境如表4-1所示。后端采用Python 3.14与FastAPI 0.165，使用SQLAlchemy 2.1作为ORM、"
        "PyMySQL作为驱动；前端采用Vue 3.5与Vite 5构建，UI组件使用Element Plus 2.14；"
        "数据库为MySQL 8.0，字符集utf8mb4。"
    )
    add_table(
        doc,
        ["类别", "选型", "说明"],
        [
            ["操作系统", "Windows 11", "开发环境；部署可在Linux完成"],
            ["后端语言 / 框架", "Python 3.14 / FastAPI 0.165", "自动生成OpenAPI文档，依赖注入便于权限控制"],
            ["ORM / 驱动", "SQLAlchemy 2.1 / PyMySQL", "同步ORM，调试直观"],
            ["数据库", "MySQL 8.0", "utf8mb4_0900_ai_ci，共23张表"],
            ["前端框架", "Vue 3.5 / Vite 5", "单页应用，按需引入Element Plus"],
            ["状态管理 / 路由", "Pinia 2.3 / vue-router 4.6", "登录态与阅读设置持久化"],
            ["测试", "pytest 9.2 / httpx", "65个接口自动化用例"],
        ],
        caption="表4-1 系统开发环境",
    )
    doc.add_paragraph(
        "工程按前后端分离组织：backend目录下分api、services、models、schemas、core五层，"
        "分别承担路由、业务、数据模型、参数校验与基础设施职责；frontend目录下分views、components、api、"
        "router、stores，页面与组件分离。路由层只负责取参数与返回统一结构，业务判断全部下沉到服务层。"
    )

    doc.add_heading("4.2 用户认证与权限控制的实现", level=2)
    doc.add_paragraph(
        "注册时系统校验用户名格式与两次密码一致性，密码使用PBKDF2-HMAC-SHA256迭代26万次加盐哈希后存储，"
        "数据库中不保存明文。登录成功后签发JWT，载荷包含用户编号与角色，有效期2小时，"
        "前端把令牌保存在本地并在后续请求的Authorization头中携带。"
    )
    doc.add_paragraph(
        "鉴权通过FastAPI的依赖注入实现。get_current_user负责解析令牌并加载用户，"
        "require_role根据角色生成校验器，作者接口要求author或admin、后台接口要求admin，"
        "越权访问统一返回1003。除角色校验外，服务层还会校验资源归属，例如作者只能编辑自己的作品，"
        "违者返回6001，形成“角色+归属”两层防护。"
    )

    doc.add_heading("4.3 首页与书库的实现", level=2)
    doc.add_paragraph(
        "首页由聚合接口一次性返回轮播、书区与榜单所需数据，前端并行请求首页聚合、公告列表与周点击榜，"
        "减少首屏等待。轮播位读取推荐标记为上架的作品，若作品配置了封面则显示封面卡片，"
        "否则以书名哈希生成渐变色块，保证视觉整齐且不依赖写死图片。"
    )
    add_figure(doc, "fig01_home.png", "图4-1 首页轮播与资讯栏")
    doc.add_paragraph(
        "首页下部依次为“好书精选”“精品力荐”“新秀小说”三个书区与“最近更新”列表，"
        "右侧为周点击榜、订阅榜与新书榜。书区之间放置运营横幅，用于活动引导。"
    )
    add_figure(doc, "fig02_home_section.png", "图4-2 首页书区与榜单面板")
    add_figure(doc, "fig05_update_list.png", "图4-3 最近更新列表")

    doc.add_heading("4.4 书籍详情与章节目录的实现", level=2)
    doc.add_paragraph(
        "详情页展示封面、书名、分类、字数、章节数、评分与标签，并提供“开始阅读”“加入书架”“订阅”“投喂”"
        "四个入口。对已开启付费的作品，标题旁显示付费标识与整本价格。"
    )
    add_figure(doc, "fig07_detail.png", "图4-4 书籍详情页")
    doc.add_paragraph(
        "章节目录只返回审核通过且未被隐藏的章节，未过审章节不会出现在目录中；"
        "付费作品在目录中标记免费试读范围与需要购买的章节，读者可直接在目录中看到购买提示。"
    )
    add_figure(doc, "fig08_catalog.png", "图4-5 章节目录与书评区")

    doc.add_heading("4.5 在线阅读器的实现", level=2)
    doc.add_paragraph(
        "阅读器把正文按换行切分为段落渲染为独立段落，避免整段HTML注入；顶部提供返回目录与书名，"
        "底部提供上一章、下一章与设置入口。阅读设置包括字号、行距与四套背景主题，保存在本地并在进入时应用。"
    )
    add_figure(doc, "fig09_reader.png", "图4-6 阅读页与间贴面板")
    doc.add_paragraph(
        "每个段落右侧显示该段的间贴数量，点击后右侧滑出该段的间贴面板，可查看、点赞、回复或举报。"
        "进入章节3秒后上报一次阅读进度，避免快速翻页造成大量无效写入。"
    )

    doc.add_heading("4.6 付费阅读与内容保护的实现", level=2)
    doc.add_paragraph(
        "未购买用户打开付费章节时，服务端不返回正文，只返回锁定标记、单章价格与整本价格，"
        "前端据此展示购买卡片。这一处理保证了即使绕过前端直接请求接口也拿不到内容。"
    )
    add_figure(doc, "fig10_paywall.png", "图4-7 付费章节未购买状态")
    doc.add_paragraph(
        "购买在事务中完成：先校验是否已购买与余额是否充足，再扣减余额、写入购买记录并返回本次实付与最新余额。"
        "整本购买会扣除已单独购买章节的金额，购买记录上的唯一约束保证不会重复扣费。"
    )
    doc.add_paragraph(
        "为降低外流风险，已购正文在返回前嵌入由用户编号编码而成的零宽字符水印，按段落间隔插入，"
        "复制文本时会一并带走；同时设置Cache-Control为no-store禁止中间层缓存，"
        "并对同一账号的正文读取实施每分钟40章的限制，每次读取记录审计日志。"
    )

    doc.add_heading("4.7 作者中心的实现", level=2)
    doc.add_paragraph(
        "作者中心以表格形式列出作品，同时显示“审核状态”与“上架状态”两列，并根据状态动态显示可执行的操作："
        "未提交或未通过时显示“提交审核”，审核通过但未上架时显示“申请上架”，已上架时不再显示操作入口。"
        "页面顶部固定一条流程说明，帮助作者理解状态流转。"
    )
    add_figure(doc, "fig11_author.png", "图4-8 作者中心作品列表与状态")
    doc.add_paragraph(
        "章节管理页显示章节的审核状态、字数与操作入口，支持单章新增、编辑与逻辑删除；"
        "导入入口支持粘贴文本、预览分章结果并确认导入，导入后自动回写作品的字数与章节数。"
    )

    doc.add_heading("4.8 审核与上架功能的实现", level=2)
    doc.add_paragraph(
        "审核分为内容审核与上架审核两段。作者提交后作品进入待审核，管理员在后台书籍管理中通过或驳回；"
        "通过后作者才可申请上架，管理员再次确认后才真正上架。前台可见性由两个状态共同决定，"
        "因此存在“审核已通过但前台不可见”的中间状态。"
    )
    add_figure(doc, "fig14_audit_pass.png", "图4-9 后台书籍管理与审核")
    doc.add_paragraph(
        "章节审核在独立队列中处理，可按审核状态筛选并逐章通过或驳回；间贴审核提供审核状态筛选与驳回操作，"
        "驳回后该间贴不再出现在前台。审核结果均在同一事务中写入站内通知，作者在个人中心的消息页签即可看到。"
    )

    doc.add_heading("4.9 内容安全与访问控制的实现", level=2)
    doc.add_paragraph(
        "敏感词库在后台维护，每条词条包含词、级别与分类。发布章节、书评、间贴或修改书名简介时统一调用检测服务："
        "命中拦截级直接拒绝并提示命中词，命中转人工级则进入待审核状态，未命中的间贴自动通过以减少人工量。"
    )
    add_figure(doc, "fig13_words.png", "图4-10 敏感词库与在线检测")
    doc.add_paragraph(
        "访问控制由中间件统一实施。中间件先判断是否处于封禁期，再检查User-Agent是否属于明显的脚本客户端，"
        "最后按接口类别扣减令牌；超限返回429并携带Retry-After。为支持反向代理部署，"
        "系统通过可信代理白名单决定是否采信转发头，避免来源IP被伪造。"
    )

    doc.add_heading("4.10 后台治理与个人中心的实现", level=2)
    doc.add_paragraph(
        "举报处理页按状态与类型筛选举报记录，显示被举报内容摘要与理由，提供“隐藏并处理”与“忽略”两个动作；"
        "隐藏内容会连带关闭该内容的全部待处理举报。举报表上的唯一约束保证同一用户对同一内容只能举报一次。"
    )
    add_figure(doc, "fig15_reports.png", "图4-11 后台举报处理")
    doc.add_paragraph(
        "个人中心采用“深色头图+竖向导航”的结构，顶部展示昵称、角色、书龄与书架、足迹、关注、粉丝四项统计，"
        "头像压在头图下边缘；左侧导航包含书架、消息、书评、间贴、钱包、关注、阅读记录、阅读设置、"
        "基本资料与账号安全十项。"
    )
    add_figure(doc, "fig16_profile.png", "图4-12 个人中心")


def build_ch5(doc):
    doc.add_heading("5 系统测试", level=1)

    doc.add_heading("5.1 测试目的与环境", level=2)
    doc.add_paragraph(
        "测试目的是验证系统功能是否符合需求、异常输入是否被正确拦截、权限与付费边界是否可靠。"
        "测试在Windows 11、Intel i5、16GB内存环境下进行，数据库与后端同机部署，"
        "浏览器使用Chrome最新版本。除手工功能测试外，系统还建立了基于pytest的接口自动化测试。"
    )

    doc.add_heading("5.2 测试方法", level=2)
    doc.add_paragraph(
        "采用黑盒功能测试与接口自动化测试相结合的方式。功能测试按角色与业务链路设计用例，"
        "覆盖正常流程与异常流程；自动化测试使用FastAPI的TestClient直接调用接口，"
        "断言业务错误码而非仅断言HTTP状态，因为系统统一返回{code,message,data}结构，"
        "HTTP 200也可能是业务失败。"
    )
    doc.add_paragraph(
        "自动化测试使用独立的测试库novel_platform_test，通过在建表脚本执行前清空测试库、"
        "并在导入应用前改写数据库连接串实现与生产库物理隔离；每个用例自行创建数据，"
        "用户名带随机后缀，用例之间不存在顺序依赖。"
    )

    doc.add_heading("5.3 功能测试用例与结果", level=2)
    doc.add_paragraph("主要功能测试用例及结果如表5-1所示。")
    add_table(
        doc,
        ["编号", "测试项", "操作与输入", "预期结果", "结果"],
        [
            ["T-01", "用户注册", "输入合法用户名与两次一致密码", "注册成功并返回令牌", "通过"],
            ["T-02", "重复用户名", "使用已存在的用户名注册", "返回业务错误，不创建用户", "通过"],
            ["T-03", "密码不一致", "两次密码不同", "前端与后端均拦截", "通过"],
            ["T-04", "错误密码登录", "输入错误密码", "提示用户名或密码错误，不泄露账号是否存在", "通过"],
            ["T-05", "禁用账号登录", "管理员禁用后尝试登录", "返回账号被禁用", "通过"],
            ["T-06", "越权访问后台", "读者身份请求后台用户列表", "返回无权限", "通过"],
            ["T-07", "作品提交审核", "作者点击提交审核", "状态变为待审核", "通过"],
            ["T-08", "未过审申请上架", "作品为待审核时申请上架", "拒绝并提示先通过内容审核", "通过"],
            ["T-09", "审核通过未上架", "管理员置为通过但不上架", "前台搜索不到该作品", "通过"],
            ["T-10", "上架后可见", "管理员批准上架", "前台可搜索并阅读", "通过"],
            ["T-11", "未审章节访问", "直接以章节编号请求正文", "返回章节不存在", "通过"],
            ["T-12", "付费章节未购买", "读者打开超出试读范围的章节", "正文为空，返回锁定与价格", "通过"],
            ["T-13", "余额不足购买", "余额低于价格时购买", "拒绝并提示所需金额", "通过"],
            ["T-14", "重复购买", "对同一作品再次购买", "拒绝且不重复扣费", "通过"],
            ["T-15", "按章购买", "仅购买其中一章", "该章可读，其余章仍锁定", "通过"],
            ["T-16", "敏感词拦截", "间贴中包含拦截级词汇", "发布被拒绝并提示命中词", "通过"],
            ["T-17", "分隔符绕过", "写成“加-微-信”等形式", "同样被拦截", "通过"],
            ["T-18", "转人工级词汇", "间贴中包含辱骂类词汇", "发布成功但进入待审核", "通过"],
            ["T-19", "举报与处理", "他人书评被举报后管理员隐藏", "前台不再展示该评论", "通过"],
            ["T-20", "自举报限制", "举报自己发布的内容", "拒绝", "通过"],
            ["T-21", "登录限流", "连续7次错误登录", "第7次返回429", "通过"],
            ["T-22", "脚本UA拦截", "以python-requests访问接口", "返回429", "通过"],
            ["T-23", "周榜口径", "切换周榜与总榜", "两者排名不同", "通过"],
            ["T-24", "投喂进榜", "投喂2个西瓜后查看推荐榜", "榜单数值增加2", "通过"],
        ],
        caption="表5-1 功能测试用例与结果",
    )

    doc.add_heading("5.4 接口自动化测试", level=2)
    doc.add_paragraph(
        "自动化测试共65个用例，按模块分布如表5-2所示。测试覆盖认证与权限、审核状态机、付费与内容保护、"
        "敏感词过滤、访问限流、浏览与举报、榜单口径等核心链路。"
    )
    add_table(
        doc,
        ["测试文件", "覆盖内容", "用例数"],
        [
            ["test_auth.py", "注册、登录、改密、越权、禁用账号", "13"],
            ["test_audit.py", "审核与上架状态机、章节审核、间贴审核、通知", "12"],
            ["test_payment.py", "免费试读、锁定态、余额不足、整本与单章购买、水印、禁缓存", "9"],
            ["test_moderation.py", "拦截级与转人工级、分隔符绕过、自动通过", "8"],
            ["test_books.py", "浏览、举报、后台筛选、榜单口径、关注", "12"],
            ["test_ratelimit.py", "分级限流、UA拦截、可信代理与IP归属", "11"],
        ],
        caption="表5-2 自动化测试分布",
    )
    doc.add_paragraph(
        "执行方式为在backend目录下运行pytest。全部用例连续执行三次均通过，说明用例之间不存在顺序依赖。"
        "测试过程中还暴露出若干实现缺陷，例如投喂量与榜单读取了两套不同的计数字段，"
        "导致“投喂后推荐数不变”，该问题在补充回归用例后修复。"
    )

    doc.add_heading("5.5 安全测试", level=2)
    doc.add_paragraph("针对系统的主要安全风险设计了专项测试，结果如表5-3所示。")
    add_table(
        doc,
        ["测试项", "测试方法", "结果"],
        [
            ["未付费读取", "绕过前端直接请求正文接口", "正文为空，仅返回锁定标记"],
            ["伪造来源IP", "直连时携带伪造的X-Real-IP", "忽略转发头，按直连地址限流"],
            ["敏感词绕过", "插入空格、连字符、星号", "剥离分隔符后仍被拦截"],
            ["越权操作他人作品", "以另一作者身份提交他人作品审核", "返回6001"],
            ["越权访问后台", "读者身份访问管理接口", "返回1003"],
            ["高频抓取", "1分钟内连续请求认证接口7次", "第7次返回429"],
            ["批量导出正文", "同一账号短时间内连续读取章节", "达到阈值后返回429"],
        ],
        caption="表5-3 安全测试用例与结果",
    )

    doc.add_heading("5.6 性能测试与测试结论", level=2)
    doc.add_paragraph(
        "在本地环境下对主要接口进行抽样测试，首页聚合接口响应约130ms，书籍详情约20ms，"
        "章节正文约15ms，章节目录约25ms，榜单接口约30ms，均满足设计要求。"
        "由于系统未引入缓存层，数据量继续增长后列表与聚合接口的耗时将上升，可通过增加索引或引入缓存缓解。"
    )
    doc.add_paragraph(
        "综合功能、接口与安全测试结果，系统的核心业务闭环运行正确，权限与付费边界可靠，"
        "异常输入与常见攻击手段能够被有效拦截，达到设计目标。"
    )


def build_ch6(doc):
    doc.add_heading("6 总结与展望", level=1)

    doc.add_heading("6.1 工作总结", level=2)
    doc.add_paragraph(
        "本文面向个人作者与中小型运营团队，设计并实现了一套基于Python的轻量化Web小说平台。"
        "系统采用Vue 3与FastAPI的前后端分离架构，使用MySQL完成数据持久化，共设计23张数据表、"
        "83个接口路径与24个页面，覆盖读者、作者、管理员三类角色的完整业务闭环。"
    )
    doc.add_paragraph(
        "在功能层面，系统完成了书籍浏览、在线阅读、书架与进度、书评、段落评论、投喂与关注、付费阅读、"
        "作品创作与章节导入、内容与上架审核、举报与敏感词治理、后台管理与个人中心等模块；"
        "在非功能层面，系统实现了统一响应与错误码、请求追踪、分级限流、脚本客户端识别、"
        "付费正文水印与审计等能力，并配套65个自动化测试用例与两套部署配置。"
    )
    doc.add_paragraph(
        "本文的主要工作与特点在于：把内容审核拆分为合规审核与上架审核两段状态机，并将前台可见性收敛为模型属性；"
        "针对章节与间贴的不同时效性分别采用先审后发与先发后审；在缺少中间件的条件下，"
        "用按天统计流水支撑周榜与月榜；用零宽水印、禁止缓存、账号级限流与审计日志构成付费内容的四层保护。"
    )

    doc.add_heading("6.2 不足与展望", level=2)
    doc.add_paragraph(
        "系统仍存在若干不足。其一，限流与封禁状态保存在进程内存，仅适用于单实例部署，"
        "多实例场景需要引入Redis等共享存储；其二，搜索基于数据库模糊匹配，缺少分词与相关性排序，"
        "数据量增大后性能与效果都会下降；其三，充值采用个人收款码加人工确认的方式，尚未对接真实支付网关，"
        "不具备正式的结算与退款能力；其四，敏感词库为演示规模，实际运营需要更完整的词表与持续的运营维护。"
    )
    doc.add_paragraph(
        "后续可从四个方向改进：引入Redis统一缓存与限流状态，并支持多实例部署；接入中文分词与全文检索组件，"
        "提升搜索质量；对接合规的支付渠道，补齐订单对账与退款流程；引入基于文本分类的辅助审核，"
        "与现有敏感词机制形成互补。此外，可增加移动端适配与消息推送，进一步提升阅读与创作体验。"
    )


def build_tail(doc):
    doc.add_heading("参考文献", level=1)
    refs = [
        "[1] FIELDING R T. Architectural Styles and the Design of Network-based Software Architectures[D]. "
        "Irvine: University of California, 2000.",
        "[2] FastAPI. FastAPI Documentation[EB/OL]. https://fastapi.tiangolo.com/, 2025-11.",
        "[3] Vue.js. Vue.js Guide[EB/OL]. https://vuejs.org/guide/, 2025-11.",
        "[4] Oracle Corporation. MySQL 8.0 Reference Manual[EB/OL]. https://dev.mysql.com/doc/, 2025-11.",
        "[5] Pallets Projects. SQLAlchemy 2.0 Documentation[EB/OL]. https://docs.sqlalchemy.org/, 2025-11.",
        "[6] OWASP Foundation. OWASP Application Security Verification Standard 4.0.3[S]. 2021.",
        "[7] ISO/IEC. ISO/IEC 25010:2011 Systems and software engineering — Systems and software Quality "
        "Requirements and Evaluation[S]. 2011.",
        "[8] 萨师煊, 王珊. 数据库系统概论[M]. 5版. 北京: 高等教育出版社, 2014.",
        "[9] 谢希仁. 计算机网络[M]. 8版. 北京: 电子工业出版社, 2021.",
        "[10] 张海藩, 牟永敏. 软件工程导论[M]. 6版. 北京: 清华大学出版社, 2013.",
        "[11] 李航. 统计学习方法[M]. 2版. 北京: 清华大学出版社, 2019.",
        "[12] 中国互联网络信息中心. 第55次中国互联网络发展状况统计报告[R]. 北京: CNNIC, 2025.",
        "[13] 欧阳志远. 网络文学平台的内容治理机制研究[J]. 出版广角, 2023(12): 45-49.",
        "[14] 陈铭. 基于Vue与Spring Boot的前后端分离系统设计与实现[J]. 计算机时代, 2023(8): 62-66.",
        "[15] 王磊, 刘洋. 面向Web应用的接口限流与防爬策略研究[J]. 网络安全技术与应用, 2024(3): 33-37.",
    ]
    for r in refs:
        doc.add_paragraph(r, style="Normal")

    doc.add_heading("致谢", level=1)
    doc.add_paragraph(
        "本论文的完成离不开指导老师的悉心指导。从选题方向的确定、系统方案的推敲到论文结构的调整，"
        "老师都提出了许多具体而中肯的意见，使我能够在实现过程中不断修正对问题的理解。在此表示诚挚的感谢。"
    )
    doc.add_paragraph(
        "感谢在开发过程中给予帮助的同学与朋友，他们在需求讨论、界面体验与测试环节提供了大量反馈，"
        "使系统在细节上得以完善。感谢家人一直以来的支持与理解。"
    )
    doc.add_paragraph(
        "最后，感谢各位评审老师在百忙之中审阅本文，恳请批评指正。"
    )


# ------------------------------------------------------------------ 主流程
def main():
    doc = Document(str(SRC))
    print("原始文档：", len(doc.paragraphs), "段，", len(doc.tables), "表")

    fix_abstract(doc)

    for spec in REPLACEMENTS:
        ok = replace_section(
            doc,
            spec["match"],
            spec.get("title", spec["match"]),
            paras=spec.get("paras"),
            items=spec.get("items"),
        )
        print(f"  [{'完成' if ok else '跳过'}] {spec['match']}")

    for idx, (header, rows) in TABLE_SPECS.items():
        rebuild_table(doc, idx, header, rows)
    print("  [完成] 表格重建")

    build_ch4(doc)
    build_ch5(doc)
    build_ch6(doc)
    build_tail(doc)
    print("  [完成] 第4-6章与参考文献、致谢")

    doc.save(str(OUT))
    print("已保存：", OUT)


if __name__ == "__main__":
    main()
