"""Real Git fixtures protect the cheap path from widening into runtime changes."""

import json
from pathlib import Path
import tempfile
import unittest

import verification as v


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.init(self.root)
        self.write("README.md", "Guide\n")
        self.write("src/locales/ko.json", json.dumps({"hello": "Hello {{name}}"}))
        self.commit(self.root)

    def init(self, root):
        root.mkdir(parents=True, exist_ok=True)
        for args in [
            ("init", "-q"),
            ("config", "user.email", "test@example.com"),
            ("config", "user.name", "Test"),
        ]:
            v.git(root, *args)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, root):
        v.git(root, "add", ".")
        v.git(root, "commit", "-qm", "fixture")

    def test_clean_and_document_changes_need_no_runtime(self):
        self.assertEqual(v.plan(self.root)["frontend"], "none")
        self.write("notes/new.md", "A new guide.\n")
        scope = v.plan(self.root)
        self.assertEqual(scope["frontend"], "docs")
        self.assertEqual(v.targets(scope, False, "all"), [])
        v.lightweight(self.root, "HEAD", None)

    def test_copy_preserves_keys_and_placeholders(self):
        self.write("src/locales/ko.json", json.dumps({"hello": "안녕하세요 {{name}}"}))
        self.assertEqual(v.plan(self.root)["frontend"], "copy")
        for payload in [
            {"renamed": "Hello {{name}}"},
            {"hello": "No placeholder"},
            {"hello": 42},
            {"hello": "<b>Hello {{name}}</b>"},
        ]:
            self.write("src/locales/ko.json", json.dumps(payload))
            self.assertEqual(v.plan(self.root)["frontend"], "full")

    def test_invalid_duplicate_or_deleted_locale_is_not_copy(self):
        for text in ["{", '{"hello":"a","hello":"b"}']:
            self.write("src/locales/ko.json", text)
            self.assertEqual(v.plan(self.root)["frontend"], "full")
            with self.assertRaises(ValueError):
                v.lightweight(self.root, "HEAD", None)
        (self.root / "src/locales/ko.json").unlink()
        self.assertEqual(v.plan(self.root)["frontend"], "full")

    def test_runtime_ui_and_protected_changes(self):
        for path, expected in [
            ("src/utils/color.ts", "behavior"),
            ("src/styles/app.css", "ui"),
            ("src/pages/settings/SettingsPage.tsx", "ui"),
            ("src/hooks/useAuth.tsx", "full"),
            ("AGENTS.md", "full"),
            ("scripts/verification.py", "full"),
            ("package-lock.json", "full"),
            ("unknown", "full"),
        ]:
            self.write(path, "changed\n")
            self.assertEqual(v.plan(self.root)["frontend"], expected, path)
            (self.root / path).unlink()

    def test_mixed_change_uses_strongest_and_full_override(self):
        self.write("README.md", "Updated\n")
        self.write("src/styles/app.css", "body {}\n")
        scope = v.plan(self.root)
        self.assertEqual(scope["frontend"], "ui")
        self.assertIn(["make", "test-ui"], v.targets(scope, False, "all"))
        self.assertEqual(v.plan(self.root, force_full=True)["frontend"], "full")

    def test_commit_range_and_staged_changes(self):
        self.write("README.md", "staged\n")
        v.git(self.root, "add", ".")
        self.assertEqual(v.plan(self.root)["frontend"], "docs")
        old = v.git(self.root, "rev-parse", "HEAD").decode().strip()
        self.commit(self.root)
        self.assertEqual(v.plan(self.root, old, "HEAD")["frontend"], "docs")
        self.assertEqual(v.plan(self.root)["frontend"], "none")

    def test_full_parent_reuses_verified_build_for_packaging(self):
        scope = {"backend": True, "frontend": "full"}
        commands = v.targets(scope, True, "frontend")
        self.assertIn(["make", "project-brand"], commands)
        self.assertIn(["make", "-C", "src/frontend", "test-routes"], commands)
        self.assertIn(
            ["make", "frontend-contract-check", "frontend-package-verified"], commands
        )
        self.assertFalse(any("frontend-package" in command for command in commands))

    def test_missing_base_falls_back_to_full(self):
        self.assertEqual(v.plan(self.root, "missing-ref")["frontend"], "full")

    def test_backend_only_does_not_run_frontend(self):
        self.write("src/backend/app/services/example.py", "pass\n")
        scope = v.plan(self.root)
        self.assertTrue(scope["backend"])
        self.assertFalse(scope["node"])
        self.assertEqual(v.targets(scope, True, "frontend"), [])
        self.assertIn("backend-test", v.targets(scope, True, "backend")[0])

    def test_pinned_child_copy_is_classified_from_actual_commits(self):
        (self.root / "src/backend").mkdir()
        child = self.root / "src/frontend"
        self.init(child)
        (child / "src/locales").mkdir(parents=True)
        locale = child / "src/locales/ko.json"
        locale.write_text('{"message":"before"}')
        self.commit(child)
        self.commit(self.root)
        locale.write_text('{"message":"after"}')
        self.commit(child)
        scope = v.plan(self.root)
        self.assertEqual(scope["frontend"], "copy")
        self.assertFalse(scope["backend"])
        self.assertFalse(scope["node"])
        (child / "package.json").write_text("{}")
        self.assertEqual(v.plan(self.root)["frontend"], "full")

    def test_dirty_child_without_pin_update_is_included(self):
        (self.root / "src/backend").mkdir()
        child = self.root / "src/frontend"
        self.init(child)
        (child / "README.md").write_text("Guide\n")
        self.commit(child)
        self.commit(self.root)
        (child / "new-runtime.ts").write_text("export const value = 1;\n")
        self.assertEqual(v.plan(self.root)["frontend"], "full")

    def test_manual_ci_retains_verification_jobs(self):
        # Manual workflows retain full verification without automatic events.
        repo = Path(v.__file__).resolve().parent.parent
        workflow = repo / ".github/workflows/build.yml"
        names = ["Frontend checks", "Backend checks"]
        if not workflow.exists():
            workflow = repo / ".github/workflows/check.yml"
            names = ["Frontend checks"]
        text = workflow.read_text()
        for name in names:
            self.assertIn(f"name: {name}", text)
        self.assertNotIn("paths:", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("    workflow_dispatch:", text)
        self.assertNotIn("\n    pull_request:", text)
        self.assertNotIn("\n    push:", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("VERIFY_BASE:", text)
        self.assertIn(
            "name: Git governance",
            (repo / ".github/workflows/governance.yml").read_text(),
        )

    def test_lightweight_rejects_bad_untracked_text_and_symlinks(self):
        self.write("notes/new.md", "trailing space \n")
        with self.assertRaises(ValueError):
            v.lightweight(self.root, "HEAD", None)
        (self.root / "notes/new.md").unlink()
        (self.root / "notes/new.md").symlink_to(self.root / "README.md")
        with self.assertRaises(ValueError):
            v.lightweight(self.root, "HEAD", None)


if __name__ == "__main__":
    unittest.main()
