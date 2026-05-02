import asyncio
from pathlib import Path

from alembic.config import Config as AlembicConfig

from alembic import command


def _build_alembic_config(database_url: str) -> AlembicConfig:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(backend_root / "alembic"))
    alembic_cfg.set_main_option("prepend_sys_path", ".")
    alembic_cfg.set_main_option("path_separator", "os")
    alembic_cfg.set_main_option("version_path_separator", "os")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    return alembic_cfg


def _upgrade_schema_to_head(database_url: str) -> None:
    alembic_cfg = _build_alembic_config(database_url)
    command.upgrade(alembic_cfg, "head")


async def run_startup_schema_migrations(database_url: str) -> None:
    await asyncio.to_thread(_upgrade_schema_to_head, database_url)
