# -*- coding: utf-8 -*-
"""信号驱动：审计日志（必须） + 缩略图生成（加分项 1）。

**为什么必须用信号**

需求明确禁止在视图里手工 ``AuditLog.objects.create``。真实项目里文章的写入
路径不止视图一条——还有 Django Admin、``manage.py shell``、数据迁移、后台
任务、测试夹具。把审计写在视图里，必然出现"某个路径忘了记"的漏 auditing。
信号挂在**模型层**，任何写入路径都会触发，视图只负责业务逻辑与权限，横切
关注点（审计）由这里统一兜住。

**"操作人"怎么来**

信号拿不到 ``request``，而审计要记是谁操作的。方案是
:class:`blog.middleware.CurrentUserMiddleware` 在每次请求进入时把
``request.user`` 存进 thread-local，这里用 ``get_current_user()`` 取出。
局限：thread-local 只在"同一线程"内有效。请求处理同线程，所以视图引发的
写入都能正确取到用户；而 shell / 后台任务没有请求上下文，取到 ``None``，
operator 记为 NULL，表示"系统操作"。

**"变更前后差异"怎么算**

``post_save`` 只能拿到"保存之后"的对象，看不到旧值。所以 ``pre_save`` 先把
数据库里的旧值快照到 ``instance._old_values``，``post_save`` 再逐字段比对，
把差异写进 ``AuditLog.changes``，形如
``{"status": {"old": "draft", "new": "published"}}``。
"""

from __future__ import annotations

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .middleware import get_current_user
from .models import Article, AuditLog
from .thumbnails import make_thumbnail

# 只有这些字段的变化才值得写审计。
#
# 特别地**不包含 views**：浏览量是高频自增，记进审计会把日志表刷爆；而且
# views 走的是 F() 的 QuerySet.update()，压根不会触发 post_save。
# 也不包含 created_at / updated_at / thumbnail / cover 这类内部字段。
TRACKED_FIELDS = ("title", "body", "status", "is_deleted")

# 状态 → 审计动作 映射。不在表里的状态（例如从 published 退回 draft）记为 update。
_STATUS_ACTION = {
    Article.Status.PUBLISHED: AuditLog.Action.PUBLISH,
    Article.Status.ARCHIVED: AuditLog.Action.ARCHIVE,
}


@receiver(pre_save, sender=Article)
def snapshot_old_values(sender, instance: Article, update_fields=None, **kwargs) -> None:
    """保存前把库里的旧值快照到 ``instance._old_values``。"""
    instance._old_values = None

    if instance.pk is None:
        # 新建：库里还没有旧行，post_save 会以 created=True 走另一条分支
        return

    if update_fields is not None and not set(update_fields) & set(TRACKED_FIELDS):
        # 本次保存显式声明只改别的字段（例如只刷 views / 缩略图），省掉这次查询
        return

    instance._old_values = (
        Article.objects.filter(pk=instance.pk).values(*TRACKED_FIELDS).first()
    )


@receiver(post_save, sender=Article)
def record_article_audit(
    sender, instance: Article, created: bool, raw: bool = False, **kwargs
) -> None:
    """文章创建 / 更新（含状态流转、软删除）都写审计日志。

    Args:
        created: 由 Django 传入，True 表示 INSERT。
        raw: 由 Django 传入，True 表示 ``loaddata`` 等夹具导入——这种不算
            业务操作，不写审计。
    """
    if raw:
        return

    if created:
        _log_creation(instance)
    else:
        _log_update(instance)

    # 幂等：没有封面图或已有缩略图时内部直接返回 False
    make_thumbnail(instance)


@receiver(pre_delete, sender=Article)
def record_article_hard_delete(sender, instance: Article, **kwargs) -> None:
    """硬删除（真正执行 ``DELETE``）也要留痕。

    ``AuditLog.article`` 是 ``SET_NULL``，所以这行日志在文章行消失后依然存在，
    只是 ``article`` 变成 NULL；标题冗余记在 ``changes`` 里，便于事后追溯。
    """
    AuditLog.objects.create(
        article=instance,
        operator=get_current_user(),
        action=AuditLog.Action.DELETE,
        changes={"title": {"old": instance.title, "new": None}},
    )


# ----------------------------------------------------------------------
# 内部辅助
# ----------------------------------------------------------------------


def _log_creation(article: Article) -> None:
    """记录创建。旧值统一记 ``None``，让 changes 的形状与更新时保持一致。"""
    changes = {
        field: {"old": None, "new": getattr(article, field)}
        for field in ("title", "body", "status")
        if getattr(article, field)
    }
    AuditLog.objects.create(
        article=article,
        operator=get_current_user(),
        action=AuditLog.Action.CREATE,
        changes=changes,
    )


def _log_update(article: Article) -> None:
    """比对快照，把有差异的字段写进审计日志。

    仅当被跟踪字段真的变了才写——例如只改了封面图、或（理论上）
    只改了 views 时，这里会静默返回，不产生噪音日志。
    """
    old = getattr(article, "_old_values", None)
    if old is None:
        return

    changes = {}
    for field in TRACKED_FIELDS:
        old_value = old.get(field)
        new_value = getattr(article, field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}

    if not changes:
        return

    if changes.get("is_deleted", {}).get("new") is True:
        # 软删除：is_deleted 由 False 变 True
        action = AuditLog.Action.DELETE
    elif "status" in changes:
        action = _STATUS_ACTION.get(changes["status"]["new"], AuditLog.Action.UPDATE)
    else:
        action = AuditLog.Action.UPDATE

    AuditLog.objects.create(
        article=article,
        operator=get_current_user(),
        action=action,
        changes=changes,
    )
