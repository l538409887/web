# 部署说明

本目录提供两种部署方式，按「答辩演示」还是「真实上线」自行选择。

| 方式 | 适用场景 | 依赖 | 启动时间 |
|---|---|---|---|
| A. 单机（Nginx + systemd） | 真实服务器、论文里的部署章节 | 系统装 Nginx、Python 3.10+、MySQL 8 | 10 分钟 |
| B. Docker Compose | 本地演示、换机器快速复现 | 只需 Docker Desktop / Docker Engine | 5 分钟 |

两种方式的前端 API 地址都是相对路径 `/api/v1`，因此**不需要改前端代码**，只要 Nginx 把 `/api/` 反代到后端即可。

---

## 文件清单

```
deploy/
├── nginx/
│   ├── novel-platform.conf     # 单机部署站点配置
│   └── docker-web.conf         # 容器内部使用（upstream 是服务名 backend）
├── systemd/
│   └── novel-backend.service   # 后端守护进程
├── Dockerfile.backend          # 后端镜像
├── Dockerfile.web              # 前端镜像（Node 构建 → Nginx 托管）
├── docker-compose.yml          # MySQL + 后端 + 前端
└── .env.docker.example         # compose 环境变量模板
```

---

## 方式 A：单机部署（Nginx + systemd）

### 1. 准备目录

```bash
sudo mkdir -p /opt/novel-platform
sudo chown -R $USER:$USER /opt/novel-platform

# 把项目放进去（或用 git clone）
cd /opt/novel-platform
# 目录结构应为：backend/ frontend/ db/ deploy/ ...
```

### 2. 建库

```bash
mysql -u root -p < db/schema.sql      # 建 23 张表
mysql -u root -p < db/seed.sql        # 基础数据（管理员、分类、演示书）
mysql -u root -p < db/demo_extra_books.sql   # 可选：追加 10 本演示书
mysql -u root -p < db/00_create_user.sql     # 可选：最小权限账号
```

### 3. 后端

```bash
cd /opt/novel-platform/backend

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# 编辑 .env：至少修改 SECRET_KEY 与 DATABASE_URL
```

`.env` 关键项：

```ini
APP_ENV=prod
SECRET_KEY=<32 位以上随机串>
DATABASE_URL=mysql+pymysql://novel_app:密码@127.0.0.1:3306/novel_platform?charset=utf8mb4
CORS_ORIGINS=https://你的域名
TRUSTED_PROXIES=127.0.0.1,::1
```

### 4. 前端构建

```bash
cd /opt/novel-platform/frontend
npm ci
npm run build          # 产物在 dist/
```

### 5. 注册服务

```bash
sudo cp deploy/systemd/novel-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now novel-backend
sudo systemctl status novel-backend
```

### 6. 配置 Nginx

```bash
sudo cp deploy/nginx/novel-platform.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx
```

访问 `http://服务器地址/` 即可。

---

## 方式 B：Docker Compose

### 1. 准备环境变量

```bash
cd deploy
cp .env.docker.example .env.docker
```

编辑 `.env.docker`，**必须改这两项**：

```ini
MYSQL_ROOT_PASSWORD=你的强密码
SECRET_KEY=用下面的命令生成
```

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2. 启动

```bash
docker compose --env-file .env.docker up -d --build
```

首次启动会自动执行 `db/schema.sql` → `db/seed.sql` → `db/demo_extra_books.sql` 建库并灌演示数据。

### 3. 访问

- 站点：<http://localhost:8080>
- 后端健康检查：<http://localhost:8080/api/v1/../health> 不可直接用，改看容器日志：

```bash
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs -f backend
```

### 4. 常用操作

```bash
docker compose --env-file .env.docker down          # 停止（保留数据）
docker compose --env-file .env.docker down -v       # 停止并删除数据卷（清库）
docker compose --env-file .env.docker logs -f web   # 看前端容器日志
```

---

## 生产环境检查清单

| # | 检查项 | 说明 |
|---|---|---|
| 1 | **改 `SECRET_KEY`** | 默认值 `dev-secret-change-me` 意味着任何人都能伪造 JWT |
| 2 | **改数据库密码** | 不要用 `root` 跑应用，用 `db/00_create_user.sql` 建的最小权限账号 |
| 3 | **`TRUSTED_PROXIES` 要配对** | Nginx 部署填 `127.0.0.1`；Compose 填容器网段 `172.28.0.0/16`。**填错会导致限流把所有用户当成同一个 IP** |
| 4 | **worker 数量保持 1** | 限流/封禁状态在进程内存，多 worker 会让额度翻倍 |
| 5 | **配 HTTPS** | 用 Certbot 申请证书，`listen 443 ssl`，并把 `CORS_ORIGINS` 改成 `https://域名` |
| 6 | **关掉 Swagger 公开访问** | 生产可加 `location /docs { deny all; }`，或改 FastAPI 的 `docs_url=None` |
| 7 | **日志轮转** | `backend/logs/` 会持续增长，用 logrotate 或容器日志驱动限制大小 |
| 8 | **数据库备份** | `mysqldump novel_platform > backup.sql` 加 cron |

---

## 常见问题

**Q：部署后 /api 请求 502**
后端没起来。`systemctl status novel-backend` 看错误；常见是 `.env` 里 `DATABASE_URL` 密码错或 MySQL 未启动。

**Q：页面能打开但数据全空**
Nginx 的 `try_files` 没配好，或者 `/api/` 没反代到 8000。检查 `nginx -T | grep proxy_pass`。

**Q：所有人都提示「请求过于频繁」**
`TRUSTED_PROXIES` 没配或配错，导致应用看到的来源 IP 都是 127.0.0.1，全站共用一个限流额度。改成实际的代理地址/网段。

**Q：Docker 启动时 MySQL 一直 unhealthy**
首次初始化要执行 3 个 SQL 文件，可能需要 30 秒以上。看 `docker compose logs mysql`，若报 SQL 语法错，多半是 `db/*.sql` 被改坏。

**Q：上传封面失败（413）**
Nginx 的 `client_max_body_size` 小于后端 `MAX_UPLOAD_SIZE_MB`。两处都调大。
