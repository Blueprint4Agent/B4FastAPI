"""Initializer tests use isolated copies, never the developer's actual environment."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import project_init as setup
from project_identity import brand_plan, validate_manifest

SOURCE = Path(__file__).resolve().parents[1]


class ProjectInitializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="b4-project-init-")
        self.root = Path(self.temp.name)
        for directory in ("src/backend", "src/frontend", "docker"):
            target = self.root / directory
            target.mkdir(parents=True)
            shutil.copyfile(
                SOURCE / directory / ".env.example", target / ".env.example"
            )
        marker = self.root / "src/frontend/scripts/project-config.mjs"
        marker.parent.mkdir()
        marker.write_text("// supported consumer fixture")
        self.config = self.root / "project.json"
        self.data = json.loads((SOURCE / "project.example.json").read_text())
        self.data.update(name="테스트 & Co", short_name="테스트")
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.config.write_text(json.dumps(self.data, ensure_ascii=False))

    def run_command(self, command):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = setup.run(command, self.root, self.config)
        return status, stream.getvalue()

    def test_fresh_setup_plan_apply_and_idempotence(self):
        self.assertEqual(self.run_command("plan")[0], 0)
        self.assertFalse((self.root / "src/backend/.env").exists())
        self.assertEqual(self.run_command("check")[0], 1)
        status, output = self.run_command("apply")
        self.assertEqual(status, 0)
        backend = self.root / "src/backend/.env"
        self.assertIn("APP_NAME='테스트 & Co API'", backend.read_text())
        self.assertIn(
            "COMPOSE_PROJECT_NAME='my-service'", (self.root / "docker/.env").read_text()
        )
        _, entries = setup.env_files.read(backend)
        secret = setup.env_value(entries, "SECRET_KEY")
        self.assertGreater(len(secret), 40)
        self.assertNotIn(secret, output)
        self.assertEqual(backend.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.run_command("check")[0], 0)
        stamp = backend.stat().st_mtime_ns
        self.assertEqual(self.run_command("apply")[0], 0)
        self.assertEqual(backend.stat().st_mtime_ns, stamp)
        self.assertFalse((self.root / ".project-backups").exists())

    def test_preserves_credentials_connections_and_unmanaged_values_with_backups(self):
        target = self.root / "src/backend/.env"
        previous = "SECRET_KEY='keep-this-secret'\nDB_NAME=production.db\nSMTP_PASSWORD='literal$token'\nCUSTOM_VALUE='retain me'\nLOGIN_ENABLED=false\n"
        target.write_text(previous)
        target.chmod(0o600)
        _, output = self.run_command("apply")
        content = target.read_text()
        for line in previous.splitlines()[:-1]:
            self.assertIn(line, content)
        self.assertIn("LOGIN_ENABLED='true'", content)
        self.assertNotIn("keep-this-secret", output)
        backups = list((self.root / ".project-backups").glob("*/src/backend/.env"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), previous)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_logo_copy_and_public_identity_excludes_features_and_secrets(self):
        asset = self.root / "branding/logo.svg"
        asset.parent.mkdir()
        asset.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.data["logo"] = "branding/logo.svg"
        self.save()
        self.run_command("apply")
        child = self.root / "src/frontend"
        identity = json.loads((child / "project.local.json").read_text())
        self.assertEqual(identity["logo_url"], "/project-brand/logo.svg")
        self.assertNotIn("features", identity)
        self.assertNotIn("SECRET_KEY", identity)
        self.assertEqual(
            (child / "public/project-brand/logo.svg").read_bytes(), asset.read_bytes()
        )
        # The standard-library build generator has the same public output.
        self.assertEqual(
            brand_plan(self.data, self.root, child)[child / "project.local.json"],
            (child / "project.local.json").read_bytes(),
        )

    def test_invalid_inputs_block_all_writes(self):
        variants = [
            {"slug": "../bad"},
            {"identifier": "not-an-id"},
            {"version": True},
            {"name": "${SECRET}"},
            {"features": {"login": "false", "email": False, "oauth": False}},
            {"features": {"login": False, "email": True, "oauth": False}},
            {"secret": "do-not-display"},
            {"logo": "../logo.svg"},
            {"logo": "branding/missing.png"},
        ]
        original = dict(self.data)
        for value in variants:
            with self.subTest(value=value):
                self.data = {**original, **value}
                self.save()
                with self.assertRaises(ValueError):
                    setup.plan(self.root, self.config)
                self.assertFalse(
                    (self.root / "src/frontend/project.local.json").exists()
                )

    def test_malformed_existing_environment_blocks_branding_writes(self):
        (self.root / "docker/.env").write_text("APP_NAME=one\nAPP_NAME=two\n")
        with self.assertRaisesRegex(ValueError, "duplicate key"):
            setup.plan(self.root, self.config)
        self.assertFalse((self.root / "src/frontend/project.local.json").exists())

    def test_feature_changes_and_generated_file_drift(self):
        self.run_command("apply")
        self.data["features"] = {"login": False, "email": False, "oauth": False}
        self.save()
        self.assertEqual(self.run_command("check")[0], 1)
        self.run_command("apply")
        for directory in ("src/backend", "docker"):
            self.assertIn(
                "LOGIN_ENABLED='false'", (self.root / directory / ".env").read_text()
            )
        self.assertEqual(self.run_command("check")[0], 0)
        (self.root / "src/frontend/project.local.json").write_text("{}")
        self.assertEqual(self.run_command("check")[0], 1)

    def test_symlink_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            target = self.root / "src/backend/.env"
            external = Path(outside) / "secret.env"
            external.write_text("SECRET_KEY=untouched\n")
            target.symlink_to(external)
            with self.assertRaisesRegex(ValueError, "Refusing output"):
                setup.plan(self.root, self.config)
            self.assertEqual(external.read_text(), "SECRET_KEY=untouched\n")

    def test_write_failure_rolls_back_completed_files(self):
        self.run_command("apply")
        before = {
            path: path.read_bytes() for path in setup.plan(self.root, self.config)
        }
        self.data["name"] = "Changed"
        self.save()
        original = setup.write_atomic
        calls = 0

        def fail_once(path, content, mode):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("fixture write failure")
            original(path, content, mode)

        with patch.object(setup, "write_atomic", side_effect=fail_once):
            with self.assertRaises(OSError):
                self.run_command("apply")
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_example_is_valid(self):
        validate_manifest(json.loads((SOURCE / "project.example.json").read_text()))
