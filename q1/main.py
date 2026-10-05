# -*- coding: utf-8 -*-
"""编程题 1：JSON 日志管道。

按行解析 JSON Lines（每行一个 JSON 对象）日志文件，统计：

- ``total``     成功解析的日志总条数
- ``by_level``  按 ``level`` 字段的分布
- ``by_user``   按 ``user`` 字段的分布
- ``last_error``最后一条 ``level == "ERROR"`` 的 ``message``（无则 ``None``）

设计要点
--------
1. **逐行解析、坏行只跳过这一行**：单行 ``json.loads`` 失败不会中断整个文件，
   满足"不得中断整个解析"的要求。
2. **失败一律返回结构一致的空结果**：文件不存在 / 是目录 / 无权限 / 内容为空，
   都返回同一个形状的 dict，绝不抛异常。
3. **文件显式指定 ``encoding="utf-8"``**，保证中文日志在各平台上一致。
4. 只用标准库（``json`` / ``os``），不引入第三方依赖。

直接运行：

    python main.py app.jsonl
"""

from __future__ import annotations

import json

# 所有"非正常但可接受"的输入都返回这个形状的字典，保证调用方不用做 None 判断。
EMPTY_RESULT = {
    "total": 0,
    "by_level": {},
    "by_user": {},
    "last_error": None,
}


def analyze_log(filepath: str) -> dict:
    """统计 JSON Lines 日志文件并返回统计字典。

    Args:
        filepath: ``.jsonl`` 文件路径。文件不存在（或不可读）时返回空结果，
            不抛异常。

    Returns:
        形如::

            {
                "total": 5,
                "by_level": {"INFO": 3, "ERROR": 2},
                "by_user": {"张三": 2, "李四": 2, "王五": 1},
                "last_error": "超时",
            }

        空文件或文件不存在时，各计数为 0 / 空字典、``last_error`` 为 ``None``。
    """
    # 每次调用返回全新的字典（含新的嵌套 dict），避免多次调用之间互相污染。
    result = {"total": 0, "by_level": {}, "by_user": {}, "last_error": None}

    try:
        handle = open(filepath, "r", encoding="utf-8")
    except OSError:
        # FileNotFoundError / IsADirectoryError / PermissionError 等
        # 都属于"拿不到数据"，按题目要求返回空结果而不是抛异常。
        return result

    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                # 跳过空行（包括文件末尾的换行和夹在中间的空白行）
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # 该行不是合法 JSON：只跳过这一行，继续解析后面的行
                continue

            if not isinstance(record, dict):
                # 合法 JSON 但不是对象（如裸数字、字符串、数组），
                # 无法取字段，同样跳过而不是崩溃
                continue

            result["total"] += 1

            level = record.get("level")
            result["by_level"][level] = result["by_level"].get(level, 0) + 1

            user = record.get("user")
            result["by_user"][user] = result["by_user"].get(user, 0) + 1

            if level == "ERROR":
                # 顺序遍历，所以最后一次赋值就是"最后一条 ERROR"
                result["last_error"] = record.get("message")

    return result


def main(argv: list[str] | None = None) -> int:
    """命令行入口：``python main.py <file.jsonl>``。"""
    import sys

    argv = sys.argv[1:] if argv is None else argv
    filepath = argv[0] if argv else "app.jsonl"

    result = analyze_log(filepath)
    print(f"文件：{filepath}")
    print(f"总条数：{result['total']}")
    print(f"按级别：{result['by_level']}")
    print(f"按用户：{result['by_user']}")
    print(f"最后一条 ERROR：{result['last_error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
