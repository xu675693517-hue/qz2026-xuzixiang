# -*- coding: utf-8 -*-
"""视图层：只负责业务逻辑与权限校验，**审计一律交给信号**。

本模块内不会出现任何 ``AuditLog.objects.create`` —— 这是工程题 A 的硬性要求。
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ArticleForm, AttachmentForm
from .models import Article, Attachment, AuditLog

PAGE_SIZE = 10


# ----------------------------------------------------------------------
# 文章
# ----------------------------------------------------------------------


def article_list(request):
    """文章列表：按状态 / 作者筛选 + 标题搜索 + 分页，并过滤掉已软删除的文章。"""
    articles = (
        Article.objects.filter(is_deleted=False)
        .select_related("author")
        .prefetch_related("attachments")
    )

    status = request.GET.get("status") or ""
    if status in dict(Article.Status.choices):
        articles = articles.filter(status=status)

    author = request.GET.get("author") or ""
    if author.isdigit():
        articles = articles.filter(author_id=int(author))

    query = (request.GET.get("q") or "").strip()
    if query:
        articles = articles.filter(title__icontains=query)

    page = Paginator(articles, PAGE_SIZE).get_page(request.GET.get("page"))

    return render(
        request,
        "blog/article_list.html",
        {
            "page_obj": page,
            "articles": page.object_list,
            "statuses": Article.Status.choices,
            "current_status": status,
            "current_author": author,
            "query": query,
        },
    )


def article_detail(request, pk):
    """文章详情：浏览量 +1、附件列表、审计日志（按时间倒序）。"""
    article = get_object_or_404(
        Article.objects.select_related("author"), pk=pk, is_deleted=False
    )

    # 浏览量 +1 —— 必须用 F() 原子自增，理由见 models.Article.increase_views：
    #   article.views += 1; article.save()  是"读-改-写"三步，并发下两个请求
    #   都读到同一个旧值，后写的覆盖先写的 → 丢更新；而且整行 save() 会把对象
    #   里所有字段一起写回，还会顺手覆盖别人对标题 / 状态的修改。
    #   F("views") + 1 编译成 SET views = views + 1，交给数据库原子执行。
    Article.increase_views(article.pk)
    article.refresh_from_db(fields=["views"])

    return render(
        request,
        "blog/article_detail.html",
        {
            "article": article,
            "attachments": article.attachments.all(),
            # AuditLog.Meta.ordering = ["-created_at"]，天然按时间倒序
            "audit_logs": article.audit_logs.select_related("operator")[:20],
            "attachment_form": AttachmentForm(),
            "can_edit": request.user.is_authenticated
            and article.author_id == request.user.pk,
        },
    )


@login_required
def article_create(request):
    """新建文章。作者强制为当前登录用户。"""
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()  # 审计日志由 post_save 信号自动写入
            messages.success(request, f"文章《{article.title}》已创建。")
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm()
    return render(request, "blog/article_form.html", {"form": form, "is_create": True})


@login_required
def article_update(request, pk):
    """编辑文章。只有作者本人可以编辑。"""
    article = get_object_or_404(Article, pk=pk)
    if article.author_id != request.user.pk:
        raise PermissionDenied("只能编辑自己的文章。")

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()  # 状态流转的审计由 post_save 信号自动判定
            messages.success(request, "文章已更新。")
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm(instance=article)
    return render(
        request,
        "blog/article_form.html",
        {"form": form, "article": article, "is_create": False},
    )


@login_required
@require_POST
def article_delete(request, pk):
    """软删除文章（不真删，审计日志与内容都保留）。"""
    article = get_object_or_404(Article, pk=pk)
    if article.author_id != request.user.pk:
        raise PermissionDenied("只能删除自己的文章。")

    article.soft_delete()  # 审计由信号检测 is_deleted 变化后写入
    messages.success(request, "文章已删除（软删除，行仍在库中）。")
    return redirect("blog:article_list")


# ----------------------------------------------------------------------
# 附件
# ----------------------------------------------------------------------


@login_required
@require_POST
def attachment_upload(request, pk):
    """给自己名下的文章上传附件。"""
    article = get_object_or_404(Article, pk=pk, is_deleted=False)
    if article.author_id != request.user.pk:
        raise PermissionDenied("只能给自己的文章上传附件。")

    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.article = article
        # 未填文件名时用上传文件名兜底
        attachment.file_name = attachment.file_name or attachment.file.name.rsplit("/", 1)[-1]
        attachment.save()
        messages.success(request, f"附件「{attachment.file_name}」上传成功。")
    else:
        messages.error(request, "上传失败：请选择一个文件。")
    return redirect(article.get_absolute_url())


@login_required
@require_POST
def attachment_delete(request, pk):
    """删除附件。只有文章作者可以删自己文章下的附件。"""
    attachment = get_object_or_404(
        Attachment.objects.select_related("article"), pk=pk
    )
    if attachment.article.author_id != request.user.pk:
        raise PermissionDenied("只能删除自己文章下的附件。")

    article = attachment.article
    # 先删磁盘文件再删记录；save=False 避免只改字段却触发保存
    attachment.file.delete(save=False)
    attachment.delete()
    messages.success(request, "附件已删除。")
    return redirect(article.get_absolute_url())


def attachment_download(request, pk):
    """下载附件，并把下载次数 +1（同样用 F() 原子自增）。"""
    attachment = get_object_or_404(Attachment, pk=pk)
    Attachment.increase_downloads(pk)

    try:
        return FileResponse(
            attachment.file.open("rb"),
            as_attachment=True,
            filename=attachment.file_name,
        )
    except FileNotFoundError:
        raise Http404("附件文件已丢失。")


# ----------------------------------------------------------------------
# 统计 / 认证
# ----------------------------------------------------------------------


@login_required
def stats(request):
    """文章统计（加分项 2）：总数 / 总浏览量 / 各状态文章数 / 最近 10 条审计日志。"""
    active = Article.objects.filter(is_deleted=False)
    choice_labels = dict(Article.Status.choices)

    by_status = {label: 0 for _, label in Article.Status.choices}
    for row in active.values("status").annotate(count=Count("id")):
        by_status[choice_labels[row["status"]]] = row["count"]

    return render(
        request,
        "blog/stats.html",
        {
            "total_articles": active.count(),
            "total_views": active.aggregate(total=Sum("views"))["total"] or 0,
            "by_status": by_status,
            "deleted_count": Article.objects.filter(is_deleted=True).count(),
            "attachment_count": Attachment.objects.count(),
            "total_downloads": Attachment.objects.aggregate(total=Sum("downloads"))["total"] or 0,
            "recent_logs": AuditLog.objects.select_related("article", "operator")[:10],
        },
    )


def register(request):
    """用户注册。

    密码交给 Django 内置的 `UserCreationForm` → `user.set_password()` 走
    PBKDF2 哈希，**不会有明文落库**。
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "注册成功，请登录。")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
