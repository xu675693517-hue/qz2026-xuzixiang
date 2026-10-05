#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Django 命令行入口。"""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "无法导入 Django。请先激活虚拟环境并安装依赖：\n"
            "    pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
