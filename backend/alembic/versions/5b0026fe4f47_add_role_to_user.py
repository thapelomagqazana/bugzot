"""Add role to User

Revision ID: 5b0026fe4f47
Revises: 070670f10596
Create Date: 2025-03-06 19:13:56.422796

"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '5b0026fe4f47'
down_revision = '070670f10596'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the 'role' column as nullable first
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))

    # Step 2: Set default value for existing rows
    op.execute("UPDATE users SET role = 'user'")

    # Step 3: Alter column to NOT NULL
    op.alter_column('users', 'role', nullable=False)


def downgrade():
    op.drop_column('users', 'role')
