# -*- coding: utf-8 -*-
"""根路由。

- ``/admin/``    Django Admin
- ``/accounts/`` 登录 / 登出（Django 内置 auth 视图）+ 注册
- ``/``          业务页面（blog.urls）
在 DEBUG 下额外把 MEDIA 暴露给开发服务器（附件 / 封面图 / 缩略图）。
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from blog import views as blog_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", blog_views.register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("blog.urls")),
]

if settings.DEBUG:
    # 开发服务器直接服务上传文件；生产环境应由 Nginx 等 Web 服务器处理
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
