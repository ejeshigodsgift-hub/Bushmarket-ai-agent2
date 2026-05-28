from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.base import Base

config = context.config

DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+psycopg2",
    "postgresql+asyncpg"
)

config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# =========================================
# OFFLINE MIGRATIONS
# =========================================
def run_migrations_offline():

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================
# ONLINE MIGRATIONS
# =========================================
def run_migrations_online():

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_migrations():

        async with connectable.connect() as connection:

            await connection.run_sync(
                lambda sync_conn: context.configure(
                    connection=sync_conn,
                    target_metadata=target_metadata
                )
            )

            await connection.run_sync(
                lambda sync_conn: context.run_migrations()
            )

    import asyncio
    asyncio.run(do_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()