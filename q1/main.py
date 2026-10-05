import json
import os


def analyze_log(filepath):
    result = {"total": 0, "by_level": {}, "by_user": {}, "last_error": None}

    if not os.path.exists(filepath):
        return result

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            result["total"] += 1
            level = data.get("level")
            user = data.get("user")

            result["by_level"][level] = result["by_level"].get(level, 0) + 1
            result["by_user"][user] = result["by_user"].get(user, 0) + 1

            if level == "ERROR":
                result["last_error"] = data.get("message")

    return result
