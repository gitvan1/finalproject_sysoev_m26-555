import json
import os


def load_json(path: str) -> dict | None:
    """Загрузка данных из JSON-файла"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data) -> None:
    """Сохранение данных в JSON-файл"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def next_user_id(users: list[dict]) -> int:
    """Автоинкремент"""
    return max((u["user_id"] for u in users), default=0) + 1
