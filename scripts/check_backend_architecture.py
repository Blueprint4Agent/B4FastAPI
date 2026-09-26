#!/usr/bin/env python3
"""Check explicit Python import boundaries without importing application code."""

import ast
from importlib.util import resolve_name
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src/backend/app"
DB_MODULES = (
    "app.core.db",
    "sqlalchemy",
    "sqlite3",
    "aiosqlite",
    "asyncpg",
    "psycopg",
    "psycopg2",
    "databases",
)
SCHEMA_BASES = {"pydantic.BaseModel", "enum.Enum", "enum.StrEnum", "enum.IntEnum"}


def within(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def imports(tree: ast.AST, module: str, package: bool):
    """Yield both the imported module/member and its local binding."""
    parent = module if package else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node, alias.name, alias.asname or alias.name.split(".")[0], True
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = resolve_name("." * node.level + base, parent)
            for alias in node.names:
                yield node, f"{base}.{alias.name}", alias.asname or alias.name, False


def qualified(node: ast.expr, bindings: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return bindings.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return qualified(node.value, bindings) + "." + node.attr
    return ""


def main() -> int:
    files = {}
    for path in sorted(APP.rglob("*.py")):
        parts = list(path.relative_to(APP.parent).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        module = ".".join(parts)
        tree = ast.parse(path.read_text(), filename=str(path))
        refs = list(imports(tree, module, path.name == "__init__.py"))
        files[path] = (module, tree, refs)

    # Models currently contain both Pydantic schemas and persistence code. Permit
    # only classes whose inheritance resolves to Pydantic/Enum (including subclasses).
    schemas = set(SCHEMA_BASES)
    classes = {}
    for module, tree, refs in files.values():
        if not within(module, "app.models"):
            continue
        bindings = {
            local: target if not direct or local != target.split(".")[0] else local
            for _, target, local, direct in refs
        }
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bindings[node.name] = f"{module}.{node.name}"
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes[f"{module}.{node.name}"] = [
                    qualified(base, bindings) for base in node.bases
                ]
    while True:
        discovered = {
            name
            for name, bases in classes.items()
            if bases and all(base in schemas for base in bases)
        }
        if discovered <= schemas:
            break
        schemas |= discovered

    errors = []
    for path, (module, tree, refs) in files.items():
        router = within(module, "app.routers")
        lower = any(
            within(module, f"app.{layer}")
            for layer in ("core", "models", "services", "utils")
        )
        for node, target, _, direct in refs:
            reason = None
            if lower and any(
                within(target, prefix) for prefix in ("app.routers", "app.main")
            ):
                reason = "lower layers must not depend on routers or app.main"
            if router and any(within(target, prefix) for prefix in DB_MODULES):
                reason = "routers must delegate database work to services"
            if (
                router
                and within(target, "app.models")
                and (direct or target not in schemas)
            ):
                reason = "routers may import model schemas/enums only, not ORM/repositories/modules"
            if reason:
                errors.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: {reason} ({target})"
                )
        # Dynamic imports hide dependencies from this static contract.
        if router or lower:
            bindings = {
                local: target if not direct or local != target.split(".")[0] else local
                for _, target, local, direct in refs
            }
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and qualified(node.func, bindings) in {
                    "__import__",
                    "builtins.__import__",
                    "importlib.import_module",
                }:
                    errors.append(
                        f"{path.relative_to(ROOT)}:{node.lineno}: use static imports in layered application code"
                    )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Backend architecture check passed ({len(files)} Python files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
