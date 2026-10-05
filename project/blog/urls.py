# -*- coding: utf-8 -*-
"""blog 应用路由。"""

from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    # 文章
    path("", views.article_list, name="article_list"),
    path("articles/new/", views.article_create, name="article_create"),
    path("articles/<int:pk>/", views.article_detail, name="article_detail"),
    path("articles/<int:pk>/edit/", views.article_update, name="article_update"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),
    # 附件
    path(
        "articles/<int:pk>/attachments/upload/",
        views.attachment_upload,
        name="attachment_upload",
    ),
    path("attachments/<int:pk>/delete/", views.attachment_delete, name="attachment_delete"),
    path(
        "attachments/<int:pk>/download/",
        views.attachment_download,
        name="attachment_download",
    ),
    # 统计
    path("stats/", views.stats, name="stats"),
]
