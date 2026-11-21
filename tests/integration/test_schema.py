"""Checks that the migrations produced the schema the code expects."""

from collections.abc import Iterator

import psycopg
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from dossier.common.db import connect

pytestmark = pytest.mark.integration

TRANSACTION_COLUMNS = [
    "txn_id",
    "ts",
    "from_bank",
    "from_account",
    "to_bank",
    "to_account",
    "amount_received",
    "receiving_currency",
    "amount_paid",
    "payment_currency",
    "payment_format",
    "is_laundering",
    "from_bank_id",
    "to_bank_id",
]


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    try:
        connection = connect()
    except psycopg.OperationalError:
        pytest.skip("Postgres is not reachable")
    with connection:
        yield connection


def test_database_is_at_latest_migration(conn: psycopg.Connection) -> None:
    head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    assert row is not None
    assert row[0] == head


def test_vector_extension_installed(conn: psycopg.Connection) -> None:
    row = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()
    assert row is not None


def test_core_tables_exist(conn: psycopg.Connection) -> None:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name IN ('accounts', 'transactions')"
    ).fetchall()
    assert {r[0] for r in rows} == {"accounts", "transactions"}


def test_transactions_columns(conn: psycopg.Connection) -> None:
    rows = conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'transactions' "
        "ORDER BY ordinal_position"
    ).fetchall()
    assert [r[0] for r in rows] == TRANSACTION_COLUMNS


def test_lookup_indexes_exist(conn: psycopg.Connection) -> None:
    expected = {"ix_transactions_from_account", "ix_transactions_to_account", "ix_accounts_entity"}
    rows = conn.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' "
        "AND indexname LIKE 'ix\\_%'"
    ).fetchall()
    assert expected <= {r[0] for r in rows}
