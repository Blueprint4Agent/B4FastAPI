"""Real changes prove ownership composition and conservative fallbacks."""

import json
from pathlib import Path
import tempfile
import unittest

import verification as v
from verification_areas import FRONTEND_AREAS, PARENT_AREAS


class AreaTests(unittest.TestCase):
    def fixture(self, parent=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for args in (
            ("init", "-q"),
            ("config", "user.email", "fixture@example.com"),
            ("config", "user.name", "Fixture"),
        ):
            v.git(root, *args)
        (root / "README.md").write_text("base\n")
        if parent:
            (root / "src/backend").mkdir(parents=True)
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "fixture")
        return root

    def change(self, root, path, text="changed\n"):
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    def test_explicit_owners_exclude_unrelated_runtime_tools(self):
        cases = [
            (True, "contracts/README.md", set()),
            (True, "AGENTS.md", {"governance"}),
            (True, "src/backend/TEST.md", {"governance"}),
            (True, "docker/docker-compose.yml", {"deployment"}),
            (True, "src/backend/app/services/auth.py", {"backend"}),
            (True, "scripts/indexnow.py", {"publication"}),
            (False, "src/hooks/useAuth.tsx", {"frontend-app"}),
            (False, "scripts/verification.py", {"harness"}),
            (False, "scripts/style-studio.mjs", {"frontend-app", "style-studio"}),
            (False, "scripts/public-discovery.mjs", {"discovery"}),
            (
                False,
                "src/styles/app.css",
                {"frontend-app", "style-studio", "discovery"},
            ),
        ]
        for parent, path, expected in cases:
            with self.subTest(path=path):
                root = self.fixture(parent)
                self.change(root, path)
                scope = v.plan(root)
                self.assertEqual(set(scope["areas"]), expected)
                self.assertEqual(set(scope["ownership"][path]), expected)
                commands = v.targets(scope, parent, "all")
                if path.endswith("auth.py"):
                    self.assertIn("backend-test", str(commands))
                    self.assertNotIn("test-ui", str(commands))
                if path.endswith("useAuth.tsx"):
                    self.assertIn(["make", "test-production"], commands)
                    self.assertNotIn(["make", "test-style-studio"], commands)
                    self.assertNotIn(["make", "test-discovery"], commands)
                    self.assertNotIn(["make", "project-config-check"], commands)
                if expected <= {"harness", "governance"}:
                    self.assertFalse(scope["node"])
                    self.assertFalse(scope["browser"])
                    self.assertFalse(any("build" in command for command in commands))

    def test_locale_key_addition_broadens_app_without_tool_browsers(self):
        root = self.fixture()
        self.change(root, "src/locales/ko.json", json.dumps({"old": "value"}))
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "locale")
        self.change(
            root, "src/locales/ko.json", json.dumps({"old": "value", "new": "추가"})
        )
        scope = v.plan(root)
        self.assertEqual(scope["frontend"], "full")
        self.assertEqual(scope["areas"], ["frontend-app"])
        commands = v.targets(scope, False, "all")
        self.assertIn(["make", "test-ui"], commands)
        self.assertNotIn(["make", "test-style-studio"], commands)
        self.assertNotIn(["make", "test-discovery"], commands)

    def test_copy_keeps_dependency_free_path(self):
        root = self.fixture()
        self.change(root, "src/locales/ko.json", '{"old":"value"}')
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "locale")
        self.change(root, "src/locales/ko.json", '{"old":"변경"}')
        scope = v.plan(root)
        self.assertEqual(scope["frontend"], "copy")
        self.assertEqual(v.targets(scope, False, "all"), [])
        self.assertFalse(scope["node"])

    def test_direct_tool_dependencies_are_not_missed(self):
        for path, expected in [
            ("src/api/styleStudio/styleStudioApi.ts", "style-studio"),
            ("src/hooks/api/styleStudio/useStyleStudioApi.ts", "style-studio"),
            ("src/locales/styleStudio.en.json", "style-studio"),
            ("public/home-previews/components-en.webp", "discovery"),
        ]:
            root = self.fixture()
            self.change(root, path, "{}")
            self.assertIn(expected, v.plan(root)["areas"], path)
        root = self.fixture()
        self.change(root, "src/locales/en.json", '{"discovery":{"heading":"hello"}}')
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "discovery")
        self.change(root, "src/locales/en.json", '{"discovery":{}}')
        self.assertIn("discovery", v.plan(root)["areas"])
        self.change(root, "src/styles/app.css", ".billing-row {height:1px}")
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "css")
        self.change(root, "src/styles/app.css", ".billing-row {height:2px}")
        self.assertEqual(v.plan(root)["areas"], ["frontend-app"])

    def test_unknown_force_full_and_missing_history_keep_all_areas(self):
        for parent in (False, True):
            root = self.fixture(parent)
            self.change(root, "unregistered-config")
            if parent:
                self.change(root, "docker/Dockerfile", "FROM example:latest\n")
            for scope in (
                v.plan(root),
                v.plan(root, force_full=True),
                v.plan(root, "missing-ref"),
            ):
                self.assertEqual(
                    set(scope["areas"]), PARENT_AREAS if parent else FRONTEND_AREAS
                )
                commands = v.targets(scope, parent, "all")
                prefix = ["make", "-C", "src/frontend"] if parent else ["make"]
                for target in (
                    "verification-harness-test",
                    "app-tooling-test",
                    "test",
                    "test-ui",
                    "test-production",
                    "test-style-studio",
                    "project-config-check",
                ):
                    self.assertIn(prefix + [target], commands)
                self.assertIn(prefix + ["discovery-check", "test-discovery"], commands)
                if parent:
                    self.assertIn("backend-test", str(commands))
                    self.assertIn("frontend-package-verified", str(commands))

    def test_mixed_backend_and_discovery_compose_both_without_app(self):
        root = self.fixture(True)
        self.change(root, "src/backend/app/services/new.py")
        self.change(root, "scripts/indexnow.py")
        scope = v.plan(root)
        self.assertEqual(set(scope["areas"]), {"backend", "publication"})
        self.assertTrue(scope["backend"])
        self.assertEqual(scope["frontend"], "none")
        commands = v.targets(scope, True, "all")
        self.assertIn(["make", "discovery-check"], commands)
        self.assertIn("backend-test", str(commands))
        self.assertNotIn("test-style-studio", str(commands))

    def test_child_areas_survive_parent_gitlink_and_dirty_changes(self):
        root = self.fixture(True)
        child = root / "src/frontend"
        child.mkdir()
        v.git(child, "init", "-q")
        v.git(child, "config", "user.email", "fixture@example.com")
        v.git(child, "config", "user.name", "Fixture")
        self.change(child, "README.md")
        v.git(child, "add", ".")
        v.git(child, "commit", "-qm", "child")
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "parent")
        self.change(child, "scripts/style-studio.mjs")
        scope = v.plan(root)
        self.assertEqual(set(scope["areas"]), {"frontend-app", "style-studio"})
        self.assertFalse(scope["backend"])
        self.assertNotIn("test-discovery", str(v.targets(scope, True, "all")))
        v.git(child, "add", ".")
        v.git(child, "commit", "-qm", "editor")
        self.assertEqual(v.plan(root)["areas"], scope["areas"])


if __name__ == "__main__":
    unittest.main()
