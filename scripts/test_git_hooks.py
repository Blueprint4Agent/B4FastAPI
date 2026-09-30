"""Real Git hooks must reject invalid messages and unverified outgoing snapshots."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent.parent
TITLE = "docs: update fixture guide"
BODY = "\n\nChanges:\n- Update guide.\n\nAffected Files:\n- README.md\n\nVerification:\n- Fixture.\n"


class GitHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "work"
        self.root.mkdir()
        self.command("git", "init", "-q", "-b", "main")
        self.command("git", "config", "user.email", "test@example.com")
        self.command("git", "config", "user.name", "Fixture")
        for name in ("git_hooks.py", "validate_git_governance.py"):
            target = self.root / "scripts" / name
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(SOURCE / "scripts" / name, target)
        shutil.copytree(SOURCE / ".githooks", self.root / ".githooks")
        (self.root / "Makefile").write_text("verify-plan:\n\t@echo Plan\nverify:\n\t@echo verified >> .git/fixture-verification\n")
        (self.root / "README.md").write_text("Initial\n")
        self.command("git", "add", ".")
        self.command("git", "commit", "-qm", "fixture seed")
        self.remote = Path(self.temp.name) / "remote.git"
        self.command("git", "init", "--bare", "-q", str(self.remote))
        self.command("git", "remote", "add", "origin", str(self.remote))
        self.command("git", "push", "-q", "origin", "main")
        self.command("git", "switch", "-qc", "docs/fixture-guide")
        self.command("python3", "scripts/git_hooks.py", "install")

    def command(self, *args, ok=True):
        result = subprocess.run(args, cwd=self.root, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def prepare(self, stage_log=True):
        (self.root / "README.md").write_text("Updated guide\n")
        log = self.root / "worklog/0001-fixture-guide.md"
        log.parent.mkdir(exist_ok=True)
        sections = ["Commit Title", "Changed File Scope", "Reason", "Design", "Verification Plan", "Impact", "Loop Alignment", "Verification"]
        log.write_text("\n".join(f"# {s}\n\n{TITLE if s == 'Commit Title' else 'Fixture evidence.'}\n" for s in sections))
        self.command("git", "add", "README.md")
        if stage_log:
            self.command("git", "add", "worklog")

    def commit(self):
        self.prepare()
        self.command("git", "commit", "-qm", TITLE + BODY)

    def test_commit_message_and_staged_worklog_are_required(self):
        self.prepare(stage_log=False)
        self.assertIn("worklog", self.command("git", "commit", "-qm", TITLE + BODY, ok=False))
        self.command("git", "add", "worklog")
        self.assertIn("invalid Conventional", self.command("git", "commit", "-qm", "invalid" + BODY, ok=False))
        self.command("git", "commit", "-qm", TITLE + BODY)

    def test_push_runs_local_plan_and_verification(self):
        self.commit()
        self.command("git", "push", "-q", "origin", "HEAD")
        self.assertEqual((self.root / ".git/fixture-verification").read_text(), "verified\n")

    def test_dirty_worktree_and_different_head_are_rejected(self):
        self.commit()
        (self.root / "README.md").write_text("Uncommitted\n")
        self.assertIn("Commit or stash", self.command("git", "push", "origin", "HEAD", ok=False))
        self.command("git", "restore", "README.md")
        self.command("git", "branch", "docs/old", "main")
        self.assertIn("checked-out HEAD", self.command("git", "push", "origin", "docs/old", ok=False))

    def test_failed_verification_blocks_push(self):
        self.prepare()
        (self.root / "Makefile").write_text("verify-plan:\n\t@echo Plan\nverify:\n\t@exit 1\n")
        self.command("git", "add", "Makefile")
        self.command("git", "commit", "-qm", TITLE + BODY)
        self.assertIn("Local Git check failed", self.command("git", "push", "origin", "HEAD", ok=False))
        self.assertEqual(self.command("git", "ls-remote", "--heads", "origin", "docs/fixture-guide"), "")

    def test_push_rechecks_authored_commits_even_if_commit_hook_was_bypassed(self):
        self.prepare()
        self.command("git", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "bad commit")
        self.assertIn("invalid Conventional", self.command("git", "push", "origin", "HEAD", ok=False))

    def test_main_and_invalid_branch_pushes_are_rejected(self):
        self.commit()
        self.assertIn("pull request", self.command("git", "push", "origin", "HEAD:main", ok=False))
        self.assertIn("destination branch", self.command("git", "push", "origin", "HEAD:wrong_name", ok=False))

    def test_install_refuses_to_replace_custom_hooks(self):
        self.command("git", "config", "core.hooksPath", "custom-hooks")
        self.assertIn("Existing core.hooksPath", self.command("python3", "scripts/git_hooks.py", "install", ok=False))
        self.assertEqual(self.command("git", "config", "--get", "core.hooksPath").strip(), "custom-hooks")

    def test_workflows_are_manual_only_and_rules_keep_pr_protection(self):
        for workflow in (SOURCE / ".github/workflows").glob("*.yml"):
            events = workflow.read_text().split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
            self.assertIn("    workflow_dispatch:", events)
            for event in ("pull_request:", "push:", "schedule:", "release:"):
                self.assertNotIn("\n    " + event, events)
        rules = json.loads((SOURCE / ".github/main-ruleset.json").read_text())["rules"]
        types = {rule["type"] for rule in rules}
        self.assertEqual(types, {"pull_request", "deletion", "non_fast_forward"})
        pr = next(rule for rule in rules if rule["type"] == "pull_request")
        self.assertTrue(pr["parameters"]["required_review_thread_resolution"])
