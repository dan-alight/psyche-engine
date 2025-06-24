"""seed aiprovider

Revision ID: 011091ea5951
Revises: 836656fa5999
Create Date: 2025-06-25 08:40:59.080861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '011091ea5951'
down_revision: str | Sequence[str] | None = '836656fa5999'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
  """Upgrade schema."""
  op.bulk_insert(
      sa.table(
          'aiprovider', sa.column('name', sa.String),
          sa.column('base_url', sa.String)),
      [
          {
              'name': 'OpenAI',
              'base_url': 'https://api.openai.com/v1'
          },
          {
              'name': 'Google',
              'base_url':
              'https://generativelanguage.googleapis.com/v1beta/openai/'
          },
          {
              'name': 'Anthropic',
              'base_url': 'https://api.anthropic.com/v1'
          },
      ])

def downgrade() -> None:
  """Downgrade schema."""
  aiprovider = sa.table(
      "aiprovider",
      sa.column("name", sa.String),
  )
  op.execute(
      aiprovider.delete().where(
          aiprovider.c.name.in_(["OpenAI", "Google", "Anthropic"])))
