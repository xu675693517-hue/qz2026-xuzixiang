# -*- coding: utf-8 -*-
"""blog app 配置。

`ready()` 里导入 signals 是 Django 官方推荐做法：保证信号在 app registry
就绪后、且只注册一次（重复 import 不会重复注册）。
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = "文章管理"

    def ready(self) -> None:
        from . import signals  # noqa: F401  （导入即注册）
