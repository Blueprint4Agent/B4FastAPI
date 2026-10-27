"""Pure parsing helpers shared by billing use cases; no provider I/O or policy."""


def _mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def subscription_price_id(obj: dict) -> str:
    items = _mapping(obj.get("items")).get("data", [])
    if not isinstance(items, list) or len(items) != 1:
        return ""
    return _mapping(_mapping(items[0]).get("price")).get("id", "")
