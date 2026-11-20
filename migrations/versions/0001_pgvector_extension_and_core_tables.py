"""pgvector extension and core tables

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE accounts (
            bank_id        text NOT NULL,
            account_number text NOT NULL,
            bank_name      text,
            entity_id      text,
            entity_name    text,
            PRIMARY KEY (bank_id, account_number)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE transactions (
            txn_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            ts                timestamp NOT NULL,
            from_bank         text NOT NULL,
            from_account      text NOT NULL,
            to_bank           text NOT NULL,
            to_account        text NOT NULL,
            amount_received   numeric(24, 4) NOT NULL,
            receiving_currency text NOT NULL,
            amount_paid       numeric(24, 4) NOT NULL,
            payment_currency  text NOT NULL,
            payment_format    text NOT NULL,
            is_laundering     boolean NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS transactions")
    op.execute("DROP TABLE IF EXISTS accounts")
    # The vector extension is left in place on purpose: other objects may use it.
