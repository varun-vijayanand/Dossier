"""kyc profiles and truth table

kyc_profiles holds the synthetic KYC record the agent may see (through MCP
tools only). kyc_profile_truth records how the profile was generated and is
evaluation-only, like transactions.is_laundering: the agent must never read it.

No foreign key to accounts: accounts.entity_id is not unique, so Postgres
cannot enforce it. A test checks that every customer entity has a profile.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE kyc_profiles (
            entity_id                 text PRIMARY KEY,
            entity_type               text NOT NULL CHECK (
                entity_type IN ('Corporation', 'Sole Proprietorship', 'Partnership', 'Individual')
            ),
            country                   text NOT NULL,
            onboarding_date           date NOT NULL,
            last_review_date          date NOT NULL,
            business_activity         text NOT NULL,
            expected_monthly_turnover numeric(18, 2) NOT NULL
                CHECK (expected_monthly_turnover >= 0),
            risk_rating               text NOT NULL
                CHECK (risk_rating IN ('low', 'medium', 'high')),
            pep_flag                  boolean NOT NULL,
            contact_name              text NOT NULL,
            registered_address        text NOT NULL,
            CHECK (last_review_date >= onboarding_date)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE kyc_profile_truth (
            entity_id           text PRIMARY KEY
                REFERENCES kyc_profiles (entity_id) ON DELETE CASCADE,
            turnover_consistent boolean NOT NULL,
            distortion_factor   numeric(10, 4)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS kyc_profile_truth")
    op.execute("DROP TABLE IF EXISTS kyc_profiles")
