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
