"""Real Git layouts protect independent API selection and shared fallbacks."""

import json
import tempfile
import unittest
from pathlib import Path

import verification as v
from verification_backend import backend_impact, registration_only, response_header_only


class BackendSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for args in (
            ("init", "-q"),
            ("config", "user.email", "fixture@example.com"),
            ("config", "user.name", "Fixture"),
        ):
            v.git(self.root, *args)
        for path in (
            "app/__init__.py",
            "app/routers/v1/__init__.py",
            "app/services/__init__.py",
            "tests/test_smoke.py",
            "tests/test_openapi_contract.py",
        ):
            self.write(path, "")
        self.write(
            "app/main.py",
            'from app.routers.v1 import old\ndef create_app():\n    app.include_router(old.router, prefix="/api/v1/old")\n    return app\n',
        )
        self.write("app/services/catalog.py", 'def result(): return "ok"\n')
        self.write(
            "app/routers/v1/catalog.py", "from app.services.catalog import result\n"
        )
        self.write(
            "tests/api/v1/catalog/test_catalog_api.py",
            "from app.routers.v1 import catalog\n",
        )
        self.write(
            "tests/unit/services/test_catalog.py",
            "from app.services.catalog import result\n",
        )
        self.write("tests/unit/services/test_unrelated.py", "def test_other(): pass\n")
        (self.root / "contracts").mkdir()
        (self.root / "contracts/openapi.json").write_text(
            json.dumps({"openapi": "3.1.0", "info": {"version": "1"}, "paths": {}})
        )
        self.commit()

    def write(self, path, text):
        target = self.root / "src/backend" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self):
        v.git(self.root, "add", ".")
        v.git(self.root, "commit", "-qm", "fixture")

    def impact(self):
        return backend_impact(
            self.root, "HEAD", None, v.changed(self.root, "HEAD", None), v.content
        )

    def response_router_fixture(self):
        self.write("app/core/db/session.py", "def get_db(): pass\n")
        self.write(
            "app/models/user.py",
            "from app.core.db.session import get_db\nclass UserResponse: pass\n",
        )
        router = (
            "from fastapi.responses import StreamingResponse as Stream\n"
            "from app.models.user import UserResponse\n"
            "from app.services.catalog import result\n"
            "def endpoint(user: UserResponse):\n"
            '    return Stream(result(), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})\n'
        )
        self.write("app/routers/v1/catalog.py", router)
        self.commit()
        return router

    def test_response_header_only_avoids_false_schema_persistence(self):
        old = self.response_router_fixture()
        new = old.replace('"no-cache"', '"no-store"')
        self.write("app/routers/v1/catalog.py", new)
        selected = self.impact()
        self.assertEqual(selected["domains"], ["catalog"])
        self.assertEqual(selected["response_header_only"], ["app.routers.v1.catalog"])
        self.assertIn("tests/api/v1/catalog/test_catalog_api.py", selected["tests"])
        self.assertIn("tests/test_smoke.py", selected["tests"])
        self.assertIn("tests/test_openapi_contract.py", selected["tests"])
        self.assertNotIn("tests/unit/services/test_unrelated.py", selected["tests"])
        forced = v.plan(self.root, force_full=True)
        self.assertNotIn("backend_impact", forced)
        # Service data access is not hidden by a simultaneous header edit.
        self.write(
            "app/services/catalog.py",
            "from app.core.db.session import get_db\ndef result(): return get_db()\n",
        )
        self.assertIsNone(self.impact())
        self.write(
            "tests/integration/api/v1/catalog/test_catalog_integration.py",
            "from app.services.catalog import result\n",
        )
        self.assertIn(
            "tests/integration/api/v1/catalog/test_catalog_integration.py",
            self.impact()["tests"],
        )

    def test_nontransport_or_protected_edits_keep_persistence_fallback(self):
        old = self.response_router_fixture()
        for new in (
            old.replace("result()", "different()"),
            old.replace("result()", "result(user.id)"),
            old.replace('"no-cache"', "runtime_header()"),
            old.replace("user: UserResponse", "user: OtherIdentity"),
        ):
            self.write("app/routers/v1/catalog.py", new)
            self.assertIsNone(self.impact(), new)
        self.write("app/routers/v1/catalog.py", old.replace('"no-cache"', '"no-store"'))
        self.write("app/models/user.py", "class UserResponse: changed = True\n")
        self.assertIsNone(self.impact())
        self.write(
            "app/models/user.py",
            "from app.core.db.session import get_db\nclass UserResponse: pass\n",
        )
        self.write("app/routers/v1/catalog.py", old)
        self.write("app/routers/v1/auth.py", old)
        self.commit()
        self.write("app/routers/v1/auth.py", old.replace('"no-cache"', '"no-store"'))
        self.assertIsNone(self.impact())

    def test_header_guard_rejects_shadowing_unpack_and_other_semantics(self):
        old = (
            "from fastapi.responses import StreamingResponse as Stream\n"
            "def endpoint(user=Depends(current_user)):\n"
            '    return Stream(body(), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})\n'
        )
        changed = old.replace('"no-cache"', '"no-store"')
        self.assertTrue(response_header_only(old, changed))
        for new in (
            changed.replace("body()", "other_body()"),
            changed.replace("current_user", "anonymous_user"),
            changed.replace('"no-store"', "settings.cache"),
            changed.replace('"X-Accel-Buffering": "no"', '"X-Accel-Buffering": "yes"'),
            changed.replace(
                '"Cache-Control": "no-store"',
                '"Cache-Control": "no-store", **other_headers',
            ),
            changed + "Stream = custom_response\n",
            changed.replace("def endpoint(user=", "def endpoint(Stream, user="),
            changed.replace("from fastapi.responses", "from other.responses"),
            old + "# comment only\n",
        ):
            self.assertFalse(response_header_only(old, new), new)
        for shadow in ("Stream = custom_response\n", "def Stream(): pass\n"):
            self.assertFalse(response_header_only(old + shadow, changed + shadow))

    def test_existing_domain_consumers_and_union_exclude_unrelated(self):
        self.write("app/services/catalog.py", 'def result(): return "changed"\n')
        selected = self.impact()
        self.assertEqual(selected["domains"], ["catalog"])
        self.assertIn("tests/api/v1/catalog/test_catalog_api.py", selected["tests"])
        self.assertIn("tests/test_openapi_contract.py", selected["tests"])
        self.assertNotIn("tests/unit/services/test_unrelated.py", selected["tests"])
        self.write(
            "app/services/second.py", "from app.services.catalog import result\n"
        )
        self.write(
            "tests/api/v1/second/test_second_api.py",
            "from app.services.second import result\n",
        )
        self.assertEqual(set(self.impact()["domains"]), {"catalog", "second"})

    def test_new_stateless_api_registration_selects_its_real_tests(self):
        old = (self.root / "src/backend/app/main.py").read_text()
        new = old.replace("import old", "import old, probe").replace(
            "    return app",
            '    app.include_router(probe.router, prefix="/api/v1/probe")\n    return app',
        )
        self.write("app/main.py", new)
        self.write("app/routers/v1/probe.py", "from app.services.probe import result\n")
        self.write("app/services/probe.py", 'def result(): return "ok"\n')
        self.write(
            "tests/api/v1/probe/test_probe_api.py", "from app.routers.v1 import probe\n"
        )
        selected = self.impact()
        self.assertEqual(selected["domains"], ["probe"])
        self.assertIn("tests/api/v1/probe/test_probe_api.py", selected["tests"])
        self.assertNotIn("tests/api/v1/catalog/test_catalog_api.py", selected["tests"])
        contract = self.root / "contracts/openapi.json"
        schema = json.loads(contract.read_text())
        schema["paths"]["/api/v1/probe"] = {
            "get": {"responses": {"200": {"description": "ok"}}}
        }
        contract.write_text(json.dumps(schema))
        scope = v.plan(self.root)
        self.assertTrue(scope["consumer_check_only"])
        self.assertFalse(scope["browser"])
        self.assertEqual(scope["backend_impact"]["domains"], ["probe"])
        commands = v.targets(scope, True, "all")
        self.assertIn(["make", "-C", "src/frontend", "api-check"], commands)
        self.assertNotIn("test-production", str(commands))
        self.assertTrue(
            any(
                arg.startswith("PYTEST_ARGS=")
                for command in commands
                for arg in command
            )
        )
        forced = v.plan(self.root, force_full=True)
        self.assertNotIn("backend_impact", forced)
        self.assertFalse(
            any(
                arg.startswith("PYTEST_ARGS=")
                for command in v.targets(forced, True, "all")
                for arg in command
            )
        )
        schema["info"]["version"] = "breaking"
        contract.write_text(json.dumps(schema))
        self.assertFalse(v.plan(self.root)["consumer_check_only"])
        self.assertIn("test-production", str(v.targets(v.plan(self.root), True, "all")))
        self.assertTrue(registration_only(old, new, {"probe"}))
        self.assertFalse(
            registration_only(
                old,
                new.replace(
                    '    app.include_router(probe.router, prefix="/api/v1/probe")\n    return app',
                    '    return app\n    app.include_router(probe.router, prefix="/api/v1/probe")',
                ),
                {"probe"},
            )
        )
        self.assertFalse(
            registration_only(
                old, new.replace('prefix="/api/v1/old"', 'prefix="/changed"'), {"probe"}
            )
        )
        self.assertFalse(
            registration_only(
                old,
                new.replace('prefix="/api/v1/probe"', "prefix=runtime_prefix()"),
                {"probe"},
            )
        )
        self.assertFalse(
            registration_only(
                old,
                new.replace(
                    '    app.include_router(probe.router, prefix="/api/v1/probe")\n', ""
                ).replace(
                    "    app.include_router(old.router",
                    '    app.include_router(probe.router, prefix="/api/v1/probe")\n    app.include_router(old.router',
                ),
                {"probe"},
            )
        )

    def test_persistence_requires_owned_integration_and_models_stay_broad(self):
        self.write(
            "app/services/catalog.py", "from app.core.db.session import get_db\n"
        )
        self.write("app/core/db/session.py", "def get_db(): pass\n")
        self.commit()
        self.write(
            "app/services/catalog.py",
            "from app.core.db.session import get_db\ndef changed(): pass\n",
        )
        self.assertIsNone(self.impact())
        self.write(
            "tests/integration/api/v1/catalog/test_catalog_integration.py",
            "from app.services.catalog import changed\n",
        )
        self.assertIn(
            "tests/integration/api/v1/catalog/test_catalog_integration.py",
            self.impact()["tests"],
        )
        self.write(
            "app/models/catalog.py", "from sqlalchemy.orm import Mapped as Field\n"
        )
        self.assertIsNone(self.impact())

    def test_shared_auth_migrations_fixtures_dynamic_and_missing_coverage_broaden(self):
        for path, text in [
            ("app/services/auth.py", "pass\n"),
            ("app/core/config/settings.py", "pass\n"),
            ("alembic/versions/new.py", "pass\n"),
            ("tests/conftest.py", "pass\n"),
            ("app/services/dynamic.py", "import importlib\n"),
            ("app/services/uncovered.py", "pass\n"),
        ]:
            self.write(path, text)
            self.assertIsNone(self.impact(), path)
            (self.root / "src/backend" / path).unlink()
        self.write("app/services/catalog.py", "def result(): return 2\n")
        (self.root / "src/backend/tests/api/v1/catalog/test_catalog_api.py").unlink()
        (self.root / "src/backend/tests/unit/services/test_catalog.py").unlink()
        self.assertIsNone(self.impact())

    def test_test_only_deletions_and_shell_unsafe_paths_are_not_selected(self):
        self.write("tests/unit/services/test_bad;name.py", "def test_bad(): pass\n")
        self.assertIsNone(self.impact())
        (self.root / "src/backend/tests/unit/services/test_bad;name.py").unlink()
        (self.root / "src/backend/tests/unit/services/test_catalog.py").unlink()
        self.assertIsNone(self.impact())

    def test_local_fixture_changes_select_only_their_pytest_subtree(self):
        self.write("tests/api/v1/catalog/conftest.py", "value = 1\n")
        selected = self.impact()
        self.assertEqual(
            selected["tests"], ["tests/api/v1/catalog/test_catalog_api.py"]
        )
