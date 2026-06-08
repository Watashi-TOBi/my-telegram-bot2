import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(_DATA_DIR, exist_ok=True)


def _path(chat_id: int) -> str:
    return os.path.join(_DATA_DIR, f"{chat_id}.json")


def load(chat_id: int) -> dict:
    try:
        with open(_path(chat_id)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(chat_id: int, data: dict) -> None:
    with open(_path(chat_id), "w") as f:
        json.dump(data, f, indent=2)


def get(chat_id: int, key: str, default=None):
    return load(chat_id).get(key, default)


def set_key(chat_id: int, key: str, value) -> None:
    data = load(chat_id)
    data[key] = value
    save(chat_id, data)
