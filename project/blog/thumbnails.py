# -*- coding: utf-8 -*-
"""封面图缩略图生成（加分项 1）。

用 Pillow 把封面图等比缩放到宽 200px，存到 ``MEDIA_ROOT/thumbnails/``。

设计约束
--------
- **幂等**：没有封面图、或已有缩略图时直接返回 ``False``，可以安全地重复调用；
- **不触发信号递归**：写回用 ``QuerySet.update()`` 而不是 ``instance.save()``，
  因此不会再触发 ``post_save`` 造成无限循环；
- **不放大**：原图本来比 200px 窄时原样保留尺寸，避免把小图拉糊。
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile

THUMBNAIL_WIDTH = 200
THUMBNAIL_FORMAT = "JPEG"
THUMBNAIL_QUALITY = 85


def make_thumbnail(article) -> bool:
    """为 ``article.cover`` 生成宽 200px 的缩略图并写入 ``article.thumbnail``。

    Args:
        article: :class:`blog.models.Article` 实例。

    Returns:
        ``True``  生成了缩略图；
        ``False`` 没有封面图、已有缩略图、图片无法解析，或环境缺少 Pillow。
    """
    if not article.pk or not article.cover or article.thumbnail:
        return False

    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - requirements.txt 已声明 Pillow
        return False

    cover_name = article.cover.name
    try:
        article.cover.open("rb")
    except OSError:
        return False

    try:
        with Image.open(article.cover) as image:
            # PNG 的透明通道无法存成 JPEG，统一转 RGB
            image = image.convert("RGB")
            if image.width > THUMBNAIL_WIDTH:
                height = max(1, round(image.height * THUMBNAIL_WIDTH / image.width))
                image = image.resize((THUMBNAIL_WIDTH, height), Image.LANCZOS)

            buffer = BytesIO()
            image.save(buffer, format=THUMBNAIL_FORMAT, quality=THUMBNAIL_QUALITY)
    except Exception:  # noqa: BLE001 - 不是能解析的图片就别拦住文章保存
        return False
    finally:
        article.cover.close()

    stem = Path(cover_name).stem
    # save=False：先把文件落到 storage 并给字段赋值，但不触发 save()
    article.thumbnail.save(f"{stem}_thumb.jpg", ContentFile(buffer.getvalue()), save=False)
    # 用 QuerySet.update() 落库：不触发 post_save，因此不会递归调用本函数
    type(article).objects.filter(pk=article.pk).update(thumbnail=article.thumbnail.name)
    return True
