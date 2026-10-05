# qz2026-xuzixiang

中国海洋大学 ITStudio 程序部 · 2026 国庆题目作答。

## 目录结构

```
.
├── README.md          # 本文件：仓库说明
├── written.md         # 选择题（10 题）+ 简答题（3 题）答案
├── q1/                # 编程题 1：JSON 日志管道
│   ├── main.py        #   analyze_log() 实现
│   └── test.py        #   unittest 用例（覆盖题目 4 个示例 + 边界）
├── q2/                # 编程题 2：用户管理器
│   ├── main.py        #   UserManager 实现
│   └── test.py        #   unittest 用例（覆盖题目行为示例 + 边界）
└── project/           # 工程题 A：文章管理系统（数据层）
    ├── README.md      #   功能列表、依赖、运行方式
    ├── requirements.txt
    ├── manage.py
    ├── config/        #   Django 项目配置
    └── blog/          #   业务 app（模型 / 信号 / 视图 / 模板）
```

## 运行方式

编程题（纯标准库，无第三方依赖）：

```bash
cd q1 && python test.py
cd q2 && python test.py
```

工程题（Django，需先装依赖）：

```bash
cd project
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

详见各目录下的说明。

## 自证

不是"应该能跑"，是跑过的：

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| 选择题答案 | 逐题实跑 10 段代码比对输出 | 10/10 与 `written.md` 一致 |
| q1 | `cd q1 && python test.py` | **13 tests OK** |
| q2 | `cd q2 && python test.py` | **16 tests OK** |
| project-a | `cd project && python manage.py test blog` | **50 tests OK** |
| project-a 建表 | `python manage.py migrate` | OK |
| 并发浏览量 | 8 线程 × 200 次 = 1600 次访问 | `views += 1; save()` → **200**（丢 87.5%）；`F("views") + 1` → **1600** |
| 操作人链路 | 真实 HTTP 登录 + POST（非测试客户端） | 审计日志 `operator` = `xuzixiang`，`changes` 含 `status: draft → published` |

## 说明

- 全仓库不含 `__pycache__/`、`venv/`、数据库、`media/` 等产物（见 `.gitignore`）。
- 提交历史按「一小步一个 commit」推进；工程题 A 在功能分支 `feature/project-a-article-data-layer`
  上开发（9 个提交），完成后经 Pull Request 合并回 `main`（见 `729171b` 合并提交）。
- 工程题 A/B 二选一，本仓库选做 **A（数据层）**。
