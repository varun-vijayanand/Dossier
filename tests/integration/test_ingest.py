"""Tests for the IBM AML loader, run against temporary tables."""

from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from dossier.common.db import connect
from dossier.ingest.ibm_aml import load_accounts, load_transactions

pytestmark = pytest.mark.integration

ACCOUNTS_CSV = (
    "Bank Name,Bank ID,Account Number,Entity ID,Entity Name\n"
    "Test Bank #1,10,AAAAAAAA1,E1,Corporation #1\n"
    "Test Bank #2,210,BBBBBBBB2,E2,Partnership #2\n"
)
TRANSACTIONS_HEADER = (
    "Timestamp,From Bank,Account,To Bank,Account,Amount Received,Receiving Currency,"
    "Amount Paid,Payment Currency,Payment Format,Is Laundering\n"
)
GOOD_ROW = "2022/09/01 00:06,010,AAAAAAAA1,0210,BBBBBBBB2,100.50,US Dollar,100.50,US Dollar,ACH,1\n"


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    try:
        connection = connect()
    except psycopg.OperationalError:
        pytest.skip("Postgres is not reachable")
    with connection:
        # Temp tables shadow the real ones for this connection only.
        connection.execute("CREATE TEMP TABLE accounts (LIKE public.accounts INCLUDING ALL)")
        connection.execute(
            "CREATE TEMP TABLE transactions (LIKE public.transactions INCLUDING ALL)"
        )
        yield connection


def test_load_accounts(conn: psycopg.Connection, tmp_path: Path) -> None:
    path = tmp_path / "accounts.csv"
    path.write_text(ACCOUNTS_CSV)
    assert load_accounts(conn, path) == 2


def test_load_accounts_refuses_second_run(conn: psycopg.Connection, tmp_path: Path) -> None:
    path = tmp_path / "accounts.csv"
    path.write_text(ACCOUNTS_CSV)
    load_accounts(conn, path)
    with pytest.raises(RuntimeError, match="already has rows"):
        load_accounts(conn, path)


def test_load_transactions_maps_columns_and_normalises_bank_ids(
    conn: psycopg.Connection, tmp_path: Path
) -> None:
    accounts = tmp_path / "accounts.csv"
    accounts.write_text(ACCOUNTS_CSV)
    load_accounts(conn, accounts)

    txns = tmp_path / "trans.csv"
    txns.write_text(TRANSACTIONS_HEADER + GOOD_ROW)
    assert load_transactions(conn, txns) == 1

    row = conn.execute(
        "SELECT ts, from_bank, from_bank_id, from_account, to_bank, to_bank_id, "
        "to_account, amount_received, is_laundering FROM transactions"
    ).fetchone()
    assert row == (
        datetime(2022, 9, 1, 0, 6),
        "010",
        "10",
        "AAAAAAAA1",
        "0210",
        "210",
        "BBBBBBBB2",
        Decimal("100.5000"),
        True,
    )

    # The padded raw code must not stop the join once the trimmed column is used.
    matched = conn.execute(
        "SELECT count(*) FROM transactions t JOIN accounts a "
        "ON a.bank_id = t.from_bank_id AND a.account_number = t.from_account"
    ).fetchone()
    assert matched is not None and matched[0] == 1


def test_load_transactions_rejects_short_rows(conn: psycopg.Connection, tmp_path: Path) -> None:
    txns = tmp_path / "trans.csv"
    txns.write_text(TRANSACTIONS_HEADER + "2022/09/01 00:06,010,AAAAAAAA1,0210\n")
    with pytest.raises(ValueError, match="line 2"):
        load_transactions(conn, txns)


def test_load_transactions_refuses_second_run(conn: psycopg.Connection, tmp_path: Path) -> None:
    txns = tmp_path / "trans.csv"
    txns.write_text(TRANSACTIONS_HEADER + GOOD_ROW)
    load_transactions(conn, txns)
    with pytest.raises(RuntimeError, match="already has rows"):
        load_transactions(conn, txns)
