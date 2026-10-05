# qz2026-xuzixiang

中国海洋大学 ITStudio 程序部 · 2026 国庆题目作答。

## 目录结构

```
.
├── README.md          # 本文件：仓库说明
├── written.md         # 选择题（10 题）+ 简答题（3 题）答案
├── q1/                # 编程题 1：JSON 日志管道
│   ├── main.py        #   analyze_log() 实现
│   ├── test.py        #   unittest 用例
│   └── app.jsonl      #   示例日志文件
└── q2/                # 编程题 2：用户管理器
    ├── main.py        #   UserManager 实现
    └── test.py        #   unittest 用例
```

## 运行方式

编程题（纯标准库，无第三方依赖）：

```bash
cd q1 && python test.py
cd q2 && python test.py
```

## 自证

不是"应该能跑"，是跑过的：

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| 选择题答案 | 逐题实跑 10 段代码比对输出 | 10/10 与 `written.md` 一致 |
| q1 | `cd q1 && python test.py` | **10 tests OK** |
| q2 | `cd q2 && python test.py` | **14 tests OK** |

## 说明

- 全仓库不含 `__pycache__/`、虚拟环境、数据库等产物（见 `.gitignore`）。
- 提交历史按「一小步一个 commit」推进。
