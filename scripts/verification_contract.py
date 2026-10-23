"""Strict additive provider compatibility; existing consumer fragments stay exact."""

import json
from pathlib import Path
import sys

METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def same_json(left, right):
    # Python equality conflates True with 1; JSON contract identity must not.
    try:
        return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
            right, sort_keys=True, allow_nan=False
        )
    except (TypeError, ValueError):
        return False


def additive_contract(consumer, provider):
    """Allow new operations/components, never infer compatibility of changed schemas."""
    if not isinstance(consumer, dict) or not isinstance(provider, dict):
        return False
    if not same_json(
        {k: v for k, v in consumer.items() if k not in {"paths", "components"}},
        {k: v for k, v in provider.items() if k not in {"paths", "components"}},
    ):
        return False
    old_paths, new_paths = consumer.get("paths", {}), provider.get("paths", {})
    if not isinstance(old_paths, dict) or not isinstance(new_paths, dict):
        return False
    for path, item in old_paths.items():
        actual = new_paths.get(path)
        if not isinstance(item, dict) or not isinstance(actual, dict):
            return False
        if any(
            key not in actual or not same_json(actual[key], value)
            for key, value in item.items()
        ):
            return False
        if set(actual) - set(item) - METHODS:
            return (
                False  # New inherited parameters/servers could affect old operations.
            )
    old_components = consumer.get("components", {})
    new_components = provider.get("components", {})
    if not isinstance(old_components, dict) or not isinstance(new_components, dict):
        return False
    for group, entries in old_components.items():
        actual = new_components.get(group)
        if not isinstance(entries, dict) or not isinstance(actual, dict):
            return False
        if any(
            key not in actual or not same_json(actual[key], value)
            for key, value in entries.items()
        ):
            return False
    return True


def main():
    provider, consumer = (json.loads(Path(name).read_text()) for name in sys.argv[1:])
    if not additive_contract(consumer, provider):
        raise ValueError(
            "Provider changes the pinned B4React contract; coordinate consumer adoption before integrating."
        )
    print(
        "Provider preserves the pinned B4React contract; additive operations/components are allowed."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
