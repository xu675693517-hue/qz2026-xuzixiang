# -*- coding: utf-8 -*-
"""q1 的单元测试。

覆盖题目给出的 4 个示例，并补齐空行、截断行、ERROR 取最后一条、
UTF-8 中文等题目范围内的边界。

运行：

    cd q1
    python test.py
"""

from __future__ import annotations

import os
import tempfile
import unittest

from main import analyze_log

# 题目"示例 1"的原始内容，逐字照抄，方便对照
APP_JSONL = (
    '{"timestamp": "2026-10-01 10:23:45", "level": "INFO", "message": "用户登录成功", "user": "张三"}\n'
    '{"timestamp": "2026-10-01 10:24:01", "level": "ERROR", "message": "数据库连接失败", "user": "李四"}\n'
    '{"timestamp": "2026-10-01 10:25:12", "level": "INFO", "message": "用户登出", "user": "张三"}\n'
    '{"timestamp": "2026-10-01 10:26:30", "level": "ERROR", "message": "超时", "user": "李四"}\n'
    '{"timestamp": "2026-10-01 10:27:00", "level": "INFO", "message": "任务完成", "user": "王五"}\n'
)

EMPTY = {"total": 0, "by_level": {}, "by_user": {}, "last_error": None}


class AnalyzeLogTestCase(unittest.TestCase):
    """analyze_log 的行为测试。"""

    def write_temp(self, content: str, suffix: str = ".jsonl") -> str:
        """把 content 写进临时文件，返回路径；测试结束自动删除。"""
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.addCleanup(os.remove, path)
        return path

    # ---------- 题目给出的 4 个示例 ----------

    def test_example_1_normal_file(self):
        """示例 1：正常 5 条日志。"""
        result = analyze_log(self.write_temp(APP_JSONL))
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["by_level"], {"INFO": 3, "ERROR": 2})
        self.assertEqual(result["by_user"], {"张三": 2, "李四": 2, "王五": 1})
        self.assertEqual(result["last_error"], "超时")

    def test_example_2_file_not_exist(self):
        """示例 2：文件不存在 —— 返回空结果且不抛异常。"""
        missing = os.path.join(tempfile.gettempdir(), "qz2026_never_exists.jsonl")
        if os.path.exists(missing):
            os.remove(missing)
        result = analyze_log(missing)
        self.assertEqual(result, EMPTY)

    def test_example_3_empty_file(self):
        """示例 3：空文件 —— 返回空结果。"""
        result = analyze_log(self.write_temp(""))
        self.assertEqual(result, EMPTY)

    def test_example_4_bad_line_skipped(self):
        """示例 4：中间夹一行非法 JSON —— 跳过该行，其余照常统计。"""
        content = (
            '{"timestamp": "2026-10-01 10:23:45", "level": "INFO", "message": "ok", "user": "张三"}\n'
            "这不是合法的 JSON\n"
            '{"timestamp": "2026-10-01 10:24:01", "level": "ERROR", "message": "失败", "user": "李四"}\n'
        )
        result = analyze_log(self.write_temp(content))
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["by_level"], {"INFO": 1, "ERROR": 1})
        self.assertEqual(result["last_error"], "失败")

    # ---------- 边界情况 ----------

    def test_no_error_gives_none(self):
        """全无 ERROR 时 last_error 为 None。"""
        content = '{"timestamp": "t", "level": "INFO", "message": "ok", "user": "x"}\n'
        self.assertIsNone(analyze_log(self.write_temp(content))["last_error"])

    def test_last_error_is_the_last_match(self):
        """多条 ERROR 时取"最后一条"的 message。"""
        content = (
            '{"timestamp": "t", "level": "ERROR", "message": "first", "user": "x"}\n'
            '{"timestamp": "t", "level": "ERROR", "message": "second", "user": "x"}\n'
            '{"timestamp": "t", "level": "INFO", "message": "later", "user": "x"}\n'
        )
        self.assertEqual(analyze_log(self.write_temp(content))["last_error"], "second")

    def test_blank_lines_ignored(self):
        """空行不计入 total。"""
        result = analyze_log(self.write_temp("\n\n" + APP_JSONL + "\n\n\n"))
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["by_level"], {"INFO": 3, "ERROR": 2})

    def test_truncated_json_line_skipped(self):
        """被截断的 JSON（写日志时常见的半行）跳过，不中断解析。"""
        content = (
            '{"timestamp": "t", "level": "INFO", "message": "ok", "user": "x"}\n'
            '{"timestamp": "t", "level": "ERRO\n'
        )
        self.assertEqual(analyze_log(self.write_temp(content))["total"], 1)

    def test_returns_independent_new_dict(self):
        """两次调用互不污染：返回的嵌套 dict 不是同一个对象。"""
        first = analyze_log(self.write_temp(""))
        second = analyze_log(self.write_temp(""))
        first["by_level"]["INFO"] = 999
        self.assertEqual(second["by_level"], {})

    def test_utf8_roundtrip(self):
        """中文 user / message 正确解析（证明 encoding="utf-8" 生效）。"""
        result = analyze_log(self.write_temp(APP_JSONL))
        self.assertEqual(result["by_user"]["王五"], 1)
        self.assertEqual(result["last_error"], "超时")


if __name__ == "__main__":
    unittest.main(verbosity=2)
