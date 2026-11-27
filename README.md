# 基于 Python 的轻量化 Web 小说平台

> 本科毕业设计 · 前后端分离的小说阅读平台
> 参考产品形态：起点中文网 / 刺猬猫阅读 / 纵横中文网

---

## 一、项目速览

| 项 | 内容 |
|---|---|
| 项目代号 | `novel_platform` |
| 中文名 | 轻量化小说平台 |
| 系统形态 | 前后端分离的 B/S 架构 Web 应用 |
| 后端 | Python 3.14 / FastAPI / SQLAlchemy 2.1 / PyMySQL |
| 前端 | Vue 3 / Vite / Vue Router / Pinia / Element Plus / Axios |
| 数据库 | MySQL 8.0（utf8mb4） |
| 认证 | JWT（Bearer Token）+ RBAC 三角色 |
| 部署 | Nginx（静态资源 + 反向代理）/ Uvicorn / MySQL |
| 文档 | 见下方「文档索引」 |
| 测试 | **61 个自动化用例**（pytest），见 [SETUP.md](SETUP.md) 第七节 |
| 部署 | 提供单机（Nginx + systemd）与 Docker Compose 两套方案，见 [deploy/README.md](deploy/README.md) |
| 当前规模 | **83 个接口路径（98 个操作）/ 23 张表 / 24 个页面（前台 11 + 作者 2 + 后台 11）/ 17 个公共组件** |
| 当前阶段 | **P4 完成**：读者端、作者端、后台三端闭环，含付费订阅、间贴、关注、充值（人工确认） |

---

## 二、文档索引

| 编号 | 文档 | 作用 | 对应论文章节 |
|---|---|---|---|
| 01 | [需求规格说明书](docs/01-需求规格说明书.md) | 角色、用例、功能分级、验收标准 | 第 2 章 需求分析 |
| 02 | [系统设计说明书](docs/02-系统设计说明书.md) | 架构、技术选型、分层、目录、时序 | 第 3 章 系统设计 |
| 03 | [数据库设计说明书](docs/03-数据库设计说明书.md) | ER 图、表结构、索引、冗余策略 | 第 3.3 节 数据库设计 |
| 04 | [接口文档](docs/04-接口文档.md) | RESTful API 契约、响应格式、错误码 | 第 4 章 详细设计 |
| 05 | [前端设计说明书](docs/05-前端设计说明书.md) | 页面地图、路由、组件、交互 | 第 4 章 详细设计 |
| 06 | [开发规范](docs/06-开发规范.md) | 命名、目录、Git、代码风格 | 附录 |
| 07 | [日志与可观测性规范](docs/07-日志与可观测性规范.md) | 应用日志、请求追踪、审计日志 | 第 4.x 节 日志设计 |
| 08 | [答辩演示脚本](docs/08-答辩演示脚本.md) | 演示前准备、分幕脚本、杀手点、常见追问 | 答辩现场 |
| 09 | [源码阅读路线](docs/09-源码阅读路线.md) | 代码地图、阅读顺序、调试手段、练手任务 | 开发与维护 |

> **03 与 04 是自动生成的**，改完表结构或接口后请重新生成，不要手工编辑：
>
> ```bash
> cd backend
> .venv\Scripts\python.exe scripts\gen_docs.py
> ```
>
> 脚本从 `information_schema` 读表结构与索引、从 `openapi.json` 读接口清单，
> 叙述性章节（状态约定、冗余策略、错误码）固化在脚本里，重新生成不会丢。
| — | [DEVLOG](DEVLOG.md) | 开发日志（**改代码前先写这里**） | — |

> 建议阅读顺序：`01 → 03 → 04 → 05 → 02 → 06 → 07`。
> 原因：先想清楚「做什么」和「数据长什么样」，再想「接口怎么给」，最后才是「架构怎么分层」。

---

## 三、目录结构

```
毕设内容/
├── README.md
├── DEVLOG.md                    # 开发日志（改代码前先写这里）
├── .gitignore
├── docs/                        # 设计文档 01~07
├── db/
│   ├── 00_create_user.sql       # 建库 + 最小权限账号 novel_app
│   ├── schema.sql               # 建表（23 张）
│   ├── seed.sql                 # 首批演示数据（12 本书）
│   ├── demo_extra_books.sql     # 补充 10 本书（首页三个书区需要）
│   └── migrations/              # 增量升级脚本 001~006
│       ├── 001_wallet.sql               # 签到 / 充值
│       ├── 002_paid_watermelon_paragraph.sql  # 付费 / 西瓜 / 间贴
│       ├── 003_chapter_purchase.sql     # 按章购买
│       ├── 004_paragraph_reply.sql      # 间贴回复
│       ├── 005_site_notice.sql          # 站点公告
│       └── 006_author_follow.sql        # 作者关注
├── backend/
│   ├── .env.example             # 环境变量模板（复制为 .env）
│   ├── requirements.txt
│   ├── main.py                  # 应用入口
│   ├── scripts/
│   │   └── check_service_refs.py  # 静态自检：service 调用是否都存在
│   ├── static/                  # 上传目录（封面 / 头像 / 收款码）
│   ├── app/
│   │   ├── core/                # 配置、安全、日志、异常、响应
│   │   ├── models/              # SQLAlchemy ORM
│   │   ├── schemas/             # Pydantic 请求/响应
│   │   ├── api/v1/              # 路由层（18 个模块）
│   │   ├── services/            # 业务逻辑层（13 个模块）
│   │   └── utils/               # 分章、字数统计
│   └── logs/                    # 运行日志（git 忽略）
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── public/
    │   └── banners/             # 首页轮播插画 b1~b5.jpg
    └── src/
        ├── main.js
        ├── router/              # 路由 + 角色守卫
        ├── stores/              # user / reader / catalog
        ├── api/                 # 按模块拆分的接口封装
        ├── components/          # 15 个公共组件
        ├── layouts/             # 后台 / 作者中心布局
        ├── views/               # 24 个页面
        ├── styles/              # 主题变量 + 基础样式
        └── utils/
```

---

## 四、版本规划

| 阶段 | 目标 | 产出 | 建议周期 |
|---|---|---|---|
| **P0 设计** | 需求、ER、接口、页面全部定稿 | 本目录全部文档 + schema.sql | 1~2 周 |
| **P1 走通主线** | 登录 → 首页 → 详情 → 阅读 一条线打通 | 可演示的最小闭环 | 3~4 周 |
| **P2 功能补齐** | 书架、评论、搜索、榜单、个人中心 | 功能完整度 100% | 3~4 周 |
| **P3 后台与作者** | 管理后台、作者中心 | 完整业务闭环 | 2~3 周 |
| **P4 打磨** | 日志、异常、测试、性能、部署 | 可交付系统 | 2 周 |
| **P5 论文** | 论文撰写、答辩 PPT、演示彩排 | 交付物 | 与 P2~P4 并行 |

> **贯穿始终**：每完成一个模块，当天更新 `DEVLOG.md`，并截图存档（写论文时要图）。

---

## 五、明确不做（避免范围爆炸）

- ❌ 接入真实支付网关（微信 / 支付宝商户 API）——**需要营业执照与支付资质**。
  「充值」功能以**人工确认**的方式实现：用户下单 → 扫码付款 → 管理员在后台点「确认到账」，
  不接任何自动回调，属演示性质，详见 DEVLOG 的合规说明。
- ❌ AI 伴读 / 大模型对话（你已明确不需要）
- ❌ 微服务拆分、Docker 集群、Redis 缓存层、消息队列
- ❌ 全文搜索引擎（Elasticsearch）—— 用 MySQL 全文索引即可
- ❌ 移动端 App / 小程序（只做响应式 Web）

---

## 六、快速开始

> 完整的搭建步骤、常见问题、验证清单见 **[SETUP.md](SETUP.md)**。
> 这里只给最短路径。

**环境要求**：Python ≥ 3.11（实测 3.14.5）、Node ≥ 18（实测 24.15）、MySQL ≥ 8.0（实测 8.0.26）

```bash
# ① 建库（一键脚本，Windows）
pwsh scripts/init_db.ps1
#    Linux/macOS 用：bash scripts/init_db.sh

# ② 后端
cd backend
copy .env.example .env        # 改 DATABASE_URL 密码 + SECRET_KEY
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/check_env.py   # 环境自检，全绿再启动
uvicorn main:app --reload --port 8000

# ③ 前端
cd ../frontend
npm install
npm run dev
```

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| 接口文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

**演示账号**：`admin/admin123`、`author1~3/author123`、`reader1~2/reader123`

---
## 七、许可证与声明

本项目为教学 / 毕业设计用途。演示数据须使用**公有领域作品**（如四大名著、鲁迅作品、凡尔纳译本）或自行生成，**不得**使用受版权保护的网络小说正文。
