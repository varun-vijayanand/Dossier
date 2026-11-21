"""Load the IBM synthetic AML data (HI-Small) into Postgres."""

import csv
import sys
from pathlib import Path

import psycopg

from dossier.common.db import connect

TRANSACTION_FIELDS = 11


def load_accounts(conn: psycopg.Connection, path: Path) -> int:
    """Stream the accounts CSV into the accounts table with COPY.

    Refuses to run if the table already has rows, so a second run cannot
    create duplicates. Returns the number of rows now in the table.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM accounts")
        existing = cur.fetchone()
        if existing is not None and existing[0] > 0:
            raise RuntimeError("accounts already has rows; refusing to load twice")

        with path.open(newline="") as f:
            reader = csv.reader(f)
            next(reader)  # skip the header line
            with cur.copy(
                "COPY accounts (bank_name, bank_id, account_number, entity_id, entity_name) "
                "FROM STDIN"
            ) as copy:
                for row in reader:
                    copy.write_row(row)

        cur.execute("SELECT count(*) FROM accounts")
        loaded = cur.fetchone()
        return int(loaded[0]) if loaded is not None else 0


def load_transactions(
    conn: psycopg.Connection, path: Path, progress_every: int = 500_000
) -> int:
    """Stream the transactions CSV into the transactions table with COPY.

    The CSV has two columns both named "Account", so columns are mapped by
    position, never by name. Every row must have exactly 11 fields. The
    whole load is one transaction: if anything fails, nothing is kept.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM transactions")
        existing = cur.fetchone()
        if existing is not None and existing[0] > 0:
            raise RuntimeError("transactions already has rows; refusing to load twice")

        with path.open(newline="") as f:
            reader = csv.reader(f)
            next(reader)  # skip the header line
            with cur.copy(
                "COPY transactions (ts, from_bank, from_account, to_bank, to_account, "
                "amount_received, receiving_currency, amount_paid, payment_currency, "
                "payment_format, is_laundering) FROM STDIN"
            ) as copy:
                for line_no, row in enumerate(reader, start=2):
                    if len(row) != TRANSACTION_FIELDS:
                        raise ValueError(
                            f"line {line_no}: expected {TRANSACTION_FIELDS} fields, got {len(row)}"
                        )
                    copy.write_row(row)
                    if (line_no - 1) % progress_every == 0:
                        print(f"  {line_no - 1:,} rows sent...", flush=True)

        cur.execute("SELECT count(*) FROM transactions")
        loaded = cur.fetchone()
        return int(loaded[0]) if loaded is not None else 0


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("accounts", "transactions"):
        raise SystemExit(
            "usage: python -m dossier.ingest.ibm_aml (accounts|transactions) [csv path]"
        )
    kind = sys.argv[1]
    default = {
        "accounts": "data/raw/HI-Small_accounts.csv",
        "transactions": "data/raw/HI-Small_Trans.csv",
    }[kind]
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(default)
    with connect() as conn:
        if kind == "accounts":
            print(f"accounts loaded: {load_accounts(conn, path)}")
        else:
            print(f"transactions loaded: {load_transactions(conn, path):,}")


if __name__ == "__main__":
    main()
