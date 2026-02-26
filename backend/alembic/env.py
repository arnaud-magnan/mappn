"""Alembic migration environment with async support for SQLAlchemy 2.0."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio
import os

# Import all models so they are registered with Base.metadata for autodiscovery.
# The models __init__.py re-exports all shared models (User, Place, Area, Visit).
from app.models import Base, User, Place, Area, Visit  # noqa: F401

# this is the Alembic Config object, which provides
# the values of the [alembic] section of the .ini
# file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run async migrations (SQLAlchemy 2.0 with asyncio)."""
    # Get database URL from environment or config
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
        if not db_url or db_url.startswith("driver://"):
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Set it or configure sqlalchemy.url in alembic.ini"
            )

    # Ensure async URL scheme
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not db_url.startswith("postgresql+asyncpg://"):
        db_url = "postgresql+asyncpg://" + db_url.split("://", 1)[-1]

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = db_url

    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations():
    """Entry point for migrations, handles both sync and async."""
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_async_migrations())


run_migrations()
