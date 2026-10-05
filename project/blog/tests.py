# -*- coding: utf-8 -*-
"""工程题 A 的测试：模型 / 信号审计 / 权限 / 并发浏览量 / 附件 / 缩略图。

运行：

    cd project
    python manage.py test blog -v 2
"""

from __future__ import annotations

import json
import tempfile
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Article, Attachment, AuditLog
from .thumbnails import THUMBNAIL_WIDTH, make_thumbnail

User = get_user_model()

def make_image_bytes(width: int, height: int, fmt: str = "PNG") -> bytes:
    """生成一张纯色图片的字节内容。"""
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (width, height), (200, 40, 40)).save(buffer, format=fmt)
    return buffer.getvalue()


class TempMediaRootMixin:
    """给每个测试类一个临时 MEDIA_ROOT，用完即删——不在 %TEMP% 里留垃圾。"""

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.TemporaryDirectory(prefix="qz2026-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir.name)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        cls._media_dir.cleanup()


class BaseBlogTestCase(TempMediaRootMixin, TestCase):
    """公共夹具。"""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username="author", password="pw-Strong-1")
        cls.other = User.objects.create_user(username="other", password="pw-Strong-1")

    def make_article(self, **kwargs) -> Article:
        defaults = {"title": "测试文章", "body": "正文内容", "author": self.author}
        defaults.update(kwargs)
        return Article.objects.create(**defaults)

    def clear_logs(self) -> None:
        AuditLog.objects.all().delete()


# ======================================================================
# 一、模型
# ======================================================================


class ModelTests(BaseBlogTestCase):
    def test_str_and_meta_ordering(self):
        first = self.make_article(title="第一篇")
        second = self.make_article(title="第二篇")
        self.assertEqual(str(first), "第一篇")
        # Meta.ordering = ["-created_at"]，新的在前
        self.assertEqual(list(Article.objects.all()), [second, first])

    def test_verbose_names(self):
        self.assertEqual(Article._meta.verbose_name, "文章")
        self.assertEqual(AuditLog._meta.verbose_name, "审计日志")
        self.assertEqual(Attachment._meta.verbose_name, "附件")

    def test_default_status_is_draft_and_views_zero(self):
        article = self.make_article()
        self.assertEqual(article.status, Article.Status.DRAFT)
        self.assertEqual(article.views, 0)

    def test_related_names(self):
        article = self.make_article()
        Attachment.objects.create(article=article, file_name="a.txt",
                                  file=SimpleUploadedFile("a.txt", b"hello"))
        self.assertEqual(article.attachments.count(), 1)
        self.assertIn(article, self.author.articles.all())
        self.assertTrue(article.audit_logs.exists())

    def test_attachment_cascade_delete(self):
        article = self.make_article()
        Attachment.objects.create(article=article, file_name="a.txt",
                                  file=SimpleUploadedFile("a.txt", b"hello"))
        article.delete()
        self.assertEqual(Attachment.objects.count(), 0)

    def test_get_absolute_url(self):
        article = self.make_article()
        self.assertEqual(article.get_absolute_url(), f"/articles/{article.pk}/")

    def test_auditlog_summary_renders(self):
        article = self.make_article()
        log = article.audit_logs.get()
        self.assertIn("→", log.summary)  # None → "..." 形式


# ======================================================================
# 二、信号驱动的审计日志（本题核心）
# ======================================================================


class AuditSignalTests(BaseBlogTestCase):
    def test_create_writes_create_log(self):
        article = self.make_article(title="新建的标题")
        log = AuditLog.objects.get(action=AuditLog.Action.CREATE)
        self.assertEqual(log.article, article)
        self.assertEqual(log.changes["title"]["new"], "新建的标题")
        self.assertIsNone(log.changes["title"]["old"])

    def test_status_to_published_logs_publish_with_diff(self):
        article = self.make_article()
        self.clear_logs()

        article.status = Article.Status.PUBLISHED
        article.save()

        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.Action.PUBLISH)
        # 与题目要求的形状完全一致
        self.assertEqual(log.changes, {"status": {"old": "draft", "new": "published"}})

    def test_status_to_archived_logs_archive(self):
        article = self.make_article(status=Article.Status.PUBLISHED)
        self.clear_logs()

        article.status = Article.Status.ARCHIVED
        article.save()

        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.Action.ARCHIVE)
        self.assertEqual(log.changes["status"], {"old": "published", "new": "archived"})

    def test_status_back_to_draft_logs_update(self):
        article = self.make_article(status=Article.Status.PUBLISHED)
        self.clear_logs()

        article.status = Article.Status.DRAFT
        article.save()

        self.assertEqual(AuditLog.objects.get().action, AuditLog.Action.UPDATE)

    def test_field_edit_logs_update(self):
        article = self.make_article(body="旧正文")
        self.clear_logs()

        article.body = "新正文"
        article.save()

        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.Action.UPDATE)
        self.assertEqual(log.changes["body"], {"old": "旧正文", "new": "新正文"})

    def test_save_without_tracked_change_writes_nothing(self):
        article = self.make_article()
        self.clear_logs()

        article.save()  # 什么都没改

        self.assertEqual(AuditLog.objects.count(), 0)

    def test_soft_delete_logs_delete_but_keeps_row(self):
        article = self.make_article()
        self.clear_logs()

        article.soft_delete()

        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.Action.DELETE)
        self.assertEqual(log.changes["is_deleted"], {"old": False, "new": True})
        # 行还在库里（软删除），审计日志没丢
        self.assertTrue(Article.objects.filter(pk=article.pk, is_deleted=True).exists())
        self.assertEqual(article.audit_logs.count(), 1)

    def test_soft_delete_is_idempotent(self):
        article = self.make_article()
        article.soft_delete()
        self.clear_logs()

        article.soft_delete()  # 再删一次

        self.assertEqual(AuditLog.objects.count(), 0)

    def test_restore_logs_update(self):
        article = self.make_article()
        article.soft_delete()
        self.clear_logs()

        article.restore()

        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.Action.UPDATE)
        self.assertEqual(log.changes["is_deleted"], {"old": True, "new": False})

    def test_hard_delete_logs_delete_and_keeps_log_with_null_article(self):
        article = self.make_article(title="将被硬删")
        pk = article.pk
        self.clear_logs()

        article.delete()

        log = AuditLog.objects.get(action=AuditLog.Action.DELETE)
        # AuditLog.article 是 SET_NULL：文章没了，日志必须留着
        self.assertIsNone(log.article)
        self.assertIsNone(log.article_id)
        self.assertEqual(log.changes["title"]["old"], "将被硬删")
        self.assertFalse(Article.objects.filter(pk=pk).exists())

    def test_only_cover_change_does_not_create_audit_log(self):
        article = self.make_article()
        self.clear_logs()

        article.cover.save("cover.png", ContentFile(make_image_bytes(400, 300)), save=True)

        # cover 不在 TRACKED_FIELDS 里，缩略图生成走 QuerySet.update()，都不该产生审计
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_plain_queryset_update_does_not_fire_signals(self):
        """F() 自增走 QuerySet.update()，不触发 post_save —— 所以不会审计刷屏。"""
        article = self.make_article()
        self.clear_logs()

        Article.increase_views(article.pk)

        self.assertEqual(AuditLog.objects.count(), 0)

    def test_operator_recorded_from_thread_local_middleware(self):
        """整个链路：登录用户 POST 视图 → 中间件写入 thread-local → 信号读取。"""
        self.client.force_login(self.author)

        response = self.client.post(
            reverse("blog:article_create"),
            {"title": "来自视图的文章", "body": "", "status": Article.Status.DRAFT},
        )

        self.assertEqual(response.status_code, 302)
        log = AuditLog.objects.get(action=AuditLog.Action.CREATE)
        self.assertEqual(log.operator, self.author)

    def test_operator_is_none_outside_request_context(self):
        """没有请求上下文（如 shell / 后台任务）时 operator 记为 NULL。"""
        self.make_article()
        self.assertIsNone(AuditLog.objects.get().operator)

    def test_changes_is_valid_json_roundtrip(self):
        article = self.make_article()
        article.status = Article.Status.PUBLISHED
        article.save()

        log = AuditLog.objects.latest("created_at")
        # JSONField 存进去能原样读出来
        dumped = json.dumps(log.changes, ensure_ascii=False)
        self.assertEqual(json.loads(dumped), log.changes)


# ======================================================================
# 三、并发安全的浏览量（F() 原子自增）
# ======================================================================


class ViewCounterTests(BaseBlogTestCase):
    def test_f_expression_counts_exactly(self):
        article = self.make_article()
        for _ in range(50):
            Article.increase_views(article.pk)
        article.refresh_from_db()
        self.assertEqual(article.views, 50)

    def test_naive_read_modify_write_loses_updates(self):
        """复现 `article.views += 1; article.save()` 的丢失更新。

        两个"并发请求"在各自的 Python 对象上读到同一个旧值，各自 +1 后写回，
        后写的覆盖先写的 —— 两次访问只留下 1。
        """
        article = self.make_article()

        first_request = Article.objects.get(pk=article.pk)   # 读到 views=0
        second_request = Article.objects.get(pk=article.pk)  # 也读到 views=0

        first_request.views += 1
        first_request.save()
        second_request.views += 1
        second_request.save()

        article.refresh_from_db()
        self.assertEqual(article.views, 1)  # 丢了一次更新
        self.assertNotEqual(article.views, 2)

    def test_detail_view_increments_views_per_request(self):
        article = self.make_article()
        url = reverse("blog:article_detail", args=[article.pk])
        for _ in range(5):
            self.assertEqual(self.client.get(url).status_code, 200)
        article.refresh_from_db()
        self.assertEqual(article.views, 5)

    def test_detail_view_of_deleted_article_returns_404(self):
        article = self.make_article()
        article.soft_delete()
        response = self.client.get(reverse("blog:article_detail", args=[article.pk]))
        self.assertEqual(response.status_code, 404)


# ======================================================================
# 四、附件：上传 / 删除 / 下载计数 / 权限
# ======================================================================


class AttachmentTests(BaseBlogTestCase):
    def upload(self, article, name="readme.txt", content=b"hello world"):
        return self.client.post(
            reverse("blog:attachment_upload", args=[article.pk]),
            {"file": SimpleUploadedFile(name, content)},
        )

    def test_author_can_upload_and_detail_page_lists_it(self):
        article = self.make_article()
        self.client.force_login(self.author)

        response = self.upload(article, "设计文档.txt")

        self.assertEqual(response.status_code, 302)
        attachment = Attachment.objects.get()
        self.assertEqual(attachment.article, article)
        self.assertEqual(attachment.file_name, "设计文档.txt")
        self.assertTrue(attachment.file.name.startswith("attachments/"))

        page = self.client.get(article.get_absolute_url())
        self.assertContains(page, "设计文档.txt")

    def test_non_author_cannot_upload(self):
        article = self.make_article()
        self.client.force_login(self.other)
        response = self.upload(article)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_anonymous_cannot_upload(self):
        article = self.make_article()
        response = self.upload(article)
        self.assertEqual(response.status_code, 302)  # 重定向到登录页
        self.assertIn("/accounts/login/", response.url)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_author_can_delete_own_attachment(self):
        article = self.make_article()
        self.client.force_login(self.author)
        self.upload(article)
        attachment = Attachment.objects.get()

        response = self.client.post(
            reverse("blog:attachment_delete", args=[attachment.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_non_author_cannot_delete_attachment(self):
        article = self.make_article()
        self.client.force_login(self.author)
        self.upload(article)
        attachment = Attachment.objects.get()

        self.client.force_login(self.other)
        response = self.client.post(
            reverse("blog:attachment_delete", args=[attachment.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.count(), 1)

    def test_download_increments_counter_atomically(self):
        article = self.make_article()
        self.client.force_login(self.author)
        self.upload(article, content=b"file body")
        attachment = Attachment.objects.get()

        for _ in range(3):
            response = self.client.get(reverse("blog:attachment_download", args=[attachment.pk]))
            self.assertEqual(response.status_code, 200)
            # FileResponse 会一直持有文件句柄，测试里不关掉的话 Windows 上
            # 临时 MEDIA_ROOT 整个删不掉（tearDownClass 会报 WinError 32）。
            response.close()

        attachment.refresh_from_db()
        self.assertEqual(attachment.downloads, 3)

    def test_upload_without_file_shows_error(self):
        article = self.make_article()
        self.client.force_login(self.author)
        response = self.client.post(reverse("blog:attachment_upload", args=[article.pk]), {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_media_settings_configured(self):
        from django.conf import settings

        # Django 会把相对路径规范成以 / 开头
        self.assertEqual(settings.MEDIA_URL, "/media/")
        self.assertTrue(Path(settings.MEDIA_ROOT).exists())


# ======================================================================
# 五、封面图缩略图（加分项 1）
# ======================================================================


class ThumbnailTests(BaseBlogTestCase):
    def attach_cover(self, article, width, height, name="cover.png"):
        article.cover.save(name, ContentFile(make_image_bytes(width, height)), save=True)
        article.refresh_from_db()
        return article

    def test_thumbnail_is_200px_wide(self):
        article = self.attach_cover(self.make_article(), 800, 600)

        self.assertTrue(article.thumbnail)
        self.assertTrue(article.thumbnail.name.startswith("thumbnails/"))

        from PIL import Image

        with Image.open(article.thumbnail.path) as image:
            self.assertEqual(image.width, THUMBNAIL_WIDTH)
            self.assertEqual(image.height, 150)  # 800x600 等比缩到 200x150

    def test_small_image_is_not_upscaled(self):
        article = self.attach_cover(self.make_article(), 100, 80)

        from PIL import Image

        with Image.open(article.thumbnail.path) as image:
            self.assertEqual(image.width, 100)

    def test_thumbnail_generation_is_idempotent(self):
        article = self.attach_cover(self.make_article(), 640, 480)
        original_name = article.thumbnail.name

        self.assertFalse(make_thumbnail(article))  # 已有缩略图，直接返回 False
        article.refresh_from_db()
        self.assertEqual(article.thumbnail.name, original_name)

    def test_no_recursion_when_generating_thumbnail(self):
        """缩略图写回走 QuerySet.update()，不能触发 post_save 造成无限递归。"""
        article = self.attach_cover(self.make_article(), 400, 400)
        self.clear_logs()
        self.assertEqual(AuditLog.objects.count(), 0)
        # 再存一次也不会炸
        article.save()
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_article_without_cover_has_no_thumbnail(self):
        article = self.make_article()
        self.assertFalse(make_thumbnail(article))
        self.assertFalse(article.thumbnail)

    def test_thumbnail_shown_on_detail_page(self):
        article = self.attach_cover(self.make_article(), 500, 500)
        response = self.client.get(article.get_absolute_url())
        self.assertContains(response, article.thumbnail.url)


# ======================================================================
# 六、列表筛选 / 统计 / 认证
# ======================================================================


class ListAndStatsTests(BaseBlogTestCase):
    def test_list_filters_out_soft_deleted(self):
        visible = self.make_article(title="可见文章")
        hidden = self.make_article(title="已删除文章")
        hidden.soft_delete()

        response = self.client.get(reverse("blog:article_list"))

        self.assertContains(response, visible.title)
        self.assertNotContains(response, hidden.title)

    def test_list_filters_by_status_and_title_search(self):
        self.make_article(title="Django 入门", status=Article.Status.PUBLISHED)
        self.make_article(title="Python 进阶", status=Article.Status.DRAFT)

        response = self.client.get(reverse("blog:article_list"), {"status": "published"})
        self.assertContains(response, "Django 入门")
        self.assertNotContains(response, "Python 进阶")

        response = self.client.get(reverse("blog:article_list"), {"q": "Python"})
        self.assertContains(response, "Python 进阶")
        self.assertNotContains(response, "Django 入门")

    def test_list_pagination_is_ten_per_page(self):
        for index in range(12):
            self.make_article(title=f"文章 {index:02d}")
        response = self.client.get(reverse("blog:article_list"))
        self.assertEqual(len(response.context["articles"]), 10)
        self.assertTrue(response.context["page_obj"].has_next())

    def test_stats_requires_login(self):
        response = self.client.get(reverse("blog:stats"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_stats_shows_aggregates(self):
        published = self.make_article(title="已发布", status=Article.Status.PUBLISHED)
        self.make_article(title="草稿")
        Article.increase_views(published.pk)
        Article.increase_views(published.pk)

        self.client.force_login(self.author)
        response = self.client.get(reverse("blog:stats"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_articles"], 2)
        self.assertEqual(response.context["total_views"], 2)
        self.assertEqual(response.context["by_status"]["已发布"], 1)
        self.assertEqual(response.context["by_status"]["草稿"], 1)
        self.assertLessEqual(len(response.context["recent_logs"]), 10)

    def test_article_create_requires_login(self):
        response = self.client.get(reverse("blog:article_create"))
        self.assertEqual(response.status_code, 302)

    def test_author_is_forced_to_current_user(self):
        """前端就算伪造 author，也会被视图强制改回当前登录用户。"""
        self.client.force_login(self.author)
        self.client.post(
            reverse("blog:article_create"),
            {"title": "冒充文", "body": "", "status": "draft", "author": self.other.pk},
        )
        self.assertEqual(Article.objects.get().author, self.author)

    def test_non_author_cannot_edit_or_delete(self):
        article = self.make_article()
        self.client.force_login(self.other)

        edit = self.client.get(reverse("blog:article_update", args=[article.pk]))
        self.assertEqual(edit.status_code, 403)

        delete = self.client.post(reverse("blog:article_delete", args=[article.pk]))
        self.assertEqual(delete.status_code, 403)

    def test_soft_delete_via_view(self):
        article = self.make_article()
        self.client.force_login(self.author)

        response = self.client.post(reverse("blog:article_delete", args=[article.pk]))

        self.assertEqual(response.status_code, 302)
        article.refresh_from_db()
        self.assertTrue(article.is_deleted)
        self.assertEqual(
            AuditLog.objects.latest("created_at").action, AuditLog.Action.DELETE
        )


# ======================================================================
# 七、注册：密码必须哈希存储
# ======================================================================


class RegistrationTests(TestCase):
    def test_register_hashes_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newbie",
                "password1": "Str0ng-Pass-2026",
                "password2": "Str0ng-Pass-2026",
            },
        )

        self.assertEqual(response.status_code, 302)  # 注册成功跳登录页
        user = User.objects.get(username="newbie")
        # 绝不能是明文
        self.assertNotEqual(user.password, "Str0ng-Pass-2026")
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password("Str0ng-Pass-2026"))
