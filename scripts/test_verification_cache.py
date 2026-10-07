"""Receipts reuse identical work only; changes, failures and missing outputs invalidate it."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import verification_cache as cache


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "app.ts").write_text("code\n")
        (self.root / "worklog").mkdir()
        (self.root / "worklog/0001-check.md").write_text("Plan\n")
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.ctx = patch.object(cache, "context", return_value={"tool": "fixture"})
        self.ctx.start()
        self.addCleanup(self.ctx.stop)

    def receipt(self, command=None):
        return cache.Receipt(self.root, command or ["make", "check", "test"])

    def test_source_new_file_and_config_changes_invalidate(self):
        self.receipt().save()
        self.assertTrue(self.receipt().reusable())
        for file in ("app.ts", "new.ts", ".env", "project.local.json", "README.md"):
            self.receipt().save()
            (self.root / file).write_text("different\n")
            self.assertFalse(self.receipt().reusable(), file)

    def test_worklog_outcomes_do_not_repeat_runtime_checks(self):
        self.receipt().save()
        (self.root / "worklog/0001-check.md").write_text("Actual test outcomes\n")
        self.assertTrue(self.receipt().reusable())

    def test_command_tool_context_force_and_ci_are_not_reused(self):
        self.receipt().save()
        self.assertFalse(self.receipt(["make", "test-ui"]).reusable())
        with patch.object(cache, "context", return_value={"tool": "new"}):
            self.assertFalse(self.receipt().reusable())
        for key in ("VERIFY_FULL", "CI"):
            with patch.dict(os.environ, {key: "1"}):
                self.assertFalse(self.receipt().reusable())

    def test_expiry_failed_rerun_and_source_mutation_invalidate(self):
        self.receipt().save()
        with patch.object(cache.time, "time", return_value=cache.time.time() + cache.TTL_SECONDS + 1):
            self.assertFalse(self.receipt().reusable())
        self.receipt().invalidate()
        self.assertFalse(self.receipt().reusable())
        receipt = self.receipt()
        (self.root / "app.ts").write_text("changed during check\n")
        receipt.save()
        self.assertFalse(self.receipt().reusable())

    def test_missing_or_modified_build_outputs_invalidate(self):
        (self.root / "dist").mkdir()
        (self.root / ".gitignore").write_text("dist/\n")
        output = self.root / "dist/index.html"
        output.write_text("built")
        command = ["make", "test-routes"]
        self.receipt(command).save()
        self.assertTrue(self.receipt(command).reusable())
        output.write_text("modified")
        self.assertFalse(self.receipt(command).reusable())
        self.receipt(command).save()
        output.unlink()
        self.assertFalse(self.receipt(command).reusable())

    def test_delegated_parent_command_uses_child_receipt(self):
        child = self.root / "src/frontend"
        child.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(child)], check=True)
        (child / "app.ts").write_text("child\n")
        cache.Receipt(child, ["make", "check", "test"]).save()
        receipt = cache.Receipt(self.root, ["make", "-C", "src/frontend", "check", "test"])
        self.assertTrue(receipt.reusable())
        (child / "app.ts").write_text("modified child\n")
        self.assertFalse(cache.Receipt(self.root, ["make", "-C", "src/frontend", "check", "test"]).reusable())

class EnvironmentTests(unittest.TestCase):
    def test_hook_helper_and_duplicate_path_entries_are_equivalent(self):
        with patch.object(cache.subprocess, "check_output", return_value="/git/helpers\n"):
            normal = cache.normalized_path("/tools:/usr/bin:/tools")
            hook = cache.normalized_path("/git/helpers:/tools:/usr/bin")
            self.assertEqual(normal, hook)
            self.assertNotEqual(normal, cache.normalized_path("/other:/tools:/usr/bin"))
            self.assertNotEqual(normal, cache.normalized_path("/usr/bin:/tools"))

    def test_real_tool_and_environment_changes_remain_distinct(self):
        with patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}, clear=True):
            first = cache.context()
            with patch.dict(os.environ, {"VITE_API_BASE_URL": "https://different.example"}):
                self.assertNotEqual(first, cache.context())
            with patch.object(cache.shutil, "which", return_value="/different/tool"):
                self.assertNotEqual(first, cache.context())


class ScopedCommandTests(unittest.TestCase):
    setUp = ReceiptTests.setUp
    receipt = ReceiptTests.receipt

    def test_one_selection_does_not_authorize_another(self):
        first = ["make", "test-selected", "TEST_FILES=src/tests/billing.test.ts"]
        second = ["make", "test-selected", "TEST_FILES=src/tests/admin.test.ts"]
        self.receipt(first).save()
        self.assertTrue(self.receipt(first).reusable())
        self.assertFalse(self.receipt(second).reusable())
        self.assertFalse(self.receipt(["make", "test"]).reusable())

    def test_hook_path_reuses_real_context(self):
        self.ctx.stop()
        with patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}, clear=True):
            helper = cache.subprocess.check_output(["git", "--exec-path"], text=True).strip()
            self.receipt().save()
            with patch.dict(os.environ, {"PATH": helper + ":/usr/bin:/bin:/usr/bin", "GIT_EXEC_PATH": helper}):
                self.assertTrue(self.receipt().reusable())
