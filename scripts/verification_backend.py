"""Static backend impact selection. Shared or unresolved effects retain the suite."""

import ast
import re
import subprocess
from collections import defaultdict
from pathlib import PurePosixPath

PREFIX = "src/backend/"
PROTECTED = {"auth", "api_key", "user", "oauth", "admin", "billing", "billing_webhook"}
COMMON = {"tests/test_smoke.py", "tests/test_openapi_contract.py"}


def module_name(path):
    path = PurePosixPath(path)
    parts = path.with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def domain_of(module):
    for prefix in ("app.routers.v1.", "app.services.", "app.models.", "app.utils."):
        if module.startswith(prefix):
            return module[len(prefix) :].split(".")[0]
    return None


def imports(tree, module, known, package=False):
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parent = module.split(".") if package else module.split(".")[:-1]
                base = ".".join(
                    parent[: len(parent) - node.level + 1] + ([base] if base else [])
                )
            targets.add(base)
            targets.update(base + "." + alias.name for alias in node.names)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith(("app.", "tests."))
        ):
            targets.add(node.value)  # Mock/patch string references are consumers too.
    result = set()
    for name in targets:
        parts = name.split(".")
        result.update(
            ".".join(parts[:i])
            for i in range(1, len(parts) + 1)
            if ".".join(parts[:i]) in known
        )
    return result


def registration_only(before, after, added):
    """Recognize only appended registration of newly added router modules."""
    old, new = ast.parse(before), ast.parse(after)
    aliases = {}
    bound = {node.id for node in ast.walk(old) if isinstance(node, ast.Name)}
    for node in list(new.body):
        if isinstance(node, ast.ImportFrom) and node.module == "app.routers.v1":
            keep = []
            for alias in node.names:
                if alias.name in added and (alias.asname or alias.name) not in bound:
                    aliases[alias.asname or alias.name] = alias.name
                else:
                    keep.append(alias)
            node.names = keep
            if not keep:
                new.body.remove(node)
    if not aliases:
        return False
    wired = set()
    for function in new.body:
        if not isinstance(function, ast.FunctionDef) or function.name != "create_app":
            continue
        existing_last = -1
        remove = []
        for index, node in enumerate(function.body):
            call = node.value if isinstance(node, ast.Expr) else None
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "app"
                and call.func.attr == "include_router"
            ):
                continue
            router = call.args[0] if call.args else None
            if (
                isinstance(router, ast.Attribute)
                and router.attr == "router"
                and isinstance(router.value, ast.Name)
                and router.value.id in aliases
            ):
                if len(call.args) != 1 or not call.keywords:
                    return False
                try:
                    values = {
                        kw.arg: ast.literal_eval(kw.value) for kw in call.keywords
                    }
                except (ValueError, TypeError):
                    return False
                if (
                    set(values) - {"prefix", "tags", "include_in_schema", "deprecated"}
                    or not isinstance(values.get("prefix"), str)
                    or not values["prefix"].startswith("/api/")
                ):
                    return False
                remove.append((index, node))
                wired.add(router.value.id)
            else:
                existing_last = index
        if [index for index, _ in remove] != list(
            range(existing_last + 1, existing_last + 1 + len(remove))
        ):
            return (
                False  # Stay after existing routers and before static mounts/returns.
            )
        for _, node in remove:
            function.body.remove(node)
    return wired == set(aliases) and ast.dump(
        old, include_attributes=False
    ) == ast.dump(new, include_attributes=False)


def response_header_only(before, after):
    """Prove only a literal cache header changed; never infer arbitrary type purity."""

    def normalized(source):
        tree = ast.parse(source)
        aliases = set()
        constructors = {
            "Response",
            "JSONResponse",
            "PlainTextResponse",
            "HTMLResponse",
            "StreamingResponse",
            "FileResponse",
            "RedirectResponse",
        }
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module in {
                "fastapi",
                "fastapi.responses",
                "starlette.responses",
            }:
                aliases.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name in constructors
                )
        original = ast.dump(tree, include_attributes=False)
        bindings = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, ast.alias):
                bindings[node.asname or node.name.split(".")[0]] += 1
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                bindings[node.id] += 1
            elif isinstance(node, ast.arg):
                bindings[node.arg] += 1
            elif (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                or isinstance(node, ast.ExceptHandler)
                and node.name
            ):
                bindings[node.name] += 1
        aliases = {name for name in aliases if bindings[name] == 1}
        masked = 0
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in aliases
            ):
                continue
            for keyword in node.keywords:
                headers = keyword.value
                if keyword.arg != "headers" or not isinstance(headers, ast.Dict):
                    continue
                if not all(
                    isinstance(key, ast.Constant) and isinstance(key.value, str)
                    for key in headers.keys
                ):
                    continue
                for key, value in zip(headers.keys, headers.values):
                    if (
                        key.value.lower() == "cache-control"
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                    ):
                        value.value = "__verification_cache_header__"
                        masked += 1
        return ast.dump(tree, include_attributes=False), masked, original

    old, old_count, old_original = normalized(before)
    new, new_count, new_original = normalized(after)
    return (
        old_count > 0
        and old_count == new_count
        and old == new
        and old_original != new_original
    )


def backend_impact(root, base, head, paths, read):
    """Return real test files and reasons, or None for the complete backend suite."""
    changed = [
        path[len(PREFIX) :]
        for path in paths
        if path.startswith(PREFIX) and not path.endswith(".md")
    ]
    if not changed:
        return None
    try:
        inventory = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            text=True,
        ).split("\0")
        files = {
            path[len(PREFIX) :]
            for path in inventory
            if path.startswith(PREFIX) and path.endswith(".py")
        }
        if any(path not in files for path in changed):
            return None
        if any(
            path == "tests/conftest.py" or path.startswith("tests/fixtures/")
            for path in changed
        ):
            return None
        if any(not re.fullmatch(r"[\w./-]+", path) for path in changed):
            return None
        for path in changed:
            read(root, head, PREFIX + path)
        local_tests = set()
        for path in changed:
            if path.startswith("tests/") and PurePosixPath(path).name == "conftest.py":
                folder = str(PurePosixPath(path).parent) + "/"
                covered = {
                    name
                    for name in files
                    if name.startswith(folder)
                    and PurePosixPath(name).name.startswith("test_")
                }
                if not covered:
                    return None
                local_tests.update(covered)
        if all(
            path.startswith("tests/")
            and (
                PurePosixPath(path).name.startswith("test_")
                or PurePosixPath(path).name == "conftest.py"
            )
            for path in changed
        ):
            return {
                "tests": sorted(
                    local_tests
                    | {
                        path
                        for path in changed
                        if PurePosixPath(path).name.startswith("test_")
                    }
                ),
                "domains": [],
                "reason": "Changed test files and local fixture subtrees; no runtime changes",
            }
        modules = {module_name(path): path for path in files}
        trees = {
            name: ast.parse(read(root, head, PREFIX + path))
            for name, path in modules.items()
        }

        def uncertain(tree):
            return any(
                isinstance(node, ast.ImportFrom)
                and (
                    any(alias.name == "*" for alias in node.names)
                    or (node.module or "").startswith("importlib")
                )
                or isinstance(node, ast.Import)
                and any(alias.name.startswith("importlib") for alias in node.names)
                or isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
                for node in ast.walk(tree)
            )

        def orm(tree):
            return any(
                isinstance(node, ast.ImportFrom)
                and (
                    (node.module or "").startswith("sqlalchemy")
                    or (node.module or "").startswith("app.core.db")
                )
                or isinstance(node, ast.Import)
                and any(alias.name.startswith("sqlalchemy") for alias in node.names)
                or isinstance(node, ast.Name)
                and node.id
                in {"Mapped", "mapped_column", "__tablename__", "__table__", "Base"}
                for node in ast.walk(tree)
            )

        if any(
            uncertain(tree) for name, tree in trees.items() if name.startswith("app.")
        ):
            return None
        added_routers = set()
        transport_only = set()
        for path in changed:
            if path.startswith("app/routers/v1/"):
                try:
                    before = read(root, base, PREFIX + path)
                except (OSError, subprocess.CalledProcessError):
                    added_routers.add(PurePosixPath(path).stem)
                else:
                    if response_header_only(before, read(root, head, PREFIX + path)):
                        transport_only.add(module_name(path))
        if "app/main.py" in changed and not registration_only(
            read(root, base, PREFIX + "app/main.py"),
            read(root, head, PREFIX + "app/main.py"),
            added_routers,
        ):
            return None
        if added_routers and "app/main.py" not in changed:
            return None
        reverse = defaultdict(set)
        dependencies = {}
        for name, tree in trees.items():
            dependencies[name] = imports(
                tree, name, modules, modules[name].endswith("/__init__.py")
            )
            for dependency in dependencies[name]:
                if name != "app.main":
                    reverse[dependency].add(name)
        reached = {module_name(path) for path in changed if path != "app/main.py"}
        pending = list(reached)
        while pending:
            name = pending.pop()
            for consumer in reverse[name] - reached:
                reached.add(consumer)
                pending.append(consumer)

        def persistent_model(name, seen=None):
            seen = set() if seen is None else seen
            if name in seen:
                return False
            seen.add(name)
            return orm(trees[name]) or any(
                target.startswith("app.core.db")
                or target.startswith("app.models.")
                and persistent_model(target, seen)
                for target in dependencies[name]
            )

        domains = set()
        needs_integration = set()
        router_domains = set()
        for name in reached:
            if not name.startswith("app."):
                continue
            domain = domain_of(name)
            if (
                domain is None
                or domain in PROTECTED
                or modules[name].endswith("/__init__.py")
            ):
                return None
            tree = trees[name]
            if any(
                isinstance(node, ast.ImportFrom)
                and any(alias.name == "*" for alias in node.names)
                for node in ast.walk(tree)
            ):
                return None
            if any(
                isinstance(node, ast.Call)
                and (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "__import__"
                    or isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                )
                for node in ast.walk(tree)
            ):
                return None
            if name.startswith("app.models.") and persistent_model(name):
                return None  # ORM/model/migration changes are intentionally broad.
            domains.add(domain)
            if name.startswith("app.routers.v1."):
                router_domains.add(domain)
            if name not in transport_only and (
                any(
                    target.startswith("app.core.db")
                    or target.startswith("app.models.")
                    and persistent_model(target)
                    for target in dependencies[name]
                )
                or any(
                    isinstance(node, ast.ImportFrom)
                    and (node.module or "").startswith("sqlalchemy")
                    for node in ast.walk(tree)
                )
            ):
                needs_integration.add(domain)
        tests = local_tests | {
            modules[name]
            for name in reached
            if modules[name].startswith("tests/")
            and PurePosixPath(modules[name]).name.startswith("test_")
        }
        for domain in domains:
            owned = {
                path
                for path in files
                if path.startswith("tests/")
                and PurePosixPath(path).name.startswith("test_")
                and (
                    f"/{domain}/" in path
                    or PurePosixPath(path).name == f"test_{domain}.py"
                    or PurePosixPath(path).name.startswith(f"test_{domain}_")
                )
            }
            if domain in router_domains and not any(
                path.startswith(("tests/api/", "tests/integration/api/"))
                for path in owned
            ):
                return None
            if (
                not owned
                or domain in needs_integration
                and not any(path.startswith("tests/integration/") for path in owned)
            ):
                return None
            tests.update(owned)
        if not domains and not tests:
            return None
        if domains:
            tests.update(COMMON)
        if any(
            path not in files or not re.fullmatch(r"[\w./-]+", path) for path in tests
        ):
            return None
        return {
            "tests": sorted(tests),
            "domains": sorted(domains),
            "reason": "Static import consumers and existing domain test files; smoke/OpenAPI retained",
            "response_header_only": sorted(transport_only),
        }
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError):
        return None
