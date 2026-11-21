"""account and entity indexes

Built after the bulk load. Transactions are indexed by account on both the
sent and received side (with ts last, so one index also serves date windows).
Accounts are indexed by entity. ANALYZE refreshes the planner's statistics
after the 5M-row load.

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_transactions_from_account "
        "ON transactions (from_bank_id, from_account, ts)"
    )
    op.execute(
        "CREATE INDEX ix_transactions_to_account "
        "ON transactions (to_bank_id, to_account, ts)"
    )
    op.execute("CREATE INDEX ix_accounts_entity ON accounts (entity_id)")
    op.execute("ANALYZE transactions")
    op.execute("ANALYZE accounts")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_accounts_entity")
    op.execute("DROP INDEX IF EXISTS ix_transactions_to_account")
    op.execute("DROP INDEX IF EXISTS ix_transactions_from_account")
