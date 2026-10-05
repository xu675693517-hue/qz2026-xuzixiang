# -*- coding: utf-8 -*-
"""q2 的单元测试。

覆盖题目"行为示例"的每一步，并补齐边界：id 不复用、**加载后 id 接续最大 id**、
加载覆盖旧数据、空数组加载、中文不转义、实例之间互不干扰等。

运行：

    cd q2
    python test.py
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from main import UserManager


class UserManagerTestCase(unittest.TestCase):
    """UserManager 的行为测试。"""

    def temp_path(self, suffix: str = ".json") -> str:
        """返回一个临时文件路径，测试结束自动删除（若已创建）。"""
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def setUp(self) -> None:
        self.um = UserManager()

    # ---------- 添加 / 查询 ----------

    def test_add_user_assigns_incrementing_ids(self):
        """id 从 1 开始按添加顺序递增，返回新建的字典。"""
        self.assertEqual(self.um.add_user("张三", 18), {"id": 1, "name": "张三", "age": 18})
        self.assertEqual(self.um.add_user("李四", 20), {"id": 2, "name": "李四", "age": 20})

    def test_get_user_existing_and_missing(self):
        """查得到返回字典，查不到返回 None。"""
        self.um.add_user("张三", 18)
        self.assertEqual(self.um.get_user(1), {"id": 1, "name": "张三", "age": 18})
        self.assertIsNone(self.um.get_user(99))

    # ---------- 修改 ----------

    def test_update_age_success_and_failure(self):
        """成功 True 且真的改了；不存在 False。"""
        self.um.add_user("张三", 18)
        self.assertTrue(self.um.update_age(1, 19))
        self.assertEqual(self.um.get_user(1)["age"], 19)
        self.assertFalse(self.um.update_age(99, 19))

    def test_update_age_failure_does_not_create_user(self):
        """对不存在的 id 更新年龄不会凭空造出用户。"""
        self.assertFalse(self.um.update_age(42, 30))
        self.assertIsNone(self.um.get_user(42))
        self.assertEqual(self.um.list_users(), [])

    # ---------- 删除 ----------

    def test_remove_user_success_then_failure(self):
        """第一次删成功，第二次删同一个 id 返回 False。"""
        self.um.add_user("张三", 18)
        self.um.add_user("李四", 20)
        self.assertTrue(self.um.remove_user(2))
        self.assertFalse(self.um.remove_user(2))

    def test_removed_id_is_not_reused(self):
        """删掉 id=1 后新增用户拿到 3，不复用 1（避免歧义）。"""
        self.um.add_user("张三", 18)
        self.um.add_user("李四", 20)
        self.um.remove_user(1)
        self.assertEqual(self.um.add_user("王五", 30)["id"], 3)

    # ---------- 列表 ----------

    def test_list_users_keeps_insertion_order(self):
        """按添加顺序返回。"""
        self.um.add_user("张三", 18)
        self.um.add_user("李四", 20)
        self.um.add_user("王五", 30)
        self.assertEqual([u["name"] for u in self.um.list_users()], ["张三", "李四", "王五"])

    # ---------- 持久化 ----------

    def test_save_and_load_roundtrip(self):
        """保存再加载，数据完全一致。"""
        self.um.add_user("张三", 18)
        self.um.add_user("李四", 20)
        path = self.temp_path()
        self.um.save_to_json(path)

        other = UserManager()
        other.load_from_json(path)
        self.assertEqual(other.list_users(), self.um.list_users())

    def test_load_then_add_continues_from_max_id(self):
        """加载已有文件后，新增用户的 id 必须接续**最大** id，而不是元素个数 + 1。

        这里特意制造 id 不连续的情况（id 变成 [2, 3]，元素个数只有 2）。
        若写成 `len(users) + 1` 会算出 3，与已存在的 id=3 撞车。
        """
        self.um.add_user("张三", 18)
        self.um.add_user("李四", 20)
        self.um.add_user("王五", 30)
        self.um.remove_user(1)  # 删掉第一个，id 变成 [2, 3]

        path = self.temp_path()
        self.um.save_to_json(path)

        other = UserManager()
        other.load_from_json(path)
        self.assertEqual([u["id"] for u in other.list_users()], [2, 3])

        new_user = other.add_user("赵六", 40)
        self.assertEqual(new_user["id"], 4)  # 不是 3
        ids = [u["id"] for u in other.list_users()]
        self.assertEqual(ids, [2, 3, 4])
        self.assertEqual(len(ids), len(set(ids)))  # 没有重复 id

    def test_load_overwrites_current_data(self):
        """加载会覆盖当前内存数据，而不是追加。"""
        self.um.add_user("旧的", 1)
        path = self.temp_path()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([{"id": 7, "name": "新的", "age": 70}], fh, ensure_ascii=False)

        self.um.load_from_json(path)
        self.assertEqual(self.um.list_users(), [{"id": 7, "name": "新的", "age": 70}])
        self.assertEqual(self.um.add_user("再加", 2)["id"], 8)

    def test_load_empty_list(self):
        """加载空数组：清空并让 id 从 1 重新开始。"""
        self.um.add_user("张三", 18)
        path = self.temp_path()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("[]")

        self.um.load_from_json(path)
        self.assertEqual(self.um.list_users(), [])
        self.assertEqual(self.um.add_user("新", 1)["id"], 1)

    def test_saved_file_is_utf8_and_unescaped(self):
        """落盘文件是 UTF-8 且中文不被转义成 \\uXXXX。"""
        self.um.add_user("张三", 18)
        path = self.temp_path()
        self.um.save_to_json(path)

        raw = open(path, "r", encoding="utf-8").read()
        self.assertIn("张三", raw)
        self.assertNotIn("\\u", raw)
        self.assertEqual(json.loads(raw), [{"id": 1, "name": "张三", "age": 18}])

    def test_two_managers_are_independent(self):
        """两个实例互不干扰（数据存在实例上，不是类属性）。"""
        other = UserManager()
        self.um.add_user("张三", 18)
        self.assertEqual(other.list_users(), [])
        self.assertEqual(other.add_user("李四", 20)["id"], 1)

    # ---------- 题目"行为示例"整体串跑 ----------

    def test_full_behaviour_example(self):
        """照题目行为示例逐步断言一遍。"""
        um = UserManager()
        self.assertEqual(um.add_user("张三", 18), {"id": 1, "name": "张三", "age": 18})
        self.assertEqual(um.add_user("李四", 20), {"id": 2, "name": "李四", "age": 20})
        self.assertEqual(um.get_user(1), {"id": 1, "name": "张三", "age": 18})
        self.assertIsNone(um.get_user(99))
        self.assertTrue(um.update_age(1, 19))
        self.assertTrue(um.remove_user(2))
        self.assertFalse(um.remove_user(2))
        self.assertEqual(um.list_users(), [{"id": 1, "name": "张三", "age": 19}])

        path = self.temp_path()
        um.save_to_json(path)
        um2 = UserManager()
        um2.load_from_json(path)
        self.assertEqual(um2.list_users(), [{"id": 1, "name": "张三", "age": 19}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
