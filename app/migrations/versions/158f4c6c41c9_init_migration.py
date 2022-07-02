"""second  migration

Revision ID: 158f4c6c41c9
Revises: 
Create Date: 2022-06-29 00:28:03.750798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = '158f4c6c41c9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('response',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('text_answer', sa.TEXT(), nullable=True),
    sa.Column('answer_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('type_service', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('response')
    # ### end Alembic commands ###
