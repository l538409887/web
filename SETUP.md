# 环境搭建与启动指南

> 目标：**clone 下来，照着做完这四步，就能在浏览器里跑起来。**
> 全程约 10 分钟，其中 `npm install` 占大半时间。

---

## 一、环境要求

| 软件 | 版本要求 | 本项目实测版本 | 检查命令 |
|---|---|---|---|
| Python | **3.11 及以上** | 3.14.5 | `python --version` |
| Node.js | **18 及以上** | 24.15.0 | `node -v` |
| npm | 9 及以上 | 11.12.1 | `npm -v` |
| MySQL | **8.0 及以上**（需支持 utf8mb4） | 8.0.26 | `mysql --version` |

> ⚠️ Python 3.10 及以下**不行**——代码里大量用了 `int | None` 这种 3.10+ 语法。
> 3.11 ~ 3.14 都可以；如果装依赖时某个包没有对应 wheel，把 `requirements.txt` 里的
> `>=` 保留即可（它就是为此设计的）。

还需要：MySQL 的 `bin` 目录在 `PATH` 里（或者你知道 `mysql.exe` 的绝对路径），
因为建库脚本要调用它。

---

## 二、第一步：初始化数据库

### 方式 A：一键脚本（推荐）

**Windows：**
```powershell
pwsh scripts\init_db.ps1
```

**Linux / macOS：**
```bash
bash scripts/init_db.sh
```

脚本会依次执行 `db/` 下四个 SQL 文件，并在最后打印表数/书数做校验。

### 方式 B：手动执行

> ⚠️ **Windows PowerShell 不支持 `<` 输入重定向**（会直接语法报错），
> 所以下面用 `-e "source ..."` 的写法。
> 如果你用的是 **cmd** 或 **Git Bash / Linux**，可以改成 `mysql -u root -p < db/schema.sql`。

```bash
# 在仓库根目录执行，顺序不能换

# ① 建库 + 建 23 张表        （注意：含 DROP，会清空同名表）
mysql -u root -p -e "source db/schema.sql"

# ② 创建最小权限账号 novel_app（应用连库用它，不用 root）
mysql -u root -p -e "source db/00_create_user.sql"

# ③ 首批演示数据：12 本书 / 357 章 / 6 个账号  （注意：含 TRUNCATE）
mysql -u root -p novel_platform -e "source db/seed.sql"

# ④ 再补 10 本书：首页三个书区需要 22 本，不够会空白
mysql -u root -p novel_platform -e "source db/demo_extra_books.sql"
```

> 路径里含中文时，`source` 用**相对路径**才可靠（mysql 客户端打不开含中文的绝对路径）。
> 这也是 `scripts/init_db.ps1` 先 `cd db/` 再执行的原因。

> ⚠️ **这两步会清空数据**：`schema.sql` 有 `DROP TABLE IF EXISTS`，
> `seed.sql` 有 `TRUNCATE`。只能在**全新环境**执行。
> 如果库里已经有数据，请改用 `db/migrations/001~006` 增量升级。

### 建库后的验证

```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='novel_platform';  -- 19
SELECT COUNT(*) FROM book;        -- 22（执行了 demo_extra_books.sql 才算）
SELECT COUNT(*) FROM book_chapter;-- 500+
```

---

## 三、第二步：配置并启动后端

```bash
cd backend

# 1) 复制配置模板
copy .env.example .env          # Windows
cp .env.example .env            # Linux / macOS
```

打开 `.env`，**必须改这两处**：

| 配置项 | 改什么 |
|---|---|
| `DATABASE_URL` | 把里面的密码换成 `00_create_user.sql` 里给 `novel_app` 设的密码 |
| `SECRET_KEY` | 换成随机长串：`python -c "import secrets; print(secrets.token_urlsafe(32))"` |

```bash
# 2) 创建虚拟环境并装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

pip install -r requirements.txt
# 想 100% 复现开发环境（含传递依赖版本）：
# pip install -r requirements.lock.txt

# 3) 自检（强烈建议，能提前发现 90% 的环境问题）
python scripts/check_env.py
```

自检全绿后启动：

```bash
uvicorn main:app --reload --port 8000
```

看到 `Uvicorn running on http://127.0.0.1:8000` 就成功了。

---

## 四、第三步：启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**

> 前端已配好代理：`/api` 和 `/static` 会自动转发到 `http://127.0.0.1:8000`，
> 所以**不需要**在前端配任何后端地址。

---

## 五、第四步：验证是否真的跑通了

按顺序点一遍，全部正常才算成功：

| # | 操作 | 预期 |
|---|---|---|
| 1 | 打开 http://127.0.0.1:8000/health | 返回 `{"status":"ok"}` |
| 2 | 打开 http://127.0.0.1:8000/docs | 能看到 83 个路径 / 98 个操作的 Swagger 文档 |
| 3 | 打开 http://localhost:5173 | 首页有轮播图 + 三个书区 + 右侧三个榜单 |
| 4 | 用 `reader1 / reader123` 登录 | 右上角显示昵称「一个读者」 |
| 5 | 点任意一本书 → 开始阅读 | 正文正常显示，段落右侧有间贴气泡 |
| 6 | 用 `admin / admin123` 登录 → 个人中心 | 能看到「管理后台」入口 |
| 7 | 进管理后台 → 书籍管理 | 能看到待审核作品 |

---

## 六、演示账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 作者 | `author1` / `author2` / `author3` | `author123` |
| 读者 | `reader1` / `reader2` | `reader123` |

> `POST /author/apply` 是**自助升级**：读者点一下就会变成作者角色。
> 如果 `reader1` 登录后没有读者视角，多半是点过升级，执行
> `UPDATE sys_user SET role='reader' WHERE username='reader1';` 可改回。

---

## 七、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `Access denied for user 'novel_app'` | 没执行 `00_create_user.sql`，或 `.env` 密码与建账号时不一致 | 重跑 ②，或改 `.env` 的 `DATABASE_URL` |
| `Unknown database 'novel_platform'` | 没执行 `schema.sql` | 执行 ① |
| 启动报 `No module named 'app'` | 不在 `backend/` 目录下启动 | `cd backend` 后再启动 |
| 前端能开但接口全 404 / 跨域报错 | 后端没起来，或 `CORS_ORIGINS` 不含 `http://localhost:5173` | 先起后端；检查 `.env` |
| 首页某个书区空白 | 书不够 22 本 | 执行 `demo_extra_books.sql` |
| 上传图片 413 | 文件超过 `MAX_UPLOAD_SIZE_MB`（默认 2MB） | 改 `.env` 里的值 |
| 充值弹窗没有二维码 | 未配置收款码 | 把图片命名为 `wechat.png` 放进 `backend/static/pay/` |
| `mysql` 不是内部或外部命令 | MySQL bin 不在 PATH | 把 `...\MySQL Server 8.0\bin` 加入 PATH |

---

## 八、目录与端口速查

| 项目 | 值 |
|---|---|
| 后端端口 | `8000` |
| 前端端口 | `5173` |
| 数据库名 | `novel_platform` |
| 应用数据库账号 | `novel_app`（只有增删改查权限，无 DDL） |
| 后端配置 | `backend/.env`（**不提交到 Git**） |
| 日志目录 | `backend/logs/`（按天切分） |
| 上传文件 | `backend/static/covers`、`static/avatars`、`static/pay` |

---

## 九、两个自检脚本

| 脚本 | 作用 | 何时用 |
|---|---|---|
| `backend/scripts/check_env.py` | 检查 Python 版本、依赖、`.env`、数据库连接与表数量 | 装完环境后 / 报错时 |
| `backend/scripts/check_service_refs.py` | 静态扫描所有 `xxx_service.func()` 调用是否真实存在 | 改完后端代码后 |

两个脚本都用退出码表示结果（0 通过），可以接进 CI。
