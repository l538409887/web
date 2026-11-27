"""环境自检：一条命令确认这台机器能不能跑起来。

检查项：
    1. Python 版本
    2. 后端依赖是否装齐
    3. backend/.env 是否存在、键是否齐全
    4. 数据库能否连上、表和数据是否就位

用法：
    cd backend
    .venv\\Scripts\\python.exe scripts\\check_env.py

退出码 0 表示全部通过，1 表示有问题（会打印处理建议）。
"""
import importlib
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

OK = "  [OK]  "
BAD = "  [!!]  "

problems: list[str] = []


def line(ok: bool, text: str) -> None:
    print((OK if ok else BAD) + text)
    if not ok:
        problems.append(text)


def check_python() -> None:
    print("\n[1] Python 版本")
    major, minor = sys.version_info[:2]
    version = f"{major}.{minor}.{sys.version_info[2]}"
    if (major, minor) >= (3, 11):
        line(True, f"Python {version}")
    else:
        line(False, f"Python {version}，需要 3.11 及以上（本项目在 3.14.5 上测试）")


def check_packages() -> None:
    print("\n[2] 后端依赖")
    required = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pymysql", "PyMySQL"),
        ("pydantic", "pydantic"),
        ("pydantic_settings", "pydantic-settings"),
        ("jwt", "PyJWT"),
        ("cryptography", "cryptography"),
        ("multipart", "python-multipart"),
        ("loguru", "loguru"),
    ]
    for module, package in required:
        try:
            importlib.import_module(module)
            line(True, package)
        except Exception as exc:  # noqa: BLE001
            line(False, f"{package} 未安装或损坏（{exc}）")

    if problems:
        print("\n    修复：pip install -r requirements.txt")


def check_env_file() -> None:
    print("\n[3] 环境变量文件")
    env_path = BACKEND_ROOT / ".env"
    example_path = BACKEND_ROOT / ".env.example"

    if not env_path.exists():
        line(False, "backend/.env 不存在")
        print("    修复：copy .env.example .env  （Linux/macOS: cp）")
        print("          然后修改 DATABASE_URL 里的密码，并把 SECRET_KEY 换成随机串")
        return
    line(True, "backend/.env 存在")

    def keys_of(path: pathlib.Path) -> set[str]:
        if not path.exists():
            return set()
        result = set()
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            result.add(raw.split("=", 1)[0].strip())
        return result

    env_keys = keys_of(env_path)
    example_keys = keys_of(example_path)

    # 这两项没有合理默认值，缺了就一定跑不起来
    critical = {"DATABASE_URL", "SECRET_KEY"}
    missing = sorted(example_keys - env_keys)
    missing_critical = [k for k in missing if k in critical]
    missing_optional = [k for k in missing if k not in critical]

    if missing_critical:
        line(False, f".env 缺少关键配置：{', '.join(missing_critical)}")
    else:
        line(True, f"关键配置齐全（共 {len(env_keys)} 项）")

    if missing_optional:
        print(f"    提示：{', '.join(missing_optional)} 未配置，将使用代码里的默认值")

    secret = ""
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("SECRET_KEY="):
            secret = raw.split("=", 1)[1].strip()
    if secret and ("change" in secret.lower() or len(secret) < 16):
        print("    警告：SECRET_KEY 看起来还是默认值，正式使用前请换成随机串")
        print('          生成：python -c "import secrets; print(secrets.token_urlsafe(32))"')


def check_database() -> None:
    print("\n[4] 数据库")
    try:
        from sqlalchemy import text

        from app.core.database import engine
    except Exception as exc:  # noqa: BLE001
        line(False, f"无法加载数据库配置（{exc}）")
        return

    try:
        with engine.connect() as conn:
            tables = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
            ).scalar()
            line(True, f"连接成功，当前库有 {tables} 张表")
    except Exception as exc:  # noqa: BLE001
        line(False, f"连接失败：{str(exc).splitlines()[0]}")
        print("    检查：MySQL 是否启动 / .env 的 DATABASE_URL 是否正确 /")
        print("         是否执行过 mysql -u root -p < db/00_create_user.sql")
        return

    if tables < 19:
        line(False, f"表数量不足（{tables}/19），可能没执行 db/schema.sql 和 migrations")
        return

    try:
        with engine.connect() as conn:
            books = conn.execute(text("SELECT COUNT(*) FROM book")).scalar()
            users = conn.execute(text("SELECT COUNT(*) FROM sys_user")).scalar()
        line(books >= 1, f"书籍 {books} 本")
        line(users >= 1, f"用户 {users} 个")
        if books < 22:
            print("    提示：执行 db/demo_extra_books.sql 可补到 22 本，首页三个书区才不会空")
    except Exception as exc:  # noqa: BLE001
        line(False, f"查询数据失败：{str(exc).splitlines()[0]}")


def main() -> int:
    print("=" * 60)
    print("  基于 Python 的轻量化 Web 小说平台 · 环境自检")
    print("=" * 60)

    check_python()
    check_packages()
    check_env_file()
    check_database()

    print("\n" + "=" * 60)
    if problems:
        print(f"  未通过：{len(problems)} 项，请按上面的提示处理")
        print("=" * 60)
        return 1

    print("  全部通过，可以启动：")
    print("    uvicorn main:app --reload --port 8000")
    print("  前端：")
    print("    cd ../frontend && npm install && npm run dev")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
