# -*- coding: utf-8 -*-
"""Django Admin 注册。

工程题 A 不要求 Admin 深度定制（那是工程题 B 的内容），这里只做基本配置，
方便在后台直接核对数据与审计日志。
"""

from django.contrib import admin

from .models import Article, Attachment, AuditLog


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("downloads", "uploaded_at")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "views", "is_deleted", "created_at", "updated_at")
    list_filter = ("status", "is_deleted", "author")
    search_fields = ("title", "body")
    readonly_fields = ("views", "thumbnail", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [AttachmentInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """审计日志只读：它只能由信号写入，禁止在后台手工增删改。"""

    list_display = ("created_at", "action", "article", "operator", "summary")
    list_filter = ("action",)
    search_fields = ("article__title", "operator__username")
    readonly_fields = ("article", "operator", "action", "changes", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "article", "downloads", "uploaded_at")
    list_filter = ("article__author",)
    search_fields = ("file_name",)
    readonly_fields = ("downloads",)
