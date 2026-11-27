"""静态自检：检查所有 `xxx_service.func(...)` 调用在对应模块里是否真的存在。

背景：曾经用整体覆盖的方式重写 author_service.py，把作者中心的 11 个函数冲掉，
      直到用户点「新建作品」报 500 才发现。这个脚本用来兜住这类问题。

用法：
    cd backend
    .venv\\Scripts\\python.exe scripts\\check_service_refs.py
"""
import importlib
import pathlib
import re
import sys

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

ROOT = BACKEND_ROOT / "app"
PATTERN = re.compile(r"\b(\w+_service)\.(\w+)")


def main() -> int:
    missing: list[tuple[str, str, str, str]] = []
    checked = 0

    for path in sorted(ROOT.rglob("*.py")):
        if path.name.endswith("_service.py"):
            continue
        text = path.read_text(encoding="utf-8")
        for module_name, func_name in sorted(set(PATTERN.findall(text))):
            try:
                module = importlib.import_module(f"app.services.{module_name}")
            except Exception as exc:  # noqa: BLE001
                missing.append((str(path.relative_to(ROOT)), module_name, func_name, f"导入失败: {exc}"))
                continue
            checked += 1
            if not hasattr(module, func_name):
                missing.append((str(path.relative_to(ROOT)), module_name, func_name, "函数不存在"))

    print(f"检查调用点: {checked}")
    if missing:
        print("发现缺失:")
        for item in missing:
            print(f"  {item[0]}  ->  {item[1]}.{item[2]}  ({item[3]})")
        return 1

    print("全部存在 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
