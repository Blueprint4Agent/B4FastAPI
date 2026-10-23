"""Impact selection fails broad when shared CSS, coverage or test boundaries are uncertain."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from verification_scope import (
    css_impact,
    changed_test_cases,
    frontend_impact,
    render_only,
    render_cases,
    DOMAINS,
)


class ScopeTests(unittest.TestCase):
    def test_css_domains_and_shared_fallback(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for path, classes in (
            ("src/pages/billing/BillingSettingsPage.tsx", "billing-records billing-a"),
            ("src/pages/admin/AdminPage.tsx", "admin-table"),
        ):
            owner = root / path
            owner.parent.mkdir(parents=True, exist_ok=True)
            owner.write_text(f'<section className="{classes}" />')
        for before, after, expected in [
            (
                ".billing-records {height:1px}",
                ".billing-records {height:2px}",
                {"billing"},
            ),
            ("", ".admin-table {height:2px}", {"admin"}),
            (".billing-a {height:1px}", "", {"billing"}),
            ("", ".billing-a, .shared {height:2px}", None),
            ("", ":root {--color:red}", None),
            (
                "@media (min-width:1px) {.billing-a {color:red}}",
                "@media (min-width:2px) {.billing-a {color:red}}",
                {"billing"},
            ),
            (
                "@keyframes spin {to {opacity:1}}",
                "@keyframes spin {to {opacity:0}}",
                None,
            ),
            ("", '.billing-a { content:"}"; }', None),
        ]:
            self.assertEqual(css_impact(before, after, root), expected, (before, after))

    def test_css_uses_actual_domain_consumers_and_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            owners = {
                "home": "src/pages/main/ProjectOverview.tsx",
                "profile": "src/pages/profile/ProfilePage.tsx",
                "inbox": "src/pages/inbox/InboxPage.tsx",
            }
            for domain, path in owners.items():
                owner = root / path
                owner.parent.mkdir(parents=True, exist_ok=True)
                # Deliberately no domain prefix: ownership comes from use, not naming.
                owner.write_text(f'<section className="local-{domain}" />')
                for test_path in DOMAINS[domain]["unit"] + DOMAINS[domain]["browser"]:
                    target = root / test_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()
            for domain in owners:
                before = f".local-{domain} {{padding:1px}}"
                after = f"@media (max-width:600px) {{.local-{domain} a:hover {{padding:2px}}}}"
                self.assertEqual(css_impact(before, after, root), {domain})
                selected = frontend_impact(
                    root,
                    "HEAD",
                    None,
                    ["src/styles/app.css"],
                    lambda _, ref, path: before if ref else after,
                )
                self.assertEqual(selected["domains"], [domain])
                self.assertEqual(
                    set(selected["browser"]), set(DOMAINS[domain]["browser"])
                )
            multi = ".local-home, .local-inbox {padding:2px}"
            self.assertEqual(css_impact("", multi, root), {"home", "inbox"})
            for unsafe in (
                ":root {--color:red}",
                "body {color:red}",
                ".ui-button {color:red}",
                ".local-home + main {color:red}",
                ".local-home ~ * {color:red}",
                ".local-home:has(+ main) {color:red}",
                ".local-home, .missing {color:red}",
                "@keyframes spin {to {opacity:0}}",
            ):
                self.assertIsNone(css_impact("", unsafe, root), unsafe)
            self.assertIsNone(
                css_impact(
                    ".local-home {color:red} .local-home {color:blue}",
                    ".local-home {color:blue} .local-home {color:red}",
                    root,
                )
            )
            # A shared or script/static producer cannot silently lose coverage.
            for path in ("src/components/ui/Panel.tsx", "scripts/discovery.mjs"):
                shared = root / path
                shared.parent.mkdir(parents=True, exist_ok=True)
                shared.write_text('const markup = "local-home";')
                self.assertIsNone(css_impact("", ".local-home {color:red}", root))
                shared.unlink()
            (root / DOMAINS["home"]["browser"][0]).unlink()
            self.assertIsNone(
                frontend_impact(
                    root,
                    "HEAD",
                    None,
                    ["src/styles/app.css"],
                    lambda _, ref, path: "" if ref else ".local-home {color:red}",
                )
            )

    def test_actual_case_lines_and_setup_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", temp], check=True)
            subprocess.run(
                ["git", "-C", temp, "config", "user.email", "fixture@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", temp, "config", "user.name", "Fixture"], check=True
            )
            path = "example.spec.ts"
            old = 'const shared = 1;\ntest("first", async () => {\n    expect(1);\n});\ntest("second", async () => {\n    expect(2);\n});\n'
            (root / path).write_text(old)
            subprocess.run(["git", "-C", temp, "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    temp,
                    "-c",
                    "core.hooksPath=/dev/null",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )

            def read(repo, ref, name):
                return (repo / name).read_text()

            (root / path).write_text(old.replace("expect(2)", "expect(3)"))
            self.assertEqual(
                changed_test_cases(root, "HEAD", None, path, read), {path + ":5"}
            )
            (root / path).write_text(old.replace("shared = 1", "shared = 2"))
            self.assertEqual(changed_test_cases(root, "HEAD", None, path, read), {path})
            (root / path).write_text(old.replace("    expect(2);\n", ""))
            self.assertEqual(changed_test_cases(root, "HEAD", None, path, read), {path})

    def test_domain_mapping_requires_existing_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            read = lambda *_: ""
            files = ["src/pages/billing/BillingSettingsPage.tsx"]
            self.assertIsNone(frontend_impact(root, "HEAD", None, files, read))
            for path in DOMAINS["billing"]["unit"] + DOMAINS["billing"]["browser"]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
            result = frontend_impact(root, "HEAD", None, files, read)
            self.assertEqual(result["domains"], ["billing"])
            self.assertEqual(result["browser"], ["tests/e2e/billing.spec.ts"])
            self.assertIsNone(
                frontend_impact(
                    root, "HEAD", None, files + ["src/components/ui/Button.tsx"], read
                )
            )

    def test_reviewed_pages_union_and_missing_or_shared_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            read = lambda *_: ""
            owners = {}
            for domain in ("home", "profile", "support", "inbox", "prompt-builder"):
                spec = DOMAINS[domain]
                owner = spec["prefixes"][0]
                if owner.endswith("/"):
                    owner += "Page.tsx"
                owners[domain] = owner
                for path in spec["unit"] + spec["browser"]:
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()
                selected = frontend_impact(root, "HEAD", None, [owner], read)
                self.assertEqual(selected["domains"], [domain])
                self.assertEqual(set(selected["browser"]), set(spec["browser"]))
            union = frontend_impact(root, "HEAD", None, list(owners.values()), read)
            self.assertEqual(len(union["browser"]), len(set(union["browser"])))
            self.assertEqual(set(union["domains"]), set(owners))
            for shared in (
                "src/components/ui/Button.tsx",
                "src/hooks/api/inbox/InboxProvider.tsx",
                "src/pages/unknown/Page.tsx",
            ):
                self.assertIsNone(
                    frontend_impact(root, "HEAD", None, [owners["inbox"], shared], read)
                )
            (root / DOMAINS["inbox"]["browser"][0]).unlink()
            self.assertIsNone(
                frontend_impact(root, "HEAD", None, [owners["inbox"]], read)
            )


class RenderImpactTests(unittest.TestCase):
    def test_only_render_region_can_select_render_cases(self):
        before = 'import { Button } from "../../ui";\nfunction Page() {\n    const data = useData();\n    return (\n        <Button />\n    );\n}\n'
        after = before.replace("<Button />", "<Button disabled />")
        self.assertTrue(render_only(before, after))
        self.assertTrue(
            render_only(before, after.replace("{ Button }", "{ Button, Spinner }"))
        )
        self.assertFalse(
            render_only(before, after.replace("useData()", "useOtherData()"))
        )
        self.assertFalse(render_only(before, after + "const sideEffect = run();\n"))
        self.assertFalse(render_only("not a component", "changed"))

    def test_missing_or_renamed_case_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertIsNone(
                render_cases(
                    root,
                    {"src/pages/admin/AdminPage.tsx"},
                    lambda *_: 'test("renamed", () => {});',
                    None,
                )
            )
            self.assertIsNone(
                render_cases(root, {"src/unknown.tsx"}, lambda *_: "", None)
            )
