"""Regression fixtures for generic response schemas without weakening ORM boundaries."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import check_backend_architecture as checker


class GenericSchemaBoundaryTests(unittest.TestCase):
    def check_fixture(self, models: str, imported: str) -> int:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "src/backend/app"
            (app / "models").mkdir(parents=True)
            (app / "routers").mkdir()
            (app / "models/page.py").write_text(models)
            (app / "routers/list.py").write_text(
                f"from app.models.page import {imported}\n"
            )
            with (
                patch.object(checker, "ROOT", root),
                patch.object(checker, "APP", app),
                redirect_stdout(StringIO()),
                redirect_stderr(StringIO()),
            ):
                return checker.main()

    def test_generic_pydantic_response_is_allowed(self):
        """Scenario: routers can import a concretely specialized Pydantic response."""
        # Given / When / Then: generic and concrete schema inheritance resolves safely.
        self.assertEqual(
            self.check_fixture(
                "from pydantic import BaseModel\n"
                "from typing import Generic, TypeVar\n"
                "T = TypeVar('T')\n"
                "class Page(BaseModel, Generic[T]): pass\n"
                "class Response(Page[str]): pass\n",
                "Response",
            ),
            0,
        )

    def test_generic_alone_or_repository_mixin_is_rejected(self):
        """Scenario: Generic does not grant schema status to repositories or mixed classes."""
        # Given / When / Then: no Pydantic base or an unapproved mixin still fails.
        for declaration in (
            "class Response(Generic[T]): pass\n",
            "class Repository: pass\nclass Response(BaseModel, Repository, Generic[T]): pass\n",
        ):
            with self.subTest(declaration=declaration):
                self.assertEqual(
                    self.check_fixture(
                        "from pydantic import BaseModel\n"
                        "from typing import Generic, TypeVar\n"
                        "T = TypeVar('T')\n" + declaration,
                        "Response",
                    ),
                    1,
                )
