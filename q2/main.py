import json


class UserManager:
    def __init__(self):
        self.users = []
        self.next_id = 1

    def _find(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None

    def add_user(self, name, age):
        user = {"id": self.next_id, "name": name, "age": age}
        self.users.append(user)
        self.next_id += 1
        return user

    def get_user(self, user_id):
        return self._find(user_id)

    def update_age(self, user_id, age):
        user = self._find(user_id)
        if user is None:
            return False
        user["age"] = age
        return True

    def remove_user(self, user_id):
        user = self._find(user_id)
        if user is None:
            return False
        self.users.remove(user)
        return True

    def list_users(self):
        return self.users

    def save_to_json(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False)

    def load_from_json(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.users = json.load(f)
        # 接续已加载的最大 id。不能写 len(self.users) + 1：
        # id 不连续时（比如删过中间的用户）会算出已被占用的 id，导致重复。
        self.next_id = max((user["id"] for user in self.users), default=0) + 1
