import sqlite3

import pytest

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config


@pytest.mark.primary_data
def test_user_id_migration_preserves_related_data_and_prevents_reuse(tmp_path, monkeypatch):
    """Scenario: upgrading populated SQLite preserves dependent records and reserves deleted IDs."""
    # Given: an existing schema with a user and their password record.
    path = tmp_path / "migration.db"
    url = f"sqlite+aiosqlite:///{path}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    config = _build_alembic_config(url)
    command.upgrade(config, "0006_api_keys_usage_and_expiry")
    with sqlite3.connect(path) as db:
        db.execute(
            "INSERT INTO users (id,email,name,is_active,is_verified,role,created_at,updated_at) VALUES (10,'migration@example.com','Migration',1,1,'user',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
        db.execute(
            "INSERT INTO credentials (user_id,password_hash,created_at,updated_at) VALUES (10,'test-only',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
    # When: upgrade, rollback and re-upgrade run against populated data.
    command.upgrade(config, "head")
    command.downgrade(config, "0006_api_keys_usage_and_expiry")
    command.upgrade(config, "head")
    # Then: FK data survives, and deleting the highest ID cannot recycle a token subject.
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        assert db.execute("SELECT user_id FROM credentials").fetchall() == [(10,)]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        db.execute("DELETE FROM users WHERE id=10")
        db.execute(
            "INSERT INTO users (email,name,is_active,is_verified,role,created_at,updated_at) VALUES ('next@example.com','Next',1,1,'user',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
        assert db.execute("SELECT id FROM users").fetchone()[0] > 10
        assert db.execute("SELECT COUNT(*) FROM credentials").fetchone()[0] == 0


@pytest.mark.primary_data
def test_manager_migration_preserves_users_and_downgrades_safely(tmp_path, monkeypatch):
    """Populated role data survives upgrade; old releases receive supported roles."""
    path = tmp_path / "roles.db"
    url = f"sqlite+aiosqlite:///{path}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    config = _build_alembic_config(url)
    command.upgrade(config, "0009_billing_checkouts")
    with sqlite3.connect(path) as db:
        for role in ("admin", "user"):
            db.execute(
                "INSERT INTO users (email,name,is_active,is_verified,role,created_at,updated_at) VALUES (?, ?,1,1,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                (f"{role}@example.com", role, role),
            )
    command.upgrade(config, "head")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT role FROM users ORDER BY id").fetchall() == [
            ("admin",),
            ("user",),
        ]
        db.execute("UPDATE users SET role='manager' WHERE role='user'")
        db.execute(
            "INSERT INTO role_change_audit (target_user_id,previous_role,new_role,operator,created_at) VALUES (2,'user','manager','cli:test',CURRENT_TIMESTAMP)"
        )
    command.downgrade(config, "0009_billing_checkouts")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT role FROM users ORDER BY id").fetchall() == [
            ("admin",),
            ("user",),
        ]
    command.upgrade(config, "head")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM role_change_audit").fetchone()[0] == 0
