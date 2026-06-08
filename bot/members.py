from .storage import load, save


def track(chat_id: int, user_id: int, first_name: str) -> None:
    """Record a group member so /crush can pick them later."""
    data = load(chat_id)
    members = data.get("members", {})
    members[str(user_id)] = first_name
    data["members"] = members
    save(chat_id, data)


def get_members(chat_id: int) -> dict:
    """Return {user_id_str: first_name} for all known group members."""
    return load(chat_id).get("members", {})
