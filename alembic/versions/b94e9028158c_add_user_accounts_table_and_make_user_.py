"""add_user_accounts_table_and_make_user_email_password_optional

Revision ID: b94e9028158c
Revises: 0036c61b16e1
Create Date: 2025-12-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b94e9028158c'
down_revision: Union[str, None] = '0036c61b16e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 修改users表，使email和hashed_password可选
    op.alter_column('users', 'email',
                    existing_type=sa.String(255),
                    nullable=True,
                    existing_nullable=False)
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=True,
                    existing_nullable=False)
    
    # 2. 创建user_accounts表
    op.create_table(
        'user_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_type', sa.String(length=20), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('extra_data', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_accounts_id'), 'user_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_user_accounts_user_id'), 'user_accounts', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_accounts_account_type'), 'user_accounts', ['account_type'], unique=False)
    op.create_index(op.f('ix_user_accounts_account_id'), 'user_accounts', ['account_id'], unique=False)
    op.create_unique_constraint('uq_user_account_type_id', 'user_accounts', ['user_id', 'account_type', 'account_id'])


def downgrade() -> None:
    # 删除user_accounts表
    op.drop_constraint('uq_user_account_type_id', 'user_accounts', type_='unique')
    op.drop_index(op.f('ix_user_accounts_account_id'), table_name='user_accounts')
    op.drop_index(op.f('ix_user_accounts_account_type'), table_name='user_accounts')
    op.drop_index(op.f('ix_user_accounts_user_id'), table_name='user_accounts')
    op.drop_index(op.f('ix_user_accounts_id'), table_name='user_accounts')
    op.drop_table('user_accounts')
    
    # 恢复users表的email和hashed_password为必填
    # 注意：如果已有NULL值，需要先处理数据
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=False,
                    existing_nullable=True)
    op.alter_column('users', 'email',
                    existing_type=sa.String(255),
                    nullable=False,
                    existing_nullable=True)
