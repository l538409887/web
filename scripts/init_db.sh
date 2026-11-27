#!/usr/bin/env bash
# =============================================================
#  一键初始化数据库（Linux / macOS）
#
#  做四件事，顺序不能换：
#    1. schema.sql           建库 + 建 19 张表（含 DROP，会清空同名表）
#    2. 00_create_user.sql   建最小权限账号 novel_app
#    3. seed.sql             写入首批演示数据（12 本书 / 6 个账号）
#    4. demo_extra_books.sql 再补 10 本书（首页三个书区需要 22 本）
#
#  用法：
#    bash scripts/init_db.sh          # 有确认提示
#    bash scripts/init_db.sh --force  # 跳过确认
#
#  注意：schema.sql 会 DROP 已有表，seed.sql 会 TRUNCATE，
#        只适合全新环境。已有数据请改用 db/migrations/ 增量脚本。
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DB_DIR="$REPO_ROOT/db"

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

if ! command -v mysql >/dev/null 2>&1; then
  echo "[错误] 找不到 mysql 客户端，请先安装 MySQL 客户端或加入 PATH" >&2
  exit 1
fi

for f in schema.sql 00_create_user.sql seed.sql demo_extra_books.sql; do
  [[ -f "$DB_DIR/$f" ]] || { echo "[错误] 缺少文件 db/$f" >&2; exit 1; }
done

echo "即将执行以下操作："
echo "  1. 重建数据库与全部表  （会清空已有数据！）"
echo "  2. 创建账号 novel_app"
echo "  3. 写入演示数据 22 本书"
echo

if [[ "$FORCE" -ne 1 ]]; then
  read -r -p "确认继续？输入 yes 回车: " ans
  [[ "$ans" == "yes" ]] || { echo "已取消。"; exit 0; }
fi

read -r -s -p "请输入 MySQL root 密码: " ROOT_PWD
echo
export MYSQL_PWD="$ROOT_PWD"

# mysql 客户端对含非 ASCII 字符的绝对路径不友好，统一切到 db/ 目录用相对文件名
cd "$DB_DIR"

run_sql() {
  local file="$1" db="${2:-}"
  if [[ -n "$db" ]]; then
    mysql -u root --default-character-set=utf8mb4 "$db" -e "source $file"
  else
    mysql -u root --default-character-set=utf8mb4 -e "source $file"
  fi
}

echo "[1/4] schema.sql"
run_sql schema.sql
echo "[2/4] 00_create_user.sql"
run_sql 00_create_user.sql
echo "[3/4] seed.sql"
run_sql seed.sql novel_platform
echo "[4/4] demo_extra_books.sql"
run_sql demo_extra_books.sql novel_platform

echo
echo "验证结果："
mysql -u root --default-character-set=utf8mb4 -t novel_platform -e "
SELECT
  (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='novel_platform') AS 数据表数,
  (SELECT COUNT(*) FROM book) AS 书籍数,
  (SELECT COUNT(*) FROM book_chapter) AS 章节数,
  (SELECT COUNT(*) FROM sys_user) AS 用户数;"

unset MYSQL_PWD

echo
echo "数据库就绪。接下来："
echo "  1) cd backend"
echo "  2) cp .env.example .env   然后改 DATABASE_URL 里的密码"
echo "  3) python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
echo "  4) python scripts/check_env.py   验证环境"
echo "  5) uvicorn main:app --reload --port 8000"
