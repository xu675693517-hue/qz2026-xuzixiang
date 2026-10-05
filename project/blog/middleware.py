# -*- coding: utf-8 -*-
"""把"当前请求的用户"放进 thread-local，供信号读取。

信号（pre_save / post_save / pre_delete）拿不到 `request`，但审计日志需要
记录操作人。业界常用做法有两种：

1. **thread-local + 中间件**（本项目采用）：中间件在请求进入时把
   `request.user` 存好，信号读取。零侵入、写法简单。
2. 显式传参：视图里 `instance._operator = request.user`。缺点是要在每个
   写入点手动写，泄漏一处就漏记一处，还要求改模型层。

局限：thread-local 只在"同一个线程"内有效。请求处理是同步同线程的，所以
视图引发的写入都能正确取到用户；而 `manage.py shell`、Celery 后台任务、
数据迁移里没有请求上下文，取到的是 `None`，此时审计日志的 operator 记为
NULL，表示"系统操作"。
"""

from __future__ import annotations

import threading

from django.http import HttpRequest, HttpResponse

_state = threading.local()


def get_current_user():
    """返回当前线程关联的登录用户；没有则返回 None。"""
    user = getattr(_state, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    return user


class CurrentUserMiddleware:
    """请求期间把 `request.user` 绑定到 thread-local。

    必须放在 `AuthenticationMiddleware` **之后**，否则 `request.user` 还不存在。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        _state.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            # 请求结束务必清理：work 线程会被复用，不清理会串号
            _state.user = None
