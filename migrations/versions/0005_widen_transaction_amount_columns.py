"""widen transaction amount columns

Migration 0001 used numeric(24, 4). The source CSV carries up to 6 decimals
(Bitcoin amounts), so 4 decimals rounded small Bitcoin payments to zero:
3,267 received and 1,803 paid amounts were stored as 0 although the source has
none. Widening the type does not restore rounded digits; the transactions must
be reloaded from the CSV after this migration.

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE transactions
            ALTER COLUMN amount_received TYPE numeric(28, 8),
            ALTER COLUMN amount_paid     TYPE numeric(28, 8)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE transactions
            ALTER COLUMN amount_received TYPE numeric(24, 4),
            ALTER COLUMN amount_paid     TYPE numeric(24, 4)
        """
    )
