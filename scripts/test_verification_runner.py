"""Exercise real child processes, dependency ordering and failure draining."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import verification_runner as runner


class RunnerTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        script = """from pathlib import Path
import sys, time
root = Path('.')
mode = sys.argv[1]
def wait_for(name):
    deadline = time.monotonic() + 8
    while not (root/name).exists():
        if time.monotonic() > deadline:
            raise RuntimeError('parallel peer did not start: ' + name)
        time.sleep(.01)
if mode in ('backend', 'frontend'):
    (root/(mode + '-started')).touch()
    wait_for(('frontend' if mode == 'backend' else 'backend') + '-started')
    (root/(mode + '-done')).touch()
elif mode == 'package':
    assert (root/'backend-done').exists()
    assert (root/'frontend-done').exists()
    (root/'packaged').touch()
elif mode == 'failure':
    (root/'backend-started').touch()
    wait_for('frontend-started')
    sys.exit(9)
elif mode == 'drain':
    (root/'frontend-started').touch()
    wait_for('backend-started')
    time.sleep(.2)
    (root/'drained').touch()
elif mode == 'forbidden':
    (root/'forbidden').touch()
"""
        (root / "step.py").write_text(script)
        return root

    def makefile(self, root, targets):
        (root / "Makefile").write_text(
            "".join(
                f"{target}:\n\t'{sys.executable}' step.py {mode}\n"
                for target, mode in targets.items()
            )
        )

    def test_independent_lanes_overlap_and_packaging_waits(self):
        root = self.fixture()
        self.makefile(
            root,
            {
                "backend-test": "backend",
                "frontend": "frontend",
                "frontend-package-verified": "package",
            },
        )
        commands = [
            ["make", "backend-test"],
            ["make", "frontend"],
            ["make", "frontend-package-verified"],
        ]
        with patch.object(runner, "Receipt") as receipt:
            receipt.return_value.miss_reason.return_value = "fixture"
            receipt.return_value.reusable.return_value = False
            runner.execute(root, commands, jobs=2)
        self.assertTrue((root / "packaged").exists())
        self.assertEqual(
            len(list((root / ".git/verification-logs").glob("run-*/*.log"))), 3
        )

    def test_failure_stops_pending_work_and_drains_running_process(self):
        root = self.fixture()
        self.makefile(
            root, {"backend-test": "failure", "frontend": "drain", "after": "forbidden"}
        )
        with patch.object(runner, "Receipt") as receipt:
            receipt.return_value.miss_reason.return_value = "fixture"
            receipt.return_value.reusable.return_value = False
            with self.assertRaises(subprocess.CalledProcessError):
                runner.execute(
                    root,
                    [["make", "backend-test"], ["make", "frontend"], ["make", "after"]],
                    jobs=2,
                )
        self.assertTrue((root / "drained").exists())
        self.assertFalse((root / "forbidden").exists())
        receipt.return_value.save.assert_called_once()

    def test_serial_mode_and_forced_mode_do_not_reuse_or_save(self):
        root = self.fixture()
        self.makefile(root, {"first": "forbidden", "second": "forbidden"})
        with patch.object(runner, "Receipt") as receipt:
            runner.execute(
                root, [["make", "first"], ["make", "second"]], jobs=1, forced=True
            )
            receipt.return_value.reusable.assert_not_called()
            receipt.return_value.save.assert_not_called()
        self.assertTrue((root / "forbidden").exists())

    def test_discovery_commands_never_overlap_other_browser_targets(self):
        commands = [
            ["make", "test-ui"],
            ["make", "discovery-check", "test-discovery"],
            ["make", "test-style-studio"],
        ]
        self.assertEqual(runner.dependencies(commands), [set(), {0}, {1}])

    def test_build_browsers_and_custom_branding_share_ordered_lane(self):
        commands = [
            ["make", "backend-test"],
            ["make", "project-brand"],
            ["make", "-C", "src/frontend", "test-ui"],
            ["make", "-C", "src/frontend", "test-production"],
            ["make", "project-build-test"],
            ["make", "frontend-package-verified"],
        ]
        self.assertEqual(
            runner.dependencies(commands), [set(), set(), {1}, {2}, {3}, set(range(5))]
        )


if __name__ == "__main__":
    unittest.main()
