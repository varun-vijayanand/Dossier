"""Alembic environment: runs hand-written SQL migrations against Dossier's DB."""

from alembic import context
from sqlalchemy import create_engine, pool

from dossier.common.config import get_settings


def _sqlalchemy_url() -> str:
    """Use the app's URL, but tell SQLAlchemy to use the psycopg v3 driver."""
    url = get_settings().database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def run_migrations_offline() -> None:
    """Emit SQL to the console without connecting (alembic upgrade --sql)."""
    context.configure(
        url=_sqlalchemy_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    engine = create_engine(_sqlalchemy_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
