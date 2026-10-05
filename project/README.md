# 工程题 A：文章管理系统（数据层）

用 Django 实现的文章管理系统**数据层**：文章模型、附件管理、**信号驱动的操作审计**、**并发安全的浏览量**。

> 本题为扩展题（A / B 二选一），本目录实现的是 **A：数据层**。
> 开发在功能分支 `feature/project-a-article-data-layer` 上进行，完成后经 Pull Request 合并回 `main`。

## 一、快速开始

```bash
cd project

# 1. 建虚拟环境并装依赖
python -m venv .venv
.venv/Scripts/activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

# 2. 建表
python manage.py migrate

# 3. （可选）建个后台账号，方便在 Admin 里看数据
python manage.py createsuperuser

# 4. 跑测试（50 条）
python manage.py test blog -v 2

# 5. 起服务
python manage.py runserver
```

打开 <http://127.0.0.1:8000/>。首次使用先到 <http://127.0.0.1:8000/accounts/register/> 注册账号，再登录写文章。

### 依赖

| 包 | 版本 | 用途 |
| --- | --- | --- |
| Django | `>=5.1,<6.0` | Web 框架 |
| Pillow | `>=10.0` | 封面图缩略图（加分项 1）；`ImageField` 必需 |
| tzdata | Windows 专用 | `USE_TZ=True` + `Asia/Shanghai` 需要 |

## 二、功能清单

### 必须实现

| # | 需求 | 实现位置 |
| --- | --- | --- |
| 1 | 数据模型：`Article` / `Attachment` / `AuditLog`，含 `__str__`、`Meta` 排序、`verbose_name` | `blog/models.py` |
| 2 | 登录用户可为**自己的**文章上传附件；详情页展示附件列表；作者可删除自己的附件；`MEDIA_URL` / `MEDIA_ROOT` 配置并可访问 | `blog/views.py`、`config/settings.py`、`config/urls.py` |
| 3 | 文章创建 / 状态变更 / 删除自动写审计日志；**必须用信号**（`post_save` / `pre_delete`），视图中不得手工 `AuditLog.objects.create`；变更摘要用 `JSONField` 记录前后差异；详情页展示审计日志（倒序） | `blog/signals.py` |
| 4 | 详情页每次访问浏览量 +1，**必须用 `F("views") + 1` 原子更新**，并注释说明为什么 `article.views += 1; article.save()` 会丢更新 | `blog/models.py:Article.increase_views`、`blog/views.py:article_detail` |

### 加分项（四个全部实现）

| # | 加分项 | 实现方式 |
| --- | --- | --- |
| 1 | 封面图缩略图 | 上传时用 Pillow 生成 200px 宽缩略图，存到 `MEDIA_ROOT/thumbnails/`（`blog/thumbnails.py`） |
| 2 | 文章统计视图 `/stats/` | 总文章数、总浏览量、各状态文章数、最近 10 条审计日志 |
| 3 | 软删除 | `Article.is_deleted`，删除只打标记，内容与审计日志都保留，列表页过滤 |
| 4 | 附件下载计数 | 每次下载 `F("downloads") + 1`，展示在附件列表 |

### 额外补充（题目未要求，但缺少就没法正常演示）

- 用户注册 / 登录 / 登出（`UserCreationForm` + `set_password` 哈希，绝无明文）
- 文章新建 / 编辑（作者强制为当前登录用户，前端伪造 `author` 无效）
- 文章列表：按状态 / 作者筛选 + 标题 `icontains` 搜索 + 每页 10 条分页

## 三、目录结构

```
project/
├── README.md
├── requirements.txt
├── manage.py
├── config/                     # Django 工程配置
│   ├── settings.py             #   含 MEDIA 配置、中间件注册
│   ├── urls.py                 #   /admin/、/accounts/、MEDIA 静态服务
│   ├── wsgi.py / asgi.py
├── blog/                       # 业务应用
│   ├── models.py               #   Article / Attachment / AuditLog + F() 自增
│   ├── signals.py              #   ★ 信号驱动的审计日志
│   ├── middleware.py           #   把 request.user 放进 thread-local
│   ├── thumbnails.py           #   Pillow 生成 200px 缩略图
│   ├── views.py                #   视图（不含任何 AuditLog.objects.create）
│   ├── forms.py / urls.py / admin.py
│   ├── migrations/0001_initial.py
│   ├── templates/              #   base / 列表 / 详情 / 表单 / 统计 / 登录注册
│   └── tests.py                #   50 条测试
└── media/                      # 上传文件（.gitignore 已忽略）
```

## 四、关键设计说明

### 4.1 为什么审计要用信号，而不是在视图里 `create`

真实项目里文章的写入路径不止视图一条——还有 Django Admin、`manage.py shell`、数据迁移、后台任务、测试夹具。把审计写在视图里，**必然**出现"某个路径忘了记"的漏 auditing。信号挂在模型层，任何写入路径都会触发；视图只负责业务逻辑与权限。

本项目 `blog/views.py` 里没有一处 `AuditLog.objects.create`，可以全文搜索验证。

### 4.2 信号拿不到 `request`，"操作人"怎么记

`blog/middleware.py` 里的 `CurrentUserMiddleware`（在 `AuthenticationMiddleware` **之后**）在每次请求进入时把 `request.user` 存进 thread-local，`blog/signals.py` 通过 `get_current_user()` 取出。

- 请求同线程 → 视图引发的写入都能正确记到操作人（有测试覆盖：登录用户 POST 创建文章 → 审计日志 `operator` 是该用户）；
- shell / 后台任务没有请求上下文 → 取到 `None`，`operator` 记为 NULL，表示"系统操作"。

**局限**（写在代码注释里）：thread-local 只在同线程内有效，跨线程 / 异步任务需要另想办法（显式传参或 `contextvars`）。

### 4.3 变更前后差异怎么算

`post_save` 只能看到"保存之后"的对象，拿不到旧值。所以：

1. `pre_save` 先把库里的旧值快照到 `instance._old_values`（`update_fields` 明显不含被跟踪字段时直接跳过，省一次查询）；
2. `post_save` 逐字段比对 `TRACKED_FIELDS = ("title", "body", "status", "is_deleted")`，把差异写进 `AuditLog.changes`。

得到的形状和题目要求完全一致：

```python
{"status": {"old": "draft", "new": "published"}}
```

**为什么 `views` 不在 `TRACKED_FIELDS` 里**：浏览量是高频自增，记进审计会把日志表刷爆；而且 `views` 走的是 `F()` 的 `QuerySet.update()`，压根不会触发 `post_save`。

**动作判定优先级**：`is_deleted` 由 False 变 True → `delete`；否则看 `status`：→ `published` 记 `publish`、→ `archived` 记 `archive`、其余记 `update`；只改标题 / 正文 → `update`。

### 4.4 并发安全的浏览量

```python
# ❌ 会丢更新
article.views += 1
article.save()

# ✅ 原子自增
Article.objects.filter(pk=pk).update(views=F("views") + 1)
```

`views += 1; save()` 是**读 → 改 → 写**三步，在 Python 侧完成，并发下两个请求会这样交错：

```
请求 A: 读 views=10          → 写 views=11
请求 B:          读 views=10  → 写 views=11
```

两次访问只加了 1 —— 这就是**丢失更新**。而且 `save()` 是整行回写，还会顺手覆盖别人对标题、状态的修改。

`F("views") + 1` 不会被求值成具体数字，而是编译成 `SET views = views + 1` 交给数据库在同一条语句里原子执行。

**实测（8 线程 × 200 次 = 1600 次并发访问，SQLite）：**

| 写法 | 期望 | 实际 | 丢失 |
| --- | --- | --- | --- |
| `article.views += 1; article.save()` | 1600 | **200** | 1400（87.5%） |
| `Article.objects.filter(...).update(views=F("views") + 1)` | 1600 | **1600** | 0 |

另外两种写法产生的审计日志都是 **0 条**，印证了 4.3 中"`F()` 自增不触发 `post_save`、不会刷爆日志表"。

### 4.5 软删除也要能被信号捕获

软删除不执行 `DELETE`，所以 `pre_delete` 不会触发。做法是让软删除走 `Article.soft_delete()` → `save(update_fields=["is_deleted", ...])`，`post_save` 检测到 `is_deleted` 由 False 变 True，判定动作是 `delete` 并写日志。

真正的硬删除（`article.delete()`）由 `pre_delete` 兜底：先写一条 `action=delete` 的日志，再把文章删掉。因为 `AuditLog.article` 是 `SET_NULL`，文章行消失后日志依然在，只是 `article` 变成 NULL，标题冗余记在 `changes` 里便于追溯。

### 4.6 缩略图为什么不递归

生成缩略图如果调用 `instance.save()`，会再次触发 `post_save`，而 `post_save` 又调生成缩略图 → 无限递归。所以 `make_thumbnail()` 把文件落到 storage 后用 `QuerySet.update()` 写回字段名——`update()` 不发信号。同时函数是**幂等**的（已有缩略图直接返回 `False`），原图比 200px 窄时不放大。

## 五、URL 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 文章列表（`?status=` `?author=` `?q=` `?page=`） |
| GET | `/articles/<id>/` | 文章详情（浏览量 +1、附件、审计日志） |
| GET/POST | `/articles/new/` | 新建文章（需登录） |
| GET/POST | `/articles/<id>/edit/` | 编辑（仅作者） |
| POST | `/articles/<id>/delete/` | 软删除（仅作者） |
| POST | `/articles/<id>/attachments/upload/` | 上传附件（仅作者） |
| POST | `/attachments/<id>/delete/` | 删除附件（仅作者） |
| GET | `/attachments/<id>/download/` | 下载附件（计数 +1） |
| GET | `/stats/` | 统计（需登录） |
| GET/POST | `/accounts/register/` `/accounts/login/` | 注册 / 登录 |
| — | `/admin/` | Django Admin（审计日志只读） |

## 六、测试

```bash
python manage.py test blog -v 2
```

**50 条测试全部通过**，覆盖：

- 模型：`__str__`、`Meta` 排序、`verbose_name`、`related_name`、级联删除
- **信号审计**：创建 / 发布 / 归档 / 回退 / 改字段 / 无变化不写 / 软删除 / 硬删除 / 只改封面不写 / `operator` 来自中间件 / 无请求上下文时为 NULL
- **并发浏览量**：`F()` 精确计数、naive 写法丢更新的复现、详情页逐次 +1
- **附件**：作者上传成功、非作者 403、匿名跳登录、删除权限、下载计数、无文件报错、MEDIA 配置
- **缩略图**：200px 宽、小图不放大、幂等、不递归、详情页展示
- 列表筛选 / 搜索 / 分页、统计聚合、注册密码哈希

## 七、已知局限

- `SECRET_KEY` 与 `DEBUG=True` 是演示配置，生产必须从环境变量读取并关掉 `DEBUG`；
- 数据库用 SQLite（作业方便），生产建议 PostgreSQL；
- 权限只有"登录 + 作者本人"，没有更细的角色模型；
- `/stats/` 用 `Sum` 聚合，文章量极大时应改成缓存或定期物化，否则每次访问都全表聚合。
