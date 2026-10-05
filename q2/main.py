# -*- coding: utf-8 -*-
"""编程题 2：用户管理器。

实现一个管理用户数据增删查改并支持 JSON 文件持久化的类。每个用户是一个字典::

    {"id": 1, "name": "张三", "age": 18}

``id`` 由管理器自动分配，从 1 开始递增；从文件加载后，后续新增接续已加载的最大 id。

设计要点
--------
- 内部用 ``dict[int, dict]`` 存储：Python 3.7+ 保证字典保持插入顺序，
  天然满足"列出所有用户按添加顺序"的要求，同时 ``id -> user`` 查询是 O(1)。
- ``_next_id`` 显式维护，避免"删除后 id 被复用"。
- ``list_users`` 返回副本，防止调用方拿到内部可变对象后误改内部状态。
- 持久化要求 ``encoding="utf-8"`` 且 ``ensure_ascii=False``（中文不转义）。

直接运行：

    python main.py
"""

from __future__ import annotations

import json


class UserManager:
    """内存中的用户集合，可保存到 / 从 JSON 文件加载。"""

    def __init__(self) -> None:
        # id -> user；依靠 dict 的插入顺序保存"添加顺序"
        self._users: dict[int, dict] = {}
        # 下一个待分配的 id（删除用户不会回收 id，避免 id 复用造成歧义）
        self._next_id: int = 1

    # ------------------------------------------------------------------
    # 增删查改
    # ------------------------------------------------------------------

    def add_user(self, name: str, age: int) -> dict:
        """添加一个用户，自动分配 id，返回新建的用户字典。

        Args:
            name: 用户名。
            age: 年龄。

        Returns:
            形如 ``{"id": 1, "name": "张三", "age": 18}`` 的新字典。
        """
        user = {"id": self._next_id, "name": name, "age": age}
        self._users[user["id"]] = user
        self._next_id += 1
        return user

    def get_user(self, user_id: int) -> dict | None:
        """按 id 查询用户。

        返回的是**副本**（与 ``list_users`` 保持一致）：调用方拿到后随便改
        都不会污染管理器内部数据，要真正修改请用 :meth:`update_age`。

        Returns:
            用户字典的副本；id 不存在返回 ``None``。
        """
        user = self._users.get(user_id)
        return dict(user) if user is not None else None

    def update_age(self, user_id: int, age: int) -> bool:
        """修改指定用户的年龄。

        Returns:
            成功返回 ``True``；用户不存在返回 ``False``。
        """
        user = self._users.get(user_id)
        if user is None:
            return False
        user["age"] = age
        return True

    def remove_user(self, user_id: int) -> bool:
        """删除指定用户。

        Returns:
            成功返回 ``True``；用户不存在返回 ``False``。
        """
        if user_id not in self._users:
            return False
        del self._users[user_id]
        return True

    def list_users(self) -> list[dict]:
        """按添加顺序返回所有用户。

        返回的是**副本**列表（每个元素也是新的 dict），
        调用方修改返回值不会影响管理器内部数据。
        """
        return [dict(user) for user in self._users.values()]

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def save_to_json(self, filepath: str) -> None:
        """把所有用户写入 JSON 文件（UTF-8，中文不转义）。

        Args:
            filepath: 目标文件路径。
        """
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(self.list_users(), fh, ensure_ascii=False, indent=2)

    def load_from_json(self, filepath: str) -> None:
        """从 JSON 文件加载用户，**覆盖**当前内存数据。

        加载完成后，``_next_id`` 接续文件中最大的 id，保证后续新增的 id 不冲突。

        Args:
            filepath: 源文件路径。

        Raises:
            FileNotFoundError: 文件不存在（调用方需保证路径有效）。
            json.JSONDecodeError: 文件内容不是合法 JSON。
        """
        with open(filepath, "r", encoding="utf-8") as fh:
            users = json.load(fh)

        self._users = {user["id"]: user for user in users}
        # max(..., default=0) 让空列表也能正确处理，得到 _next_id = 1
        self._next_id = max(self._users, default=0) + 1

    # 方便调试 / 交互时直接 print(um)
    def __repr__(self) -> str:
        return f"UserManager(users={self.list_users()!r})"


def demo() -> None:
    """按题目"行为示例"跑一遍，便于直接 `python main.py` 观察。"""
    um = UserManager()
    print("add_user('张三', 18) ->", um.add_user("张三", 18))
    print("add_user('李四', 20) ->", um.add_user("李四", 20))
    print("get_user(1)          ->", um.get_user(1))
    print("get_user(99)         ->", um.get_user(99))
    print("update_age(1, 19)    ->", um.update_age(1, 19))
    print("remove_user(2)       ->", um.remove_user(2))
    print("remove_user(2)       ->", um.remove_user(2))
    print("list_users()         ->", um.list_users())

    path = "users.json"
    um.save_to_json(path)
    print(f"save_to_json('{path}') 完成")

    um2 = UserManager()
    um2.load_from_json(path)
    print("um2.list_users()     ->", um2.list_users())
    print("um2.add_user('王五', 30) ->", um2.add_user("王五", 30), "(id 接续最大值 2)")


if __name__ == "__main__":
    demo()
