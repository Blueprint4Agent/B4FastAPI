"""Explicit impact mapping for local frontend suites; unknown impact stays broad."""
import re
import subprocess

DOMAINS = {
    "billing": {
        "prefixes": ("src/pages/billing/", "src/components/features/billing/", "src/hooks/api/billing/"),
        "unit": ("src/tests/component/components/features/billing", "src/tests/integration/hooks/billing", "src/tests/integration/api/billingApi.test.ts"),
        "browser": ("tests/e2e/billing.spec.ts",),
    },
    "admin": {
        "prefixes": ("src/pages/admin/", "src/components/features/admin/", "src/hooks/api/admin/"),
        "unit": ("src/tests/component/pages/admin", "src/tests/integration/hooks/useAdminUsers.test.tsx", "src/tests/integration/api/adminUsersApi.test.ts", "src/tests/integration/api/adminStatus.test.tsx"),
        "browser": ("tests/e2e/admin-panel.spec.ts", "tests/e2e/admin-server.spec.ts"),
    },
}


# Reviewed render-only ownership. Hook/service changes retain complete domain coverage.
RENDER_CASES = {
    "src/pages/billing/BillingSettingsPage.tsx": ("tests/e2e/billing.spec.ts", (
        "billing and three example plans fit", "registration opens only", "disabled billing never",
        "Korean pricing and settings", "cancellation uses one transient", "billing loading uses",
        "paid subscription changes", "Link-only billing", "billing isolates concurrent",
        "manual billing profile", "embedded card return", "invoice history stays",
    )),
    "src/components/features/billing/InvoiceHistoryDialog.tsx": ("tests/e2e/billing.spec.ts", ("invoice history stays",)),
    "src/pages/admin/AdminPage.tsx": ("tests/e2e/admin-panel.spec.ts", (
        "admin profile opens", "non-admin users", "directory failures",
    )),
    "src/components/features/admin/AdminUserTable.tsx": ("tests/e2e/admin-panel.spec.ts", (
        "admin profile opens", "non-admin users", "directory failures",
    )),
    "src/pages/admin/AdminServerPage.tsx": ("tests/e2e/admin-server.spec.ts", (
        "server status matches", "cannot fetch server status", "initial status loading",
    )),
}


def render_only(before, after):
    def prefix(text):
        # Only permit JSX-region edits; hook setup/helper changes retain domain-wide tests.
        index = text.rfind("\n    return (")
        if index < 0:
            return None
        value = text[:index]
        end = text.rfind("\n    );")
        if end <= index:
            return None
        return (re.sub(r'import\s+(?:[^;]+)from\s+["\'][^"\']*/(?:components/)?ui["\'];', '', value), text[end:])
    old, new = prefix(before), prefix(after)
    return old is not None and old == new


def render_cases(root, owners, read, head):
    result = set()
    for owner in owners:
        if owner not in RENDER_CASES:
            return None
        spec, markers = RENDER_CASES[owner]
        lines = read(root, head, spec).splitlines()
        for marker in markers:
            matches = [i + 1 for i, line in enumerate(lines)
                       if re.match(r'\s*test\(["\'`]', line) and marker in line]
            if len(matches) != 1:
                return None  # Renamed/missing coverage is never silently ignored.
            result.add(f"{spec}:{matches[0]}")
    return result


def css_owners(root, before, after):
    owners = set()
    for _, selector, _ in css_rules(before) ^ css_rules(after):
        for part in selector.split(","):
            match = re.search(r"\.((?:billing|admin)-[\w-]+)", part)
            if not match:
                return None
            name = match[1]
            hits = {str(path.relative_to(root)) for path in (root / "src").rglob("*.tsx")
                    if re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", path.read_text())}
            if not hits or any(hit not in RENDER_CASES for hit in hits):
                return None
            owners.update(hits)
    return owners


def css_rules(text):
    """Parse a deliberately narrow CSS subset. Unsupported syntax falls back to all UI."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    # Braces in quoted strings need a complete CSS parser; never guess their impact.
    if re.search(r'''["'][^"'\n]*[{}][^"'\n]*["']''', text):
        raise ValueError("complex CSS string")
    records = set()

    def parse(start, end, parents=()):
        cursor = start
        while cursor < end:
            opening = text.find("{", cursor, end)
            if opening < 0:
                if text[cursor:end].strip():
                    raise ValueError("unsupported CSS statement")
                return
            header = text[cursor:opening].strip()
            depth, closing = 1, opening + 1
            while closing < end and depth:
                depth += (text[closing] == "{") - (text[closing] == "}")
                closing += 1
            if depth:
                raise ValueError("unbalanced CSS")
            body = text[opening + 1:closing - 1]
            if "{" in body:
                parse(opening + 1, closing - 1, (*parents, header))
            else:
                records.add((parents, header, body.strip()))
            cursor = closing
    parse(0, len(text))
    return records


def css_impact(before, after):
    try:
        modified = css_rules(before) ^ css_rules(after)
    except ValueError:
        return None
    domains = set()
    for parents, selector, _ in modified:
        if any(not item.startswith(("@media ", "@supports ", "@layer ", "@container ")) for item in parents):
            return None
        for part in selector.split(","):
            part = part.strip()
            if re.match(r"\.billing-[\w-]+(?:\b|:)", part) or part.startswith('[aria-labelledby="billing-'):
                domains.add("billing")
            elif re.match(r"\.admin-[\w-]+(?:\b|:)", part):
                domains.add("admin")
            else:
                return None
    return domains


def changed_test_cases(root, base, head, path, read):
    """Select whole generated test groups when edits are wholly inside existing test bodies."""
    args = ["git", "-C", str(root), "diff", "--unified=0", "--no-renames", base]
    if head:
        args.append(head)
    diff = subprocess.check_output([*args, "--", path], text=True)
    text = read(root, head, path)
    lines = text.splitlines()
    ranges = []
    for index, line in enumerate(lines):
        match = re.match(r'^(\s*)test\(["\'`]', line)
        if not match:
            continue
        ending = match[1] + "});"
        close = next((i for i in range(index + 1, len(lines)) if lines[i] == ending), None)
        if close is not None:
            ranges.append((index + 1, close + 1))
    selected = set()
    hunks = re.findall(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M)
    if not hunks:
        return {path}
    for start, length in hunks:
        start, length = int(start), int(length or 1)
        # Deletion-only edits can remove/reorder test groups; retain the complete suite.
        owner = next((a for a, b in ranges if length and a < start and start + length - 1 < b), None)
        if owner is None:
            return {path}
        selected.add(f"{path}:{owner}")
    return selected


def frontend_impact(root, base, head, paths, read):
    domains, units, browsers = set(), set(), set()
    owners, render_safe = set(), True
    for path in paths:
        if path.endswith(".md"):
            continue
        if path.startswith("tests/e2e/") and path.endswith(".spec.ts"):
            try:
                browsers.update(changed_test_cases(root, base, head, path, read))
            except (OSError, ValueError, subprocess.CalledProcessError):
                return None
            continue
        if path.startswith("src/tests/") and re.search(r"\.test\.tsx?$", path):
            units.add(path)
            continue
        if path == "src/styles/app.css":
            try:
                affected = css_impact(read(root, base, path), read(root, head, path))
            except (OSError, ValueError, subprocess.CalledProcessError):
                return None
            if affected is None:
                return None
            domains.update(affected)
            mapped = css_owners(root, read(root, base, path), read(root, head, path))
            if mapped is None:
                render_safe = False
            else:
                owners.update(mapped)
            continue
        domain = next((name for name, spec in DOMAINS.items() if path.startswith(spec["prefixes"])), None)
        if domain is None:
            return None
        domains.add(domain)
        try:
            if path in RENDER_CASES and render_only(read(root, base, path), read(root, head, path)):
                owners.add(path)
            else:
                render_safe = False
        except (OSError, ValueError, subprocess.CalledProcessError):
            render_safe = False
    try:
        cases = render_cases(root, owners, read, head) if render_safe and owners else None
    except (OSError, ValueError, subprocess.CalledProcessError):
        cases = None
    for domain in domains:
        units.update(DOMAINS[domain]["unit"])
        if cases is None:
            browsers.update(DOMAINS[domain]["browser"])
    if cases is not None:
        browsers.update(cases)
    units = {item for item in units if not any(item.startswith(other + "/") for other in units if other != item)}
    # A full suite selection supersedes case filters for that suite.
    browsers = {item for item in browsers if ":" not in item or item.split(":")[0] not in browsers}
    if not units and not browsers:
        return None
    # Never silently accept deleted/missing mapped coverage or a path that can become shell syntax.
    for path in units | {item.split(":")[0] for item in browsers}:
        if not re.fullmatch(r"[\w./-]+", path) or not (root / path).exists():
            return None
    checks = [path for path in paths if re.fullmatch(r"[\w./-]+", path)
              and path.endswith((".ts", ".tsx", ".css", ".json")) and (root / path).is_file()]
    return {"domains": sorted(domains), "unit": sorted(units), "browser": sorted(browsers),
            "checks": sorted(checks), "render_only": cases is not None}
