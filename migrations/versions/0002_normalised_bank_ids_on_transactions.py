"""normalised bank ids on transactions

The IBM transactions file zero-pads bank codes ('010', '03208') while the
accounts file does not ('210', '21884'). These generated columns strip the
leading zeros so transactions join to accounts on (bank_id, account_number).
The raw from_bank / to_bank columns are kept exactly as loaded.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE transactions
            ADD COLUMN from_bank_id text GENERATED ALWAYS AS (ltrim(from_bank, '0')) STORED,
            ADD COLUMN to_bank_id   text GENERATED ALWAYS AS (ltrim(to_bank, '0')) STORED
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE transactions
            DROP COLUMN IF EXISTS from_bank_id,
            DROP COLUMN IF EXISTS to_bank_id
        """
    )
