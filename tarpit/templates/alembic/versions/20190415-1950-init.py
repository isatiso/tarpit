"""init

Revision ID: 54ce85d0b3df
Revises: 
Create Date: 2019-04-15 19:50:47.822374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54ce85d0b3df'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('phone', sa.String(length=100), nullable=True),
    sa.Column('password', sa.String(length=36), nullable=True),
    sa.Column('avatar', sa.String(length=255), nullable=True),
    sa.Column('remark', sa.Text(), nullable=True),
    sa.Column('deleted', sa.SmallInteger(), server_default=sa.text('0'), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP  ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
    sa.PrimaryKeyConstraint('user_id'),
    mysql_engine='InnoDB'
    )
    op.create_index('ix_user_name', 'user', ['name'], unique=False)
    op.create_index('ix_user_password', 'user', ['password'], unique=False)
    op.create_index('ix_user_phone', 'user', ['phone'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_phone', table_name='user')
    op.drop_index('ix_user_password', table_name='user')
    op.drop_index('ix_user_name', table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
