# -*- coding: utf-8 -*-
"""表单：文章表单 + 附件上传表单。"""

from __future__ import annotations

from django import forms

from .models import Article, Attachment


class ArticleForm(forms.ModelForm):
    """文章的新建 / 编辑表单。

    刻意**不包含 `author` 字段**：作者必须由视图强制设为当前登录用户，
    否则前端可以伪造 `author_id` 把文章挂到别人名下。
    """

    class Meta:
        model = Article
        fields = ["title", "body", "status", "cover"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "文章标题"}),
            "body": forms.Textarea(attrs={"rows": 12, "placeholder": "正文"}),
        }
        help_texts = {
            "cover": "可选。上传后会按 200px 宽自动生成缩略图。",
        }


class AttachmentForm(forms.ModelForm):
    """附件上传表单。"""

    class Meta:
        model = Attachment
        fields = ["file"]
