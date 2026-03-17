"""
Alembic env.py — async migrations for OnCopilot.
"""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from alembic import context

# Ensure the project root is on the path so `core` and `models` resolve
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.config import settings
from core.database import Base

# All models must be imported so their metadata is populated
import models  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# NOTE: We intentionally do NOT call config.set_main_option("sqlalchemy.url", ...)
# because Alembic passes it through Python's configparser which mangles special
# characters like % in passwords. Instead we read the URL directly from our
# pydantic-settings object (which python-dotenv loaded cleanly).


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda conn: context.run_migrations())
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
