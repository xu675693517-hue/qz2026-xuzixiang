# -*- coding: utf-8 -*-
"""文章管理系统的数据模型（工程题 A：数据层）。

三个模型：

- :class:`Article`    —— 文章：标题 / 正文 / 作者 / 状态 / 浏览量，
  另含软删除标记（加分项 3）与封面图 + 缩略图（加分项 1）。
- :class:`Attachment` —— 附件：挂在文章下，含下载计数（加分项 4）。
- :class:`AuditLog`   —— 审计日志：**由 blog.signals 的信号驱动写入**，
  视图里绝不手工 `create`。

关系设计：

- `Article.author` → `User`，`CASCADE`：作者注销，其文章一并清理。
- `Attachment.article` → `Article`，`CASCADE`，`related_name="attachments"`。
- `AuditLog.article` → `Article`，`SET_NULL`：**文章没了，日志必须留着**，
  所以不能级联删除，冗余记下文章标题即可追溯。
- `AuditLog.operator` → `User`，`SET_NULL`：操作人注销后日志仍然保留。
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse


class Article(models.Model):
    """一篇文章。"""

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        ARCHIVED = "archived", "已归档"

    title = models.CharField("标题", max_length=200)
    body = models.TextField("正文", blank=True, default="")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        on_delete=models.CASCADE,
        related_name="articles",
    )
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    # editable=False：浏览量只能由 F() 原子自增，不允许在表单里手填
    views = models.PositiveIntegerField("浏览量", default=0, editable=False)

    # 软删除（加分项 3）：删除只是打标记，行与审计日志都留在库里
    is_deleted = models.BooleanField("已删除", default=False, db_index=True)

    # 封面图 + 自动生成的缩略图（加分项 1）
    cover = models.ImageField("封面图", upload_to="covers/", blank=True, null=True)
    thumbnail = models.ImageField(
        "缩略图",
        upload_to="thumbnails/",
        blank=True,
        null=True,
        editable=False,
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering = ["-created_at"]  # 默认按创建时间倒序
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("blog:article_detail", args=[self.pk])

    # ------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------

    def soft_delete(self, *, actor=None) -> None:
        """软删除：只把 `is_deleted` 置为 True。

        不真正 `DELETE`，好处是文章内容与审计日志都保留，可恢复、可追溯。
        审计日志由 :mod:`blog.signals` 检测到 `is_deleted` 由 False 变 True
        时自动写入，这里不需要（也不允许）手工创建。

        Args:
            actor: 预留参数（操作人由 thread-local 中间件提供，此参数仅作
                显式标注用，写入信号时会以中间件为准）。
        """
        if self.is_deleted:
            return
        self.is_deleted = True
        # auto_now 字段只有在 update_fields 里出现时才会被更新
        self.save(update_fields=["is_deleted", "updated_at"])

    def restore(self) -> None:
        """撤销软删除。"""
        if not self.is_deleted:
            return
        self.is_deleted = False
        self.save(update_fields=["is_deleted", "updated_at"])

    # ------------------------------------------------------------------
    # 浏览量：必须原子自增
    # ------------------------------------------------------------------

    @classmethod
    def increase_views(cls, pk: int) -> int:
        """把指定文章的浏览量 +1，并返回自增后的值。

        **必须用 `F("views") + 1`，不能用 `article.views += 1; article.save()`。**

        `article.views += 1` 的执行过程是：先在 Python 里把当前值读出来（比如
        10），加一得到 11，再把 11 整行写回数据库。两个并发请求会这样交错：

            请求 A: 读 views=10          → 写 views=11
            请求 B:          读 views=10  → 写 views=11

        两次"访问"最终只加了 1 —— 这就是**丢失更新（lost update）**。而且整行
        `save()` 会把对象当时的所有字段都写回去，并发下还会覆盖别人对标题、
        状态等字段的修改。

        `F("views") + 1` 则完全不同：它不被求值成具体数字，而是编译成

            UPDATE blog_article SET views = views + 1 WHERE id = %s

        交给**数据库**在同一条语句里读改写，行级原子，两个并发请求得到 12。
        """
        from django.db.models import F

        Article.objects.filter(pk=pk).update(views=F("views") + 1)
        return Article.objects.values_list("views", flat=True).get(pk=pk)


class Attachment(models.Model):
    """文章附件。"""

    article = models.ForeignKey(
        Article,
        verbose_name="所属文章",
        on_delete=models.CASCADE,
        related_name="attachments",  # article.attachments.all()
    )
    file_name = models.CharField("文件名", max_length=255)
    file = models.FileField("文件", upload_to="attachments/%Y/%m/")
    # 下载计数（加分项 4），同样只允许 F() 自增
    downloads = models.PositiveIntegerField("下载次数", default=0, editable=False)
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = "附件"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.file_name

    def get_absolute_url(self) -> str:
        return reverse("blog:attachment_download", args=[self.pk])

    @classmethod
    def increase_downloads(cls, pk: int) -> None:
        """下载次数 +1（同样用 F() 原子自增，理由见 `Article.increase_views`）。"""
        from django.db.models import F

        Attachment.objects.filter(pk=pk).update(downloads=F("downloads") + 1)


class AuditLog(models.Model):
    """文章操作审计日志（全部由信号写入）。"""

    class Action(models.TextChoices):
        CREATE = "create", "创建"
        UPDATE = "update", "更新"
        PUBLISH = "publish", "发布"
        ARCHIVE = "archive", "归档"
        DELETE = "delete", "删除"

    article = models.ForeignKey(
        Article,
        verbose_name="关联文章",
        on_delete=models.SET_NULL,  # 文章被硬删后日志必须保留
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="操作人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField("操作类型", max_length=16, choices=Action.choices)
    # 变更摘要：{"status": {"old": "draft", "new": "published"}}
    changes = models.JSONField("变更摘要", default=dict, blank=True)
    created_at = models.DateTimeField("时间戳", auto_now_add=True)

    class Meta:
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        ordering = ["-created_at"]  # 按时间倒序
        indexes = [models.Index(fields=["article", "created_at"])]

    def __str__(self) -> str:
        target = self.article.title if self.article else "（文章已删除）"
        return f"[{self.get_action_display()}] {target}"

    @property
    def summary(self) -> str:
        """把 `changes` 渲染成一行可读摘要，供模板直接展示。"""
        if not self.changes:
            return "—"
        parts = []
        for field, diff in self.changes.items():
            if isinstance(diff, dict) and "old" in diff:
                old = "∅" if diff["old"] is None else diff["old"]
                new = "∅" if diff["new"] is None else diff["new"]
                parts.append(f"{field}: {old} → {new}")
            else:
                parts.append(f"{field}: {diff}")
        return "；".join(parts)
